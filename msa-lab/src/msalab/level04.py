"""LEVEL 4 - figure sheets.

Sheet 1: against what. Left, one gauge spread drawn against the two things it
    might be compared to - the study spread and the tolerance band - so
    "a percentage of what" is a picture rather than a phrase. Right, the verdict
    map: every combination of part spread and tolerance, coloured by whether the
    two AIAG gates agree, with the two example gauges marked on it.

Sheet 2: what the numbers are worth. Left, ndc against the study ratio, with
    both printed gates on it - they are different lines, and the gap is the
    finding. Right, the conformance decision itself: readings against truth with
    the limits drawn, and the four outcomes counted, centred and shifted.

    PYTHONPATH=src .venv/bin/python -m msalab.level04
"""
from __future__ import annotations

import math
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    PANEL, PANEL_HIGH, RULE, SIGNAL_ALARM, SIGNAL_OK, rc,
)
from msalab.against_what import (
    ACCEPT_PCT, A_PART, A_TOL, B_PART, B_TOL, CENTRED, GAUGE_SIGMA, NDC_MIN,
    REJECT_PCT, SHIFTED, STUDY_PCT_AT_NDC5, TOLERANCE, ndc_from_study_ratio,
    study_ratio, tolerance_ratio, verdict,
)
from msalab.measurement import PART_SIGMA

mpl.rcParams.update(rc())


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


# --------------------------------------------------------------- sheet 1
def sheet_l04_against_what() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.2], wspace=0.26)

    # ---- left: one numerator, two denominators, drawn to scale
    ax = fig.add_subplot(gs[0])
    g6 = 6 * GAUGE_SIGMA
    s6 = 6 * math.hypot(PART_SIGMA, GAUGE_SIGMA)
    rows = [("the gauge\n6\u03c3", g6, ACCENT),
            ("the study spread\n6\u03c3 observed", s6, DATA_OBSERVED),
            ("the tolerance\nfrom the drawing", TOLERANCE, DATA_TRUTH)]
    for i, (name, w, colour) in enumerate(rows):
        ax.barh([-i], [w], color=colour, height=0.44, alpha=0.72)
        ax.text(w + 1.2, -i, f"{w:.1f} " + r"$\mu$m", va="center", color=colour,
                fontsize=11, family="monospace")
    ax.set_yticks([0, -1, -2])
    ax.set_yticklabels([r[0] for r in rows], fontsize=10.5)
    ax.set_xlim(0, max(s6, TOLERANCE) * 1.30)
    ax.set_ylim(-3.75, 0.95)
    ax.set_xlabel(r"$\mu$m", fontsize=10.5)
    ax.grid(alpha=0.18, axis="x")
    ax.set_title("one numerator, two denominators", fontsize=11.5, loc="left",
                 pad=13)
    # its own band: at 0.10 it sat across the tolerance bar
    ax.text(0.02, 0.085,
            f"gauge / study spread   = {study_ratio():4.1f} %\n"
            f"gauge / tolerance      = {tolerance_ratio():4.1f} %",
            transform=ax.transAxes, fontsize=10.5, family="monospace", color=INK)

    # ---- right: the verdict map
    ax2 = fig.add_subplot(gs[1])
    parts = np.linspace(0.6, 30.0, 260)
    tols = np.linspace(8.0, 170.0, 260)
    P, T = np.meshgrid(parts, tols)
    sr = GAUGE_SIGMA / np.sqrt(PART_SIGMA * 0 + P ** 2 + GAUGE_SIGMA ** 2) * 100
    tr = 6.0 * GAUGE_SIGMA / T * 100

    def band(x):
        return np.where(x <= ACCEPT_PCT, 0, np.where(x > REJECT_PCT, 2, 1))

    agree = (band(sr) == band(tr)).astype(float)
    # 0 = the gates disagree, 1 = they agree
    cmap = ListedColormap([SIGNAL_ALARM, PANEL_HIGH])
    ax2.pcolormesh(P, T, agree, cmap=cmap, shading="auto", vmin=0, vmax=1)

    for x, y, tag, colour in [(A_PART, A_TOL, "A", INK_BRIGHT),
                              (B_PART, B_TOL, "B", INK_BRIGHT),
                              (PART_SIGMA, TOLERANCE, "this study", INK_BRIGHT)]:
        ax2.scatter([x], [y], s=70, color=colour, marker="s", zorder=5,
                    edgecolors="none")
        # offset away from the nearest boundary rather than always up-right,
        # where "this study" landed exactly on a verdict edge
        dx, dy = (1.4, 7) if y > 60 else (1.4, -11)
        ax2.annotate(tag, xy=(x, y), xytext=(x + dx, y + dy),
                     color=colour, fontsize=11)

    ax2.set_xlabel(r"part-to-part spread, $\mu$m", fontsize=10.5)
    ax2.set_ylabel(r"tolerance, $\mu$m", fontsize=10.5)
    ax2.set_title(f"where the two gates disagree — one gauge, "
                  f"{GAUGE_SIGMA:.2f} " + r"$\mu$m", fontsize=11.5, loc="left",
                  pad=13)
    ax2.text(0.985, 0.955, "salmon: the two verdicts differ\ndark: they agree",
             transform=ax2.transAxes, ha="right", va="top", fontsize=10.5,
             color=INK_BRIGHT)

    fig.suptitle("A verdict is a percentage, and a percentage needs a denominator. "
                 "The two usual choices are answering different questions.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l04_1_against_what")


