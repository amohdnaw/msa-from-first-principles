"""LEVEL 5 - figure sheets.

Sheet 1: precision is not accuracy. Left, two gauges with the identical spread -
    so the identical %GRR - one centred and one three microns high, drawn over
    the tolerance band. Right, where the rejections happen: an unbiased gauge
    scraps at both limits and a biased one puts almost everything on one side.

Sheet 2: the two that are worse than invisible. Left, error against true size:
    linearity inflates the apparent part spread, which is the denominator of the
    study ratio, so the gauge's own defect improves its score. Right, twelve
    monthly studies of a drifting gauge - each interval is the right width, the
    %GRR is identical every month, and the gauge has moved three times its own
    sigma.

    PYTHONPATH=src .venv/bin/python -m msalab.level05
"""
from __future__ import annotations

import math
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    PANEL_HIGH, RULE, SIGNAL_ALARM, SIGNAL_OK, rc,
)
from msalab.accuracy import (
    BIAS, BIASED_MISS, CLEAN_MISS, CLEAN_RATIOS, DRIFT, DRIFT_OVER_GAUGE,
    DRIFT_PCT_TOL, DRIFT_PER_MONTH, DRIFT_TOTAL, GAUGE_SIGMA, GRR_BY_MONTH,
    LINEARITY, LINEAR_RATIOS, MONTHS, STUDY_IMPROVEMENT, linear_error,
)
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA

mpl.rcParams.update(rc())


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


def _normal(x, mu, sd):
    return np.exp(-((x - mu) ** 2) / (2 * sd ** 2)) / (sd * np.sqrt(2 * np.pi))


# --------------------------------------------------------------- sheet 1
def sheet_l05_precision_is_not_accuracy() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.26)

    half = TOLERANCE / 2

    # ---- left: two gauges with the same spread, one off centre
    ax = fig.add_subplot(gs[0])
    xs = np.linspace(-half * 1.5, half * 1.5, 700)
    ax.axvspan(-half, half, color=PANEL_HIGH, alpha=0.55, lw=0)
    for mu, colour, label in [(0.0, SIGNAL_OK, "centred"),
                              (BIAS, SIGNAL_ALARM, f"{BIAS:.0f} µm high")]:
        y = _normal(xs, mu, math.hypot(PART_SIGMA, GAUGE_SIGMA))
        ax.plot(xs, y, color=colour, lw=2.4, label=label)
        # ymax stops the verticals below the label band. Without it every
        # centred label is crossed by a line, because axvline spans the axes.
        ax.axvline(mu, color=colour, lw=1.2, ls=(0, (4, 3)), ymax=0.74)
    for v in (-half, half):
        ax.axvline(v, color=DATA_TRUTH, lw=1.6, ymax=0.74)

    top = ax.get_ylim()[1]
    ax.set_ylim(0, top * 1.34)
    ax.text(0, top * 1.13, "the tolerance band", color=DATA_TRUTH, fontsize=10.5,
            ha="center")
    ax.set_xlabel(r"reading, $\mu$m from nominal", fontsize=10.5)
    ax.set_ylabel("density", fontsize=10.5)
    ax.set_title(f"identical spread, identical %GRR "
                 f"({CLEAN_RATIOS['study']:.1f} % both)", fontsize=11.5,
                 loc="left", pad=13)
    ax.grid(alpha=0.15, axis="y")
    leg = ax.legend(frameon=False, fontsize=10, loc="upper left")
    for t in leg.get_texts():
        t.set_family("monospace")
    ax.text(0.985, 0.975,
            f"good parts scrapped\n"
            f"{CLEAN_MISS['good_rejected_pct']:.2f} %  →  "
            f"{BIASED_MISS['good_rejected_pct']:.2f} %",
            transform=ax.transAxes, ha="right", va="top", fontsize=10.5,
            color=INK)

    # ---- right: which limit the rejections happen at
    ax2 = fig.add_subplot(gs[1])
    rows = [("centred", CLEAN_MISS), (f"{BIAS:.0f} µm high", BIASED_MISS)]
    for i, (name, m) in enumerate(rows):
        ax2.barh([-i], [m["rejected_at_lower_pct"]], color=DATA_GAUGE,
                 height=0.44, label="at the lower limit" if i == 0 else None)
        ax2.barh([-i], [m["rejected_at_upper_pct"]],
                 left=[m["rejected_at_lower_pct"]], color=SIGNAL_ALARM,
                 height=0.44, label="at the upper limit" if i == 0 else None)
        for centre, width, colour in [
                (m["rejected_at_lower_pct"] / 2, m["rejected_at_lower_pct"],
                 DATA_GAUGE),
                (m["rejected_at_lower_pct"] + m["rejected_at_upper_pct"] / 2,
                 m["rejected_at_upper_pct"], SIGNAL_ALARM)]:
            if width >= 9:
                ax2.text(centre, -i, f"{width:.0f} %", ha="center", va="center",
                         color=INK_BRIGHT, fontsize=10.5, family="monospace")
            else:
                # below the bar, so it cannot collide with the tick label
                ax2.text(centre, -i + 0.36, f"{width:.0f} %", ha="center",
                         va="bottom", color=colour, fontsize=10,
                         family="monospace")
    ax2.set_yticks([0, -1])
    ax2.set_yticklabels([r[0] for r in rows], fontsize=10.5)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-1.85, 0.55)
    ax2.set_xlabel("share of the rejections, %", fontsize=10.5)
    ax2.set_title("bias is one-sided; noise is not", fontsize=11.5, loc="left",
                  pad=13)
    ax2.grid(alpha=0.18, axis="x")
    leg2 = ax2.legend(frameon=False, fontsize=9.5, loc="lower center", ncol=2)
    for t in leg2.get_texts():
        t.set_family("monospace")

    fig.suptitle("Every ratio in Levels 1 to 4 is built from variances, and a "
                 "constant offset has none. %GRR cannot see this.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l05_1_precision_is_not_accuracy")


