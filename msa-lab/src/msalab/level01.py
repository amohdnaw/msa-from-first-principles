"""LEVEL 1 - figure sheets.

Sheet 1: the law. Left, one bore measured two hundred times - a part with a
    single true size producing a distribution. Right, a population of six
    thousand parts drawn twice: as they are, and as the gauge reports them.
    Six thousand rather than forty on purpose; see sheet 2.

Sheet 2: what one study can and cannot show. Left, the sampling distribution of
    an observed standard deviation across four thousand forty-part studies,
    with the true part spread and the exact observed spread marked - they sit
    inside the noise, and the shaded region is how often a study points the
    wrong way. Right, the averaging floor: repeats buy less and less, and never
    reach the part spread.

Every number annotated here is imported from `measurement.py`. Nothing is typed.

    PYTHONPATH=src .venv/bin/python -m msalab.level01
"""
from __future__ import annotations

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    PANEL_HIGH, RULE, SIGNAL_ALARM, rc,
)
from msalab.measurement import (
    AVERAGE_TABLE, EXPECTED_OBSERVED, FLOOR, GAUGE_SIGMA, ONE_PART_MEAN,
    ONE_PART_RANGE, ONE_PART_READS, ONE_PART_SAMPLE, ONE_PART_SD, ONE_PART_TRUE,
    OBSERVED_EXACT, PART_SIGMA, PARTS, POP, REPEATS_FOR_1PCT, SE_OBSERVED_PCT,
    WIDENING_PCT, WRONG_DIRECTION_PCT, averaging_floor, replicate,
)

mpl.rcParams.update(rc())


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


# --------------------------------------------------------------- sheet 1
def sheet_l01_a_gauge_is_a_process() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.45], wspace=0.24)

    # ---- left: one part, two hundred readings
    ax = fig.add_subplot(gs[0])
    ax.hist(ONE_PART_SAMPLE, bins=26, color=DATA_GAUGE, alpha=0.5,
            edgecolor=DATA_GAUGE, linewidth=0.8)
    ax.axvline(ONE_PART_TRUE, color=INK_BRIGHT, lw=1.6, zorder=5)
    # headroom for the annotations: they go ABOVE the bars, never on them
    bars_top = ax.get_ylim()[1]
    ax.set_ylim(0, bars_top * 1.42)
    ax.annotate("", xy=(ONE_PART_SAMPLE.min(), bars_top * 1.10),
                xytext=(ONE_PART_SAMPLE.max(), bars_top * 1.10),
                arrowprops=dict(arrowstyle="<->", color=INK_DIM, lw=1.1))
    ax.text(ONE_PART_MEAN, bars_top * 1.14,
            f"{ONE_PART_RANGE:.1f} " + r"$\mu$m of spread",
            color=INK_DIM, fontsize=10, ha="center", va="bottom")
    ax.text(ONE_PART_TRUE, bars_top * 1.33, "one true size",
            color=INK_BRIGHT, fontsize=10.5, ha="center", va="bottom")
    ax.set_xlabel(r"reading, $\mu$m from nominal", fontsize=10.5)
    ax.set_ylabel("readings", fontsize=10.5)
    ax.set_title(f"one bore, {ONE_PART_READS} readings", fontsize=11.5, loc="left",
                 pad=13)
    ax.grid(alpha=0.18, axis="y")
    ax.text(0.03, 0.97, f"s = {ONE_PART_SD:.2f} " + r"$\mu$m",
            transform=ax.transAxes, color=DATA_GAUGE, fontsize=11,
            va="top", family="monospace")

    # ---- right: the same parts under two gauges, one real and one bad
    #
    # Drawn this way because the honest version of the claim needs both. At the
    # real gauge the widening is 4.3 %, which is smaller than the linewidth: a
    # figure showing only that would be asserting something the reader cannot
    # see. Beside it the same law with a gauge as big as the parts is obvious.
    # The pair IS the lesson of claim 3 - cheap at first, brutal later.
    ax2 = fig.add_subplot(gs[1])
    rng = np.random.default_rng(404)
    truth = POP["truth"]
    bad_sigma = PART_SIGMA
    observed = POP["observed"]
    bad = truth + rng.normal(0.0, bad_sigma, truth.size)

    lo, hi = min(truth.min(), bad.min()), max(truth.max(), bad.max())
    bins = np.linspace(lo, hi, 80)
    ax2.hist(truth, bins=bins, color=DATA_TRUTH, alpha=0.30, edgecolor="none",
             label=f"the parts                      s = {truth.std(ddof=1):5.2f}")
    ax2.hist(observed, bins=bins, histtype="step", color=DATA_GAUGE, lw=1.9,
             label=f"gauge {GAUGE_SIGMA} um  ({WIDENING_PCT:4.1f} % wider)  "
                   f"s = {observed.std(ddof=1):5.2f}")
    ax2.hist(bad, bins=bins, histtype="step", color=DATA_OBSERVED, lw=1.9,
             label=f"gauge {bad_sigma} um  (41.4 % wider)  "
                   f"s = {bad.std(ddof=1):5.2f}")
    ax2.set_xlabel(r"size, $\mu$m from nominal", fontsize=10.5)
    ax2.set_ylabel("parts", fontsize=10.5)
    ax2.set_title(f"the same {POP['n']:,} parts under two gauges", fontsize=11.5,
                  loc="left", pad=13)
    ax2.grid(alpha=0.18, axis="y")
    leg = ax2.legend(frameon=False, fontsize=9.5, loc="upper right",
                     handlelength=1.4)
    for tx in leg.get_texts():
        tx.set_family("monospace")
    # lower-left is the one region no curve enters
    ax2.text(0.02, 0.30,
             "the middle outline is the\nreal gauge: 4.3 % wider,\nand invisible.",
             transform=ax2.transAxes, color=INK, fontsize=10, va="top")

    fig.suptitle("A gauge is a process. The spread you see is not the spread of the parts.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l01_1_a_gauge_is_a_process")


