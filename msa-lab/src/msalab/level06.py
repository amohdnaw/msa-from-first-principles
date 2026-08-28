"""LEVEL 6 - figure sheets.

Sheet 1: kappa is not a free parameter. Left, the same five tables at one
    percent agreement, kappa collapsing as the stream gets lopsided. Right,
    kappa and percent agreement as functions of the variable gauge underneath
    the pass/fail decision - the point being that nobody picks either number.

Sheet 2: where the mistakes are. The part distribution with the two limits, the
    disagreement density on top of it, and the bands at one, two and three gauge
    sigmas annotated with what share of production and what share of mistakes
    each holds.
"""
from __future__ import annotations

import numpy as np

from msalab.attribute import (
    BAND_SIGMAS, GRAY_BANDS, HALF, PARADOX, gray_zone, kappa_from_gauge,
    _pass_prob,
)
from msalab.accuracy import GAUGE_SIGMA, _phi
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA
import os

import matplotlib as mpl
import matplotlib.pyplot as plt

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    PANEL_HIGH, RULE, SIGNAL_ALARM, SIGNAL_OK, rc,
)

mpl.rcParams.update(rc())

#: The "where the parts are" fill. PANEL_HIGH is the raised-surface token, which
#: is what a background mass should read as against the ground.
MUTED = PANEL_HIGH


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


def sheet_l06_kappa_is_not_free():
    fig = plt.figure(figsize=(11.0, 4.6))
    gs = fig.add_gridspec(1, 2, wspace=0.28, left=0.07, right=0.97,
                          top=0.80, bottom=0.14)

    # ---------------- left: one agreement, five kappas
    ax = fig.add_subplot(gs[0])
    shares = [r["share_of_agreement_in_pass"] * 100 for r in PARADOX]
    kappas = [r["kappa"] for r in PARADOX]
    obs = PARADOX[0]["observed"] * 100

    ax.plot(shares, [obs] * len(shares), color=DATA_TRUTH, lw=2.2,
            marker="o", ms=5, label="percent agreement")
    ax.plot(shares, [k * 100 for k in kappas], color=SIGNAL_ALARM, lw=2.4,
            marker="o", ms=5, label="kappa")
    for i, (s, k) in enumerate(zip(shares, kappas)):
        # the last point sits at the bottom-right corner, where a label below it
        # would land on the note and the arrow; it goes to the left instead
        off = (-30, 2) if i == len(shares) - 1 else (0, -15)
        ax.annotate(f"{k:.2f}", xy=(s, k * 100), xytext=off,
                    textcoords="offset points", color=SIGNAL_ALARM,
                    fontsize=10, ha="right" if i == len(shares) - 1 else "center")
    ax.set_xlim(45, 102)
    ax.set_ylim(-6, 108)
    ax.set_xlabel("share of the agreement sitting in the 'pass' cell, %",
                  fontsize=10.5)
    ax.set_ylabel("%", fontsize=10.5)
    ax.set_title("one percent agreement, five kappas", fontsize=11,
                 color=INK_BRIGHT, loc="left")
    ax.legend(loc="center left", fontsize=9.5, frameon=False)
    ax.text(0.04, 0.10, "a capable process lives at this end  \u2192",
            transform=ax.transAxes, fontsize=9.5, color=INK_DIM, ha="left")

    # ---------------- right: both, as functions of the gauge
    ax2 = fig.add_subplot(gs[1])
    gauges = np.linspace(0.25, 9.0, 60)
    rows = kappa_from_gauge(tuple(float(g) for g in gauges))
    grr = [r["grr_tolerance_pct"] for r in rows]
    ax2.plot(grr, [r["agreement"] * 100 for r in rows], color=DATA_TRUTH, lw=2.2)
    ax2.plot(grr, [r["kappa"] * 100 for r in rows], color=SIGNAL_ALARM, lw=2.4)
    ax2.plot(grr, [r["effectiveness"] * 100 for r in rows], color=SIGNAL_OK,
             lw=1.8, ls=(0, (5, 3)))

    here = 6.0 * GAUGE_SIGMA / TOLERANCE * 100.0
    mine = kappa_from_gauge((GAUGE_SIGMA,))[0]
    ax2.axvline(here, color=ACCENT, lw=1.4, ls=(0, (3, 3)))
    # the legend owns the right half at mid height, so the callout goes below
    # the two flat curves and above kappa's tail, left-aligned off the rule
    ax2.annotate(f"the gauge Levels 2-5 built\n"
                 f"agreement {mine['agreement']*100:.2f} %\n"
                 f"kappa {mine['kappa']:.3f}",
                 xy=(here, 78), xytext=(here + 6, 60),
                 fontsize=9.5, color=ACCENT, va="center", ha="left",
                 arrowprops=dict(arrowstyle="-", color=ACCENT, lw=1.0))
    # Three curves plus a callout leaves no region a legend box can occupy -
    # measured at three pixels of clearance. Labelling each curve at its own
    # right-hand end needs no empty region at all, only x-axis headroom.
    ax2.set_xlim(0, 218)
    ax2.set_ylim(-4, 108)
    for series, colour, label in (
            ("effectiveness", SIGNAL_OK, "effectiveness"),
            ("agreement", DATA_TRUTH, "percent agreement"),
            ("kappa", SIGNAL_ALARM, "kappa")):
        yv = rows[-1][series] * 100
        ax2.annotate(label, xy=(grr[-1], yv), xytext=(6, 0),
                     textcoords="offset points", color=colour, fontsize=9.5,
                     va="center", ha="left")
    ax2.set_xlabel("the variable gauge underneath, %GRR against tolerance",
                   fontsize=10.5)
    ax2.set_ylabel("%", fontsize=10.5)
    ax2.set_title("nobody chooses either number", fontsize=11,
                  color=INK_BRIGHT, loc="left")

    fig.suptitle("An attribute gauge is a variable gauge with the number thrown "
                 "away", fontsize=12.5, color=INK_BRIGHT, x=0.055, ha="left",
                 y=1.045)
    _save(fig, "l06_1_kappa_is_not_free")


