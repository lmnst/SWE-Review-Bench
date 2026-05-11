"""F.3 variant_comparison.png renderer.

Two side-by-side panels:
  Left  : instance hit rate per variant per reviewer (Wilson 95% CI).
  Right : file-level hit rate per variant per reviewer (Wilson 95% CI).

FP/instance is a mean, not a rate, so it is reported in
``variant_summary.csv`` rather than charted here. The chart caption
notes Variant C is diagnostic-only.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


REVIEWERS = ("claude-sonnet-4-5", "gpt-4o-mini")
VARIANTS = ("A", "B", "C")
COLOURS = {"claude-sonnet-4-5": "#3a7ca5", "gpt-4o-mini": "#d68a59"}
LABELS = {"claude-sonnet-4-5": "Claude Sonnet 4.5", "gpt-4o-mini": "GPT-4o-mini"}


def _panel(ax, df, *, rate_col: str, lo_col: str, hi_col: str, title: str) -> None:
    x = np.arange(len(VARIANTS))
    width = 0.36
    for i, rev in enumerate(REVIEWERS):
        rates = []
        lows = []
        highs = []
        for var in VARIANTS:
            r = df[(df["reviewer"] == rev) & (df["prompt_variant"] == var)]
            if len(r) != 1:
                rates.append(0.0)
                lows.append(0.0)
                highs.append(0.0)
                continue
            rate = float(r[rate_col].iloc[0])
            lo = float(r[lo_col].iloc[0])
            hi = float(r[hi_col].iloc[0])
            rates.append(rate)
            lows.append(rate - lo)
            highs.append(hi - rate)
        offset = (i - 0.5) * width
        bars = ax.bar(
            x + offset,
            rates,
            width=width,
            yerr=[lows, highs],
            capsize=4,
            color=COLOURS[rev],
            edgecolor="black",
            linewidth=0.4,
            label=LABELS[rev],
        )
        for bar, rate in zip(bars, rates):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                rate + 0.015,
                f"{rate:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(VARIANTS)
    ax.set_xlabel("Prompt variant")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_title(title)
    ax.axhline(0, color="black", linewidth=0.4)
    ax.grid(axis="y", linestyle=":", linewidth=0.4)


def main() -> None:
    df = pd.read_csv(ROUND2_DIR / "variant_summary.csv")

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    _panel(
        ax_l,
        df,
        rate_col="instance_hit_rate",
        lo_col="instance_hit_rate_wilson_lo",
        hi_col="instance_hit_rate_wilson_hi",
        title="Instance hit rate (tolerance=3)",
    )
    _panel(
        ax_r,
        df,
        rate_col="file_level_hit_rate",
        lo_col="file_level_hit_rate_wilson_lo",
        hi_col="file_level_hit_rate_wilson_hi",
        title="File-level hit rate",
    )
    ax_l.legend(loc="upper left", framealpha=0.9, fontsize=9)
    fig.suptitle(
        "F.3 prompt-variant comparison  (N=20 instances; error bars = Wilson 95% CI)",
        fontsize=11,
    )
    fig.text(
        0.5,
        0.02,
        "Variant A = Round 1 v1 (cache-hit, byte-identical). "
        "Variant B = no-suppression. Variant C = force-emit (diagnostic-only).",
        ha="center",
        fontsize=8,
        color="#555",
    )
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    out = ROUND2_DIR / "variant_comparison.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