# --------------------------------------------------------------- sheet 2
def sheet_l05_worse_than_invisible() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.2], wspace=0.28)

    # ---- left: linearity, and why it flatters
    ax = fig.add_subplot(gs[0])
    rng = np.random.default_rng(66)
    truth = rng.normal(0.0, PART_SIGMA, 500)
    err = linear_error(truth) + rng.normal(0.0, GAUGE_SIGMA, truth.size)
    ax.scatter(truth, err, s=7, color=INK_DIM, alpha=0.5, edgecolors="none")
    line = np.linspace(truth.min(), truth.max(), 100)
    ax.plot(line, linear_error(line), color=SIGNAL_ALARM, lw=2.4, label=f"slope {LINEARITY}")
    ax.axhline(0, color=DATA_TRUTH, lw=1.4, ls=(0, (4, 3)))
    ax.set_xlabel(r"the part's true size, $\mu$m", fontsize=10.5)
    ax.set_ylabel(r"the gauge's error, $\mu$m", fontsize=10.5)
    ax.set_title("right in the middle, wrong at the ends", fontsize=11.5,
                 loc="left", pad=13)
    ax.grid(alpha=0.15)
    lo, hi = ax.get_ylim()
    ax.set_ylim(lo - (hi - lo) * 0.30, hi)
    ax.text(0.03, 0.055,
            f"apparent part spread {LINEAR_RATIOS['apparent_part']:.2f} vs true "
            f"{PART_SIGMA}\n"
            f"so %GRR improves: {CLEAN_RATIOS['study']:.1f} % → "
            f"{LINEAR_RATIOS['study']:.1f} %",
            transform=ax.transAxes, fontsize=10.5, color=ACCENT)
    leg = ax.legend(frameon=False, fontsize=10, loc="upper left")
    for t in leg.get_texts():
        t.set_family("monospace")

    # ---- right: twelve months of a drifting gauge
    ax2 = fig.add_subplot(gs[1])
    rows = DRIFT["rows"]
    ms = [r["month"] for r in rows]
    ax2.plot(ms, [r["true_bias"] for r in rows], color=DATA_TRUTH, lw=2.0,
             ls=(0, (5, 3)), label="the gauge's real bias")
    ax2.errorbar(ms, [r["mean"] for r in rows],
                 yerr=[r["half_width"] for r in rows], fmt="s", ms=4.6,
                 color=SIGNAL_OK, ecolor=SIGNAL_OK, elinewidth=1.4, capsize=3,
                 label="each month's study, with its interval")
    ax2.axhline(0, color=RULE, lw=1.2)
    ax2.set_xlabel("month", fontsize=10.5)
    ax2.set_ylabel(r"measured bias, $\mu$m", fontsize=10.5)
    ax2.set_title(f"one master, once a month — %GRR reads "
                  f"{GRR_BY_MONTH[0]:.1f} % every time", fontsize=11,
                  loc="left", pad=13)
    ax2.grid(alpha=0.18)
    lo2, hi2 = ax2.get_ylim()
    ax2.set_ylim(lo2 - (hi2 - lo2) * 0.24, hi2)
    ax2.text(0.03, 0.045,
             f"total drift {DRIFT_TOTAL:.1f} µm = {DRIFT_OVER_GAUGE:.1f}× the "
             f"gauge's own σ, {DRIFT_PCT_TOL:.0f} % of tolerance",
             transform=ax2.transAxes, fontsize=10.5, color=INK)
    leg2 = ax2.legend(frameon=False, fontsize=9.5, loc="upper left")
    for t in leg2.get_texts():
        t.set_family("monospace")

    fig.suptitle("Linearity does not hide from %GRR — it improves it. And no single "
                 "study can see a drift, because the bias is constant inside one.",
                 fontsize=13, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l05_2_worse_than_invisible")


if __name__ == "__main__":
    sheet_l05_precision_is_not_accuracy()
    sheet_l05_worse_than_invisible()