# --------------------------------------------------------------- sheet 2
def sheet_l04_what_the_numbers_are_worth() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.25], wspace=0.28)

    # ---- left: ndc is a function of the study ratio
    ax = fig.add_subplot(gs[0])
    rs = np.linspace(3.0, 70.0, 400)
    ax.plot(rs, [ndc_from_study_ratio(float(r)) for r in rs],
            color=DATA_OBSERVED, lw=2.4)
    ax.axhline(NDC_MIN, color=ACCENT, lw=1.6, ls=(0, (5, 3)))
    ax.axvline(REJECT_PCT, color=SIGNAL_ALARM, lw=1.6)
    ax.axvline(STUDY_PCT_AT_NDC5, color=ACCENT, lw=1.6)
    ax.set_xlim(3, 70)
    ax.set_ylim(0, 22)
    ax.set_xlabel("%GRR against study variation", fontsize=10.5)
    ax.set_ylabel("ndc", fontsize=10.5)
    ax.set_title("ndc is a function of the study ratio and nothing else",
                 fontsize=11, loc="left", pad=13)
    ax.grid(alpha=0.18)
    ax.text(REJECT_PCT + 1.2, 19.5, f"reject above\n{REJECT_PCT:.0f} %",
            color=SIGNAL_ALARM, fontsize=10.5, va="top")
    ax.text(STUDY_PCT_AT_NDC5 - 1.2, 19.5,
            f"ndc reaches {NDC_MIN}\nat {STUDY_PCT_AT_NDC5:.1f} %",
            color=ACCENT, fontsize=10.5, va="top", ha="right")
    ax.text((STUDY_PCT_AT_NDC5 + REJECT_PCT) / 2, 2.7,
            f"{REJECT_PCT - STUDY_PCT_AT_NDC5:.1f} points apart,\n"
            f"printed in the same table",
            color=INK_BRIGHT, fontsize=10, ha="center", va="bottom")

    # ---- right: the decision itself
    ax2 = fig.add_subplot(gs[1])
    rng = np.random.default_rng(77)
    n = 2600
    half = TOLERANCE / 2
    truth = rng.normal(0.0, PART_SIGMA, n)
    read = truth + rng.normal(0.0, GAUGE_SIGMA, n)
    good, passed = np.abs(truth) <= half, np.abs(read) <= half

    ax2.scatter(truth[good & passed], read[good & passed], s=4,
                color=INK_DIM, alpha=0.45, edgecolors="none", label="correct")
    ax2.scatter(truth[~good & ~passed], read[~good & ~passed], s=4,
                color=INK_DIM, alpha=0.45, edgecolors="none")
    ax2.scatter(truth[~good & passed], read[~good & passed], s=22,
                color=SIGNAL_ALARM, edgecolors="none",
                label="bad part, accepted")
    ax2.scatter(truth[good & ~passed], read[good & ~passed], s=22,
                color=ACCENT, edgecolors="none",
                label="good part, rejected")

    for v in (-half, half):
        ax2.axvline(v, color=DATA_TRUTH, lw=1.3, ls=(0, (4, 3)))
        ax2.axhline(v, color=DATA_TRUTH, lw=1.3)
    ax2.set_ylim(-half * 1.62, half * 1.62)
    ax2.set_xlabel(r"the part's true size, $\mu$m", fontsize=10.5)
    ax2.set_ylabel(r"what the gauge read, $\mu$m", fontsize=10.5)
    ax2.set_title("the decision a percentage was standing in for",
                  fontsize=11.5, loc="left", pad=13)
    ax2.grid(alpha=0.15)
    leg = ax2.legend(frameon=False, fontsize=9.5, loc="upper left",
                     markerscale=1.6, bbox_to_anchor=(0.0, 1.005))
    for t in leg.get_texts():
        t.set_family("monospace")
    # two lines, not three: measured clearance against the lower limit line was
    # 0.169 against 0.191 in axes fraction, which is too tight to trust at
    # render scale, and shorter copy is better copy anyway
    ax2.text(0.98, 0.03,
             f"{CENTRED['bad_parts_accepted_pct']:.0f} % of the bad parts are accepted\n"
             f"shift the process and scrap goes "
             f"{CENTRED['scrap_rate_pct']:.2f} % \u2192 "
             f"{SHIFTED['scrap_rate_pct']:.1f} %",
             transform=ax2.transAxes, ha="right", va="bottom", fontsize=10,
             color=INK)

    fig.suptitle("ndc cannot disagree with the study ratio. And neither of them "
                 "knows what the decision costs.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l04_2_what_the_numbers_are_worth")


if __name__ == "__main__":
    sheet_l04_against_what()
    sheet_l04_what_the_numbers_are_worth()
