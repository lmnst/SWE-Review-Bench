"""H-lite Task 6 — preliminary results one-pager + variant figure.

Reads only the derived CSVs from Task 2 plus Round 1's
``outputs/summary.csv`` (for the Round 1 cost number) and produces:

  docs/preliminary_results.md
  docs/figures/variant_comparison_with_ci.png

The figure uses matplotlib only (no seaborn) and the default colour
cycle. Variant C bars are hatched and the caption marks them as
diagnostic-only.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
H_LITE_DIR = PROJECT_ROOT / "outputs" / "round2" / "h_lite"
DOCS_DIR = PROJECT_ROOT / "docs"
FIG_DIR = DOCS_DIR / "figures"

LLM_REVIEWERS = ("claude-sonnet-4-5", "gpt-4o-mini")
LLM_LABELS = {"claude-sonnet-4-5": "Claude Sonnet 4.5", "gpt-4o-mini": "GPT-4o-mini"}
VARIANTS = ("A", "B", "C")


def _fmt_cell(k: int, n: int, lo: float, hi: float) -> str:
    pct = (k / n * 100) if n else 0.0
    return f"{k}/{n} = {pct:.0f}% [{lo:.3f}, {hi:.3f}]"


def _round1_table() -> str:
    df = pd.read_csv(H_LITE_DIR / "round1_with_ci.csv")
    lines: list[str] = []
    lines.append(
        "| reviewer | instance hit rate | file-level hit rate | site recall | FP / instance |\n"
    )
    lines.append("|---|---|---|---|---:|\n")
    for _, r in df.iterrows():
        lines.append(
            f"| `{r['reviewer']}` | "
            f"{_fmt_cell(int(r['instance_hit_n']), int(r['instance_total_n']), float(r['instance_hit_rate_ci_low']), float(r['instance_hit_rate_ci_high']))} | "
            f"{_fmt_cell(int(r['file_hit_instances_n']), int(r['file_total_instances_n']), float(r['file_level_hit_rate_ci_low']), float(r['file_level_hit_rate_ci_high']))} | "
            f"{_fmt_cell(int(r['sites_hit_n']), int(r['sites_total_n']), float(r['site_recall_ci_low']), float(r['site_recall_ci_high']))} | "
            f"{float(r['false_positives_per_instance_mean']):.2f} |\n"
        )
    return "".join(lines)


def _variant_table() -> str:
    df = pd.read_csv(H_LITE_DIR / "variant_summary_with_ci.csv")
    lines: list[str] = []
    lines.append("| variant | reviewer | instance hit rate | note |\n")
    lines.append("|---|---|---|---|\n")
    for var in VARIANTS:
        for rev in LLM_REVIEWERS:
            row = df[(df["prompt_variant"] == var) & (df["reviewer"] == rev)]
            if len(row) != 1:
                continue
            r = row.iloc[0]
            note = ""
            if var == "C":
                note = "diagnostic-only probe; forces ≥1 comment per file"
            elif var == "A":
                note = "Round 1 baseline (`v1`)"
            elif var == "B":
                note = "no-speculation clause removed (`v1b`)"
            lines.append(
                f"| {var} | `{rev}` | "
                f"{_fmt_cell(int(r['instance_hit_n']), int(r['instance_total_n']), float(r['instance_hit_rate_ci_low']), float(r['instance_hit_rate_ci_high']))} | "
                f"{note} |\n"
            )
    return "".join(lines)


def _cost_lines() -> str:
    s = pd.read_csv(PROJECT_ROOT / "outputs" / "summary.csv")
    total_r1 = float(s["total_estimated_cost_usd"].sum())
    per_rev = {row["reviewer"]: float(row["total_estimated_cost_usd"]) for _, row in s.iterrows()}
    return (
        f"- Round 1 baseline: total **${total_r1:.4f}** across 60 reviewer/instance cells "
        f"(LLM-only spend; `claude-sonnet-4-5` ${per_rev.get('claude-sonnet-4-5', 0.0):.4f}, "
        f"`gpt-4o-mini` ${per_rev.get('gpt-4o-mini', 0.0):.4f}, static $0).\n"
        f"- Round 2 diagnostic: **$1.92, 120 calls** (Variant A all cache hits at $0; "
        f"Variants B and C cache-missed and cost about $0.95 each on Claude plus a few cents on GPT-4o-mini).\n"
        f"- Hard cap for Round 2 was $5; actual spend was 38% of the cap.\n"
    )


def write_md() -> Path:
    lines: list[str] = []
    lines.append("# Preliminary results (SWE-Review-Bench, 20-instance pilot)\n\n")
    lines.append(
        "Headline numbers from the SWE-Review-Bench pilot. The 20-instance "
        "pilot uses `princeton-nlp/SWE-bench_Lite`, `split=test`, "
        "`seed=42`, oracle `strict_mode=False`, default tolerance N=3. "
        "Wilson 95% intervals are given in brackets for every rate cell; "
        "the methodology and formula are recorded in "
        "`outputs/round2/h_lite/ci_methodology.md`.\n\n"
    )

    lines.append("## Round 1 baseline (prompt `v1`)\n\n")
    lines.append(_round1_table())

    lines.append("\n## Round 2 prompt-variant experiment (Claude + GPT-4o-mini only)\n\n")
    lines.append(_variant_table())

    lines.append("\n## Cost summary\n\n")
    lines.append(_cost_lines())

    lines.append("\n## Figure\n\n")
    lines.append(
        "![Prompt-variant comparison](figures/variant_comparison_with_ci.png)\n\n"
        "*n=20 per instance-level cell; error bars are Wilson 95% CIs; "
        "Variant C is a controlled probe and is not used as a headline "
        "result.*\n\n"
    )

    lines.append("## Framing\n\n")
    lines.append(
        "n=20 is a pilot; CIs are wide; prompt sensitivity appears "
        "material; full Lite is needed before final claims.\n"
    )

    out = DOCS_DIR / "preliminary_results.md"
    out.write_text("".join(lines), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------


def _panel(ax, df, *, rate_col, lo_col, hi_col, title):
    x = np.arange(len(VARIANTS))
    width = 0.36
    for i, rev in enumerate(LLM_REVIEWERS):
        rates: list[float] = []
        lows: list[float] = []
        highs: list[float] = []
        for var in VARIANTS:
            row = df[(df["reviewer"] == rev) & (df["prompt_variant"] == var)]
            if len(row) != 1:
                rates.append(0.0)
                lows.append(0.0)
                highs.append(0.0)
                continue
            r = row.iloc[0]
            rate = float(r[rate_col])
            lo = float(r[lo_col])
            hi = float(r[hi_col])
            rates.append(rate)
            lows.append(rate - lo)
            highs.append(hi - rate)
        offset = (i - 0.5) * width
        hatches = ["", "", "//"]  # mark Variant C as diagnostic
        bars = ax.bar(
            x + offset,
            rates,
            width=width,
            yerr=[lows, highs],
            capsize=4,
            label=LLM_LABELS[rev],
            edgecolor="black",
            linewidth=0.4,
        )
        for bar, h in zip(bars, hatches):
            bar.set_hatch(h)
        for bar, rate in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                rate + 0.02,
                f"{rate:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(VARIANTS)
    ax.set_xlabel("Prompt variant")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Rate")
    ax.set_title(title)
    ax.axhline(0, color="black", linewidth=0.4)
    ax.grid(axis="y", linestyle=":", linewidth=0.4)


def write_figure() -> Path:
    df = pd.read_csv(H_LITE_DIR / "variant_summary_with_ci.csv")
    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    _panel(
        ax_l,
        df,
        rate_col="instance_hit_rate",
        lo_col="instance_hit_rate_ci_low",
        hi_col="instance_hit_rate_ci_high",
        title="Instance hit rate (tolerance=3)",
    )
    _panel(
        ax_r,
        df,
        rate_col="file_level_hit_rate",
        lo_col="file_level_hit_rate_ci_low",
        hi_col="file_level_hit_rate_ci_high",
        title="File-level hit rate",
    )
    ax_l.legend(loc="upper left", framealpha=0.9, fontsize=9)
    fig.suptitle(
        "SWE-Review-Bench prompt-variant comparison  (n=20; Wilson 95% CIs; hatched bars = Variant C, diagnostic-only)",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.02,
        "Variant A = Round 1 v1 (cache-hit, byte-identical to Round 1). "
        "Variant B = no-speculation clause removed. "
        "Variant C is a controlled probe and is not used as a headline result.",
        ha="center",
        fontsize=8,
        color="#555",
    )
    fig.tight_layout(rect=[0, 0.05, 1, 0.93])
    out = FIG_DIR / "variant_comparison_with_ci.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out_md = write_md()
    out_png = write_figure()
    print(f"wrote {out_md}")
    print(f"wrote {out_png}")


if __name__ == "__main__":
    main()