def sheet_l06_where_the_mistakes_are():
    fig = plt.figure(figsize=(11.0, 4.6))
    gs = fig.add_gridspec(1, 2, wspace=0.26, left=0.07, right=0.97,
                          top=0.80, bottom=0.14, width_ratios=[1.25, 1.0])

    # ---------------- left: the two densities, on one axis
    ax = fig.add_subplot(gs[0])
    xs = np.linspace(-24, 24, 1200)
    parts = np.array([_phi(float(x), PART_SIGMA) for x in xs])
    dis = np.array([_phi(float(x), PART_SIGMA)
                    * 2.0 * _pass_prob(float(x)) * (1.0 - _pass_prob(float(x)))
                    for x in xs])

    ax.fill_between(xs, parts / parts.max(), color=MUTED, alpha=0.55, lw=0)
    ax.plot(xs, dis / dis.max(), color=SIGNAL_ALARM, lw=2.4)
    for v in (-HALF, HALF):
        ax.axvline(v, color=DATA_TRUTH, lw=1.8)
    ax.set_xlim(-24, 24)
    ax.set_ylim(0, 1.42)
    # Labelled in place rather than in a legend box: the two curves and the two
    # limit lines leave no rectangle a legend can occupy without crossing one.
    ax.text(0.0, 0.42, "where the parts are", color=INK_DIM, fontsize=9.5,
            ha="center")
    # centred between the two peaks: at x=-13 the label ran through the left
    # limit line, and either peak position does the same to its own limit
    ax.text(0.0, 1.10, "where the disagreements are", color=SIGNAL_ALARM,
            fontsize=9.5, ha="center")
    ax.text(HALF, 1.33, "  the go/no-go limits", color=DATA_TRUTH,
            fontsize=9.5, ha="left")
    ax.set_xlabel("the part's true size, µm from nominal", fontsize=10.5)
    ax.set_ylabel("density, each to its own peak", fontsize=10.5)
    ax.set_title("two distributions that barely overlap", fontsize=11,
                 color=INK_BRIGHT, loc="left")
    ax.set_yticks([])

    # ---------------- right: the bands, as shares
    ax2 = fig.add_subplot(gs[1])
    labels = [f"±{s}σ" for s in (1, 2, 3)]
    y = np.arange(3)
    p_share = [r["parts_in_band_pct"] for r in GRAY_BANDS]
    m_share = [r["disagreements_in_band_pct"] for r in GRAY_BANDS]

    ax2.barh(y + 0.19, m_share, height=0.34, color=SIGNAL_ALARM, alpha=0.85)
    ax2.barh(y - 0.19, p_share, height=0.34, color=MUTED, alpha=0.9)
    for i, (ps, ms, r) in enumerate(zip(p_share, m_share, GRAY_BANDS)):
        # the series name rides on the top group's two bars, so no legend box
        # has to find a gap between them
        tail = "  of the mistakes" if i == 0 else ""
        head = "  of production" if i == 0 else ""
        ax2.text(ms + 1.6, i + 0.19, f"{ms:.1f} %{tail}", va="center",
                 fontsize=10, color=SIGNAL_ALARM)
        ax2.text(ps + 1.6, i - 0.19, f"{ps:.2f} %{head}", va="center",
                 fontsize=10, color=INK_DIM)
        ax2.text(148, i, f"{r['concentration']:.0f}×", va="center",
                 fontsize=11, color=INK_BRIGHT, ha="right")
    ax2.text(148, -0.72, "concentration", va="center", fontsize=9.5,
             color=INK_DIM, ha="right")
    ax2.set_yticks(y)
    ax2.set_yticklabels([f"within {l}  of the limit" for l in labels],
                        fontsize=10)
    ax2.set_xlim(0, 152)
    ax2.set_xticks([0, 25, 50, 75, 100])
    ax2.set_ylim(2.6, -0.95)
    ax2.set_xlabel("share, %", fontsize=10.5)
    ax2.set_title("the band is set by the gauge, not the appraiser",
                  fontsize=11, color=INK_BRIGHT, loc="left")

    fig.suptitle("Six percent of production carries ninety-nine percent of the "
                 "mistakes", fontsize=12.5, color=INK_BRIGHT, x=0.055,
                 ha="left", y=1.045)
    _save(fig, "l06_2_where_the_mistakes_are")


if __name__ == "__main__":
    sheet_l06_kappa_is_not_free()
    sheet_l06_where_the_mistakes_are()
