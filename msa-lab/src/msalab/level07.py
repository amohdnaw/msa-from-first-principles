"""LEVEL 7 - figure sheets.

Sheet 1: the identity. Left, the ceiling against %GRR of tolerance, with the
    three published gates marked and our own gauge on the curve - one hyperbola
    that turns every MSA verdict into a capability verdict. Right, the same fact
    from underneath: observed capability against a process that keeps improving,
    flattening onto its ceiling while the true one runs away.

Sheet 2: what the chart cannot see. Left, five factories with different parts and
    different gauges producing one identical within-subgroup number, their true
    capability spanning more than a factor of two. Right, the detection bill:
    average run length against shift size, as charted and as it would be with a
    perfect gauge, with the gap shaded.
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
from msalab.handshake import (
    AIAG_GATES, CAP, SAME_CHART, SHIFTS, arl, capability, ceiling_table,
)
from msalab.accuracy import GAUGE_SIGMA
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA

mpl.rcParams.update(rc())

MUTED = PANEL_HIGH


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


def sheet_l07_the_identity():
    fig = plt.figure(figsize=(11.0, 4.6))
    gs = fig.add_gridspec(1, 2, wspace=0.30, left=0.07, right=0.97,
                          top=0.80, bottom=0.15)

    # ------------------- left: the ceiling, as one curve
    ax = fig.add_subplot(gs[0])
    grr = np.linspace(4.0, 120.0, 400)
    ceiling = 100.0 / grr
    ax.plot(grr, ceiling, color=SIGNAL_ALARM, lw=2.6)

    for g, label in zip(AIAG_GATES, ("accept", "marginal", "reject")):
        c = 100.0 / g
        ax.plot([g, g], [0, c], color=INK_DIM, lw=1.0, ls=(0, (3, 3)))
        ax.plot([0, g], [c, c], color=INK_DIM, lw=1.0, ls=(0, (3, 3)))
        ax.plot([g], [c], marker="o", ms=5, color=INK_BRIGHT)
        ax.annotate(f"{g:.0f} %  {label}\nCpk ≤ {c:.2f}",
                    xy=(g, c), xytext=(9, 7), textcoords="offset points",
                    fontsize=9.5, color=INK_BRIGHT, va="bottom")

    here = CAP["grr_tolerance_pct"]
    ax.plot([here], [CAP["ceiling"]], marker="o", ms=6, color=ACCENT)
    # every gate labels itself above-right of its point, so this one goes below
    # the curve or it lands on the 30 % gate's second line
    ax.annotate(f"our gauge, {here:.1f} %\nCpk ≤ {CAP['ceiling']:.2f}",
                xy=(here, CAP["ceiling"]), xytext=(26, -30),
                textcoords="offset points", fontsize=9.5, color=ACCENT,
                va="top",
                arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1.0))

    ax.set_xlim(0, 120)
    ax.set_ylim(0, 11.5)
    ax.set_xlabel("%GRR against tolerance", fontsize=10.5)
    ax.set_ylabel("the highest Cpk this gauge permits", fontsize=10.5)
    ax.set_title("one hyperbola joins the two curricula", fontsize=11,
                 color=INK_BRIGHT, loc="left")

    # ------------------- right: approached from underneath
    ax2 = fig.add_subplot(gs[1])
    parts = np.linspace(6.0, 0.12, 300)
    obs = [capability(part=float(p))["observed_cpk"] for p in parts]
    true = [capability(part=float(p))["true_cpk"] for p in parts]

    ax2.plot(parts, true, color=DATA_TRUTH, lw=2.0, ls=(0, (5, 3)))
    ax2.plot(parts, obs, color=SIGNAL_ALARM, lw=2.6)
    ax2.axhline(CAP["ceiling"], color=ACCENT, lw=1.4, ls=(0, (3, 3)))
    ax2.annotate(f"the ceiling, {CAP['ceiling']:.2f}",
                 xy=(5.6, CAP["ceiling"]), xytext=(0, 8),
                 textcoords="offset points", fontsize=9.5, color=ACCENT)
    # the x axis is inverted, so anchoring at parts[-1] puts a right-aligned
    # label past the frame edge. Label where the two curves separate instead.
    def _at(part_value):
        c = capability(part=part_value)
        return c["true_cpk"], c["observed_cpk"]

    t_lab, o_lab = _at(1.6)
    ax2.annotate("true Cpk", xy=(1.6, t_lab), xytext=(30, 14),
                 textcoords="offset points", fontsize=9.5, color=DATA_TRUTH,
                 arrowprops=dict(arrowstyle="-", color=DATA_TRUTH, lw=1.0))
    ax2.annotate("as reported", xy=(1.6, o_lab), xytext=(34, -20),
                 textcoords="offset points", fontsize=9.5, color=SIGNAL_ALARM,
                 arrowprops=dict(arrowstyle="-", color=SIGNAL_ALARM, lw=1.0))

    ax2.plot([PART_SIGMA], [CAP["observed_cpk"]], marker="o", ms=6,
             color=INK_BRIGHT)
    ax2.set_xlim(6.2, 0.0)
    ax2.set_ylim(0, 6.2)
    ax2.set_xlabel("part-to-part spread, µm  (improving to the right)",
                   fontsize=10.5)
    ax2.set_ylabel("Cpk", fontsize=10.5)
    ax2.set_title("perfect the process and it still stops there", fontsize=11,
                  color=INK_BRIGHT, loc="left")

    fig.suptitle("Cpk can never exceed 100 divided by %GRR against tolerance",
                 fontsize=12.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l07_1_the_identity")


def sheet_l07_what_the_chart_cannot_see():
    fig = plt.figure(figsize=(11.0, 4.6))
    gs = fig.add_gridspec(1, 2, wspace=0.28, left=0.07, right=0.97,
                          top=0.80, bottom=0.15, width_ratios=[1.15, 1.0])

    # ------------------- left: five factories, one chart
    ax = fig.add_subplot(gs[0])
    y = np.arange(len(SAME_CHART))
    for i, r in enumerate(SAME_CHART):
        ax.barh(i, r["part"] ** 2, height=0.52, color=MUTED, alpha=0.95)
        ax.barh(i, r["repeat"] ** 2, height=0.52, left=r["part"] ** 2,
                color=SIGNAL_ALARM, alpha=0.85)
        ax.text(r["within_estimate"] ** 2 + 0.6, i,
                f"true Cpk {r['true_cpk']:.2f}", va="center", fontsize=10,
                color=INK_BRIGHT)
    total = SAME_CHART[0]["within_estimate"] ** 2
    ax.axvline(total, color=DATA_TRUTH, lw=1.8)
    # anchored in axes fraction: at data y = len(rows) - 0.35 this sat below the
    # inverted ylim and never rendered
    ax.annotate("what the chart estimates —\nidentical in every row",
                xy=(total, -0.62), xytext=(10, 0),
                textcoords="offset points",
                fontsize=9.5, color=DATA_TRUTH, ha="left", va="center")

    ax.set_yticks(y)
    ax.set_yticklabels([f"{r['gauge_share_of_variance']:.0f} % gauge"
                        for r in SAME_CHART], fontsize=10)
    ax.set_xlim(0, total * 1.62)
    ax.set_xlabel("within-subgroup variance, µm²   "
                  "(parts, then gauge)", fontsize=10.5)
    ax.set_title("five factories the chart reads as one", fontsize=11,
                 color=INK_BRIGHT, loc="left")
    # a header band above row 0, so the callout is not competing with a bar
    ax.set_ylim(len(SAME_CHART) - 0.45, -1.30)

    # ------------------- right: the detection bill
    ax2 = fig.add_subplot(gs[1])
    shifts = np.linspace(0.30, 2.10, 160)
    rows = [arl(float(s)) for s in shifts]
    perfect = [r["arl_if_gauge_were_perfect"] for r in rows]
    charted = [r["arl_as_charted"] for r in rows]

    ax2.fill_between(shifts, perfect, charted, color=SIGNAL_ALARM, alpha=0.22,
                     lw=0)
    ax2.plot(shifts, perfect, color=DATA_TRUTH, lw=2.0, ls=(0, (5, 3)))
    ax2.plot(shifts, charted, color=SIGNAL_ALARM, lw=2.6)
    at05 = arl(0.5)
    ax2.annotate(f"at half a sigma:\n"
                 f"{at05['arl_if_gauge_were_perfect']:.0f} subgroups becomes "
                 f"{at05['arl_as_charted']:.0f}",
                 xy=(0.5, (at05["arl_if_gauge_were_perfect"]
                           + at05["arl_as_charted"]) / 2),
                 xytext=(0.30, 0.60), textcoords="axes fraction",
                 fontsize=9.5, color=INK_BRIGHT,
                 arrowprops=dict(arrowstyle="->", color=INK_DIM, lw=1.0))
    # the curves converge to the bottom-right, so everything above them there is
    # empty; a label under the axis line ran into the x-axis title
    ax2.annotate("as charted", xy=(1.30, arl(1.30)["arl_as_charted"]),
                 xytext=(0.62, 0.44), textcoords="axes fraction", fontsize=9.5,
                 color=SIGNAL_ALARM,
                 arrowprops=dict(arrowstyle="-", color=SIGNAL_ALARM, lw=1.0))
    ax2.annotate("if the gauge were perfect", xy=(1.52, arl(1.52)[
                     "arl_if_gauge_were_perfect"]),
                 xytext=(0.62, 0.26), textcoords="axes fraction", fontsize=9.5,
                 color=DATA_TRUTH,
                 arrowprops=dict(arrowstyle="-", color=DATA_TRUTH, lw=1.0))

    # linear, and stopped where both curves have converged: on a log axis the
    # shaded gap was a sliver and the panel did not show its own claim
    ax2.set_xlim(0.3, 2.1)
    ax2.set_ylim(0, 62)
    ax2.set_xlabel("size of a real process shift, part sigmas", fontsize=10.5)
    ax2.set_ylabel("subgroups until it is caught", fontsize=10.5)
    ax2.set_title("and the wait it adds", fontsize=11, color=INK_BRIGHT,
                  loc="left")

    fig.suptitle("The chart is wider than the process, and was never told",
                 fontsize=12.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l07_2_what_the_chart_cannot_see")


if __name__ == "__main__":
    sheet_l07_the_identity()
    sheet_l07_what_the_chart_cannot_see()