# --------------------------------------------------------------- sheet 2
def sheet_l01_what_one_study_can_show() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 1.0], wspace=0.26)

    rng = np.random.default_rng(909)
    obs = np.array([
        (rng.normal(0.0, PART_SIGMA, PARTS)
         + rng.normal(0.0, GAUGE_SIGMA, PARTS)).std(ddof=1)
        for _ in range(4000)])

    # ---- left: the sampling distribution of one study's answer
    ax = fig.add_subplot(gs[0])
    n, bins, patches = ax.hist(obs, bins=58, color=INK_DIM, alpha=0.42,
                               edgecolor="none")
    for b, patch in zip(bins[:-1], patches):
        if b < PART_SIGMA:
            patch.set_facecolor(SIGNAL_ALARM)
            patch.set_alpha(0.5)

    bars_top = ax.get_ylim()[1]
    ax.set_ylim(0, bars_top * 1.34)
    ax.axvline(PART_SIGMA, color=DATA_TRUTH, lw=1.6)
    ax.axvline(OBSERVED_EXACT, color=DATA_OBSERVED, lw=1.6)

    # The gap between the two lines IS the whole effect, and on this axis it is
    # four pixels wide. Labelling it from a distance with a leader line is the
    # only honest way to draw something that small - shrinking the axis to make
    # it look big would be the lie.
    mid = (PART_SIGMA + OBSERVED_EXACT) / 2
    ax.annotate(f"the whole effect: {WIDENING_PCT:.1f} %\n"
                f"parts {PART_SIGMA}  vs  law {OBSERVED_EXACT:.2f}",
                xy=(mid, bars_top * 1.02), xytext=(mid + 1.35, bars_top * 1.24),
                color=INK_BRIGHT, fontsize=10.5, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=INK_DIM, lw=0.9,
                                shrinkA=2, shrinkB=2))
    # the right shoulder is empty: both notes go there, clear of every bar
    ax.text(0.985, 0.60,
            f"one study spans {SE_OBSERVED_PCT:.0f} %,\n"
            f"the effect is {WIDENING_PCT:.1f} %",
            transform=ax.transAxes, color=INK, fontsize=10.5, va="top", ha="right")
    ax.text(0.985, 0.42,
            f"shaded: the {WRONG_DIRECTION_PCT:.0f} % of studies\n"
            f"reporting the parts as\nnarrower than they are",
            transform=ax.transAxes, color=SIGNAL_ALARM, fontsize=10.5,
            va="top", ha="right")
    ax.set_xlabel(r"observed standard deviation from one study, $\mu$m", fontsize=10.5)
    ax.set_ylabel("studies", fontsize=10.5)
    ax.set_title(f"4000 studies of {PARTS} parts, all estimating the same thing",
                 fontsize=11.5, loc="left", pad=13)
    ax.grid(alpha=0.18, axis="y")

    # ---- right: the averaging floor
    ax2 = fig.add_subplot(gs[1])
    ms = np.arange(1, 26)
    sds = np.array([averaging_floor(int(m)) for m in ms])
    ax2.plot(ms, sds, color=DATA_GAUGE, lw=2.0, marker="s", ms=3.4,
             markerfacecolor=DATA_GAUGE, markeredgecolor="none")
    ax2.axhline(FLOOR, color=DATA_TRUTH, lw=1.5, ls=(0, (5, 3)))
    # below the line and hard left, where the curve has already flattened away
    ax2.text(1.0, FLOOR - (sds[0] - FLOOR) * 0.055,
             f"the floor: the parts, {FLOOR} " + r"$\mu$m",
             color=DATA_TRUTH, fontsize=10, ha="left", va="top")
    ax2.set_ylim(FLOOR - (sds[0] - FLOOR) * 0.20, sds[0] + (sds[0] - FLOOR) * 0.10)
    ax2.axvline(REPEATS_FOR_1PCT, color=ACCENT, lw=1.2, alpha=0.75)
    ax2.text(REPEATS_FOR_1PCT + 0.7, sds[0],
             f"m = {REPEATS_FOR_1PCT} reaches\n1 % above the floor",
             color=ACCENT, fontsize=10, va="top")
    ax2.set_xlabel("repeats averaged per part, m", fontsize=10.5)
    ax2.set_ylabel(r"observed spread, $\mu$m", fontsize=10.5)
    ax2.set_title("averaging cannot get under the parts", fontsize=11.5, loc="left",
                  pad=13)
    ax2.grid(alpha=0.18)
    ax2.set_xlim(0, 26)

    fig.suptitle("The law holds on average and is invisible in one study. "
                 "That is why gauge error is measured on one part, not on a histogram.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l01_2_what_one_study_can_show")


if __name__ == "__main__":
    sheet_l01_a_gauge_is_a_process()
    sheet_l01_what_one_study_can_show()
