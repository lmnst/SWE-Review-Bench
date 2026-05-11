"""LLM reviewer driven by litellm.

Hard rules enforced here:

* Model id resolution honours ``MODEL_ID_OVERRIDE`` from ``.env``. If the
  resolved id is not recognised by the installed litellm version we
  RAISE at construction time -- never silently substitute another model.
* Cache key = sha256 of ``(resolved_model, PROMPT_TEMPLATE_ID, file_path,
  file_content)``; cached payload is a full ``ReviewResult``.
* Pre-flight token estimate must stay below 60% of the model's
  ``max_input_tokens``. Over that, we emit a ``TokenLimitExceeded``
  ``ReviewMeta`` (no API call, no cache write) so the orchestration layer
  can record it in ``failures.jsonl``.
* JSON parse failure is NEVER swallowed: the raw output is saved, the
  parse error event is reflected in ``ReviewMeta.parse_error``, and the
  comment list is empty for that file.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import litellm

from ..config import Config
from ..utils.json_io import extract_json_array
from .base import (
    PROMPT_TEMPLATE_ID,
    Comment,
    ReviewMeta,
    ReviewResult,
    Reviewer,
    ReviewerInput,
    build_prompt,
)
from .cache import cache_key, raw_path, read_cached, write_cached, write_raw
from .prompt_variants import PromptVariant, get_variant, render_prompt


# Suppress litellm's chatty startup banner in CLI output.
litellm.suppress_debug_info = True


class LLMReviewer(Reviewer):
    """Single-model LLM reviewer."""

    def __init__(
        self,
        requested_model: str,
        config: Config,
        *,
        max_tokens: int = 2048,
        token_budget_fraction: float = 0.6,
        timeout_seconds: int = 120,
        prompt_variant: str = "A",
    ) -> None:
        self.requested_model = requested_model
        self.resolved_model = config.resolve_model_id(requested_model)
        self.name = requested_model
        self.config = config
        self.max_tokens = max_tokens
        self.token_budget_fraction = token_budget_fraction
        self.timeout_seconds = timeout_seconds
        self.context_window = self._probe_context_window(self.resolved_model)
        # Variant A = Round 1 prompt template ``v1``. Variant B/C are
        # Round 2 only. The cache key incorporates the variant's
        # template_id so the three variants never collide.
        self.variant: PromptVariant = get_variant(prompt_variant)
        # For Variant A only: read-through to Round 1 cache for
        # byte-identical-prompt hits. Round 1 cache is never written.
        self._round1_read_through = self.variant.name == "A"

    @staticmethod
    def _probe_context_window(model: str) -> int:
        """Return the model's ``max_input_tokens``; raise if the model is unknown.

        Per project rule: never silently substitute a different model.
        """
        try:
            info: dict[str, Any] = litellm.get_model_info(model)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                f"Model id {model!r} is not recognised by litellm "
                f"({type(e).__name__}: {e}). Set MODEL_ID_OVERRIDE in .env "
                f"to map it to a known id, or use a model litellm supports."
            ) from e
        max_input = info.get("max_input_tokens") or info.get("max_tokens")
        if not max_input:
            raise RuntimeError(
                f"litellm returned model info for {model!r} but no max_input_tokens. "
                f"Refusing to proceed; set MODEL_ID_OVERRIDE or upgrade litellm."
            )
        return int(max_input)

    # ----- main entry --------------------------------------------------

    def review(self, inp: ReviewerInput) -> ReviewResult:
        key = cache_key(
            self.resolved_model,
            self.variant.template_id,
            inp.file_path,
            inp.file_content,
        )

        # Variant A reads from Round 2 cache first (so prior Round 2
        # writes win in case of any later edit), then falls back to
        # Round 1 cache. Variants B/C only consult the Round 2 cache.
        cached = read_cached(self.config.llm_cache_dir_round2, key)
        if cached is None and self._round1_read_through:
            cached = read_cached(self.config.llm_cache_dir, key)
        if cached is not None:
            return ReviewResult(
                comments=cached.comments,
                meta=cached.meta.model_copy(
                    update={"cache_hit": True, "latency_seconds": 0.0}
                ),
            )

        prompt = render_prompt(self.variant, inp.file_path, inp.file_content)

        # Pre-flight token check.
        est_input_tokens = self._safe_token_count(self.resolved_model, prompt)
        budget = int(self.context_window * self.token_budget_fraction)
        if est_input_tokens > budget:
            return ReviewResult(
                comments=[],
                meta=ReviewMeta(
                    latency_seconds=0.0,
                    estimated_input_tokens=est_input_tokens,
                    skipped_reason="TokenLimitExceeded",
                ),
            )

        # Actual API call.
        start = time.monotonic()
        try:
            response = litellm.completion(
                model=self.resolved_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=self.max_tokens,
                timeout=self.timeout_seconds,
                num_retries=0,
            )
        except Exception as e:  # noqa: BLE001
            return ReviewResult(
                comments=[],
                meta=ReviewMeta(
                    latency_seconds=time.monotonic() - start,
                    estimated_input_tokens=est_input_tokens,
                    skipped_reason=f"APIError:{type(e).__name__}: {e}",
                ),
            )
        latency = time.monotonic() - start

        raw_text = self._extract_raw_text(response)
        raw_p = write_raw(self.config.llm_raw_cache_dir_round2, key, raw_text)

        comments, parse_error = self._parse_comments(raw_text, inp.file_path)

        usage = getattr(response, "usage", None)
        cost = self._safe_cost(response)

        meta = ReviewMeta(
            latency_seconds=latency,
            input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
            output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            estimated_cost_usd=cost,
            cache_hit=False,
            raw_output_path=str(raw_p),
            parse_error=parse_error,
            estimated_input_tokens=est_input_tokens,
        )
        result = ReviewResult(comments=comments, meta=meta)
        # All Round 2 writes go to the Round 2 cache dir. The Round 1
        # cache directory is read-only for Round 2.
        write_cached(self.config.llm_cache_dir_round2, key, result)
        return result

    # ----- helpers -----------------------------------------------------

    @staticmethod
    def _extract_raw_text(response: Any) -> str:
        try:
            return response.choices[0].message.content or ""
        except (AttributeError, IndexError):
            return ""

    @staticmethod
    def _safe_token_count(model: str, text: str) -> int:
        try:
            return int(litellm.token_counter(model=model, text=text))
        except Exception:  # noqa: BLE001
            # Fall back to a coarse 4-chars-per-token estimate; never crash.
            return max(1, len(text) // 4)

    @staticmethod
    def _safe_cost(response: Any) -> float | None:
        try:
            return float(litellm.completion_cost(completion_response=response))
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _parse_comments(
        raw_text: str, expected_file: str
    ) -> tuple[list[Comment], bool]:
        """Parse and validate the JSON array returned by the model.

        Returns ``(comments, parse_error)``. ``parse_error`` is True iff the
        raw output is non-empty but no JSON array could be recovered.
        Items that don't fit the schema are dropped silently from the list
        but do NOT mark the whole response as a parse error -- those are
        per-item validation misses, not catastrophic format failures.
        """
        if not raw_text.strip():
            return [], False
        arr = extract_json_array(raw_text)
        if arr is None:
            return [], True
        out: list[Comment] = []
        for item in arr:
            if not isinstance(item, dict):
                continue
            # Tolerate slight file path mismatch: accept basename / suffix.
            file_in = (item.get("file") or "").strip()
            if file_in and file_in != expected_file:
                if expected_file.endswith("/" + file_in) or expected_file.endswith(
                    "\\" + file_in
                ):
                    item = {**item, "file": expected_file}
                else:
                    item = {**item, "file": expected_file}
            elif not file_in:
                item = {**item, "file": expected_file}
            try:
                out.append(Comment.model_validate(item))
            except Exception:  # noqa: BLE001
                continue
        return out, False
