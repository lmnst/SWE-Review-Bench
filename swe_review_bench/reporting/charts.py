"""Single grouped bar chart for Milestone D.

x = reviewer; two bars per reviewer:
    * left bar  -- instance hit rate (left y-axis, range 0..1)
    * right bar -- mean FP per instance (right y-axis, autoscaled)

This is intentionally the ONLY chart the MVP produces. Pareto / ROC /
calibration plots are out of scope.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend, no display required
import matplotlib.pyplot as plt
import numpy as np

from ..scoring.metrics import ReviewerSummary


def write_hit_fp_chart(
    summaries: list[ReviewerSummary],
    path: Path,
    *,
    tolerance: int,
    n_instances: int,
) -> None:
    """Render the hit-rate vs FP/instance grouped bar chart."""
    reviewers = [s.reviewer for s in summaries]
    hit_rates = [s.instance_hit_rate for s in summaries]
    fps = [s.fp_per_instance_mean for s in summaries]

    x = np.arange(len(reviewers))
    width = 0.36

    fig, ax_left = plt.subplots(figsize=(max(6.5, 2.0 * len(reviewers)), 4.8))
    bars_hit = ax_left.bar(
        x - width / 2, hit_rates, width, color="#1f77b4", label="Instance hit rate"
    )
    ax_left.set_ylabel("Instance hit rate", color="#1f77b4")
    ax_left.tick_params(axis="y", labelcolor="#1f77b4")
    ax_left.set_ylim(0, 1)

    ax_right = ax_left.twinx()
    bars_fp = ax_right.bar(
        x + width / 2, fps, width, color="#d62728", label="FP per instance (mean)"
    )
    ax_right.set_ylabel("FP per instance (mean)", color="#d62728")
    ax_right.tick_params(axis="y", labelcolor="#d62728")
    fp_top = max(fps + [1.0])
    ax_right.set_ylim(0, fp_top * 1.15)

    ax_left.set_xticks(x)
    ax_left.set_xticklabels(reviewers, rotation=12, ha="right")
    ax_left.set_title(
        f"SWE-Review-Bench MVP -- hit rate vs FP "
        f"(N={n_instances} instances, tolerance={tolerance})"
    )

    # Numeric labels on bars.
    for bar, v in zip(bars_hit, hit_rates):
        ax_left.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.02,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#1f77b4",
        )
    for bar, v in zip(bars_fp, fps):
        ax_right.text(
            bar.get_x() + bar.get_width() / 2,
            v + fp_top * 0.02,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#d62728",
        )

    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
