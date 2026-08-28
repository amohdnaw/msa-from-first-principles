"""LEVEL 3 - figure sheets.

Sheet 1: what an interaction looks like. Two studies of the same gauge, one
    without the term and one with it. Parallel operator lines on the left,
    crossing lines on the right. Non-parallel lines *are* the interaction -
    there is nothing else in the study that shows it.

Sheet 2: what it costs to omit it. Left, both methods' error against the
    interaction strength, averaged over three hundred studies per point, so the
    comparison is not one study's luck. Right, the gauge variance as the two
    methods report it - four terms against three, and the shorter bar is the one
    that flatters the gauge.

    PYTHONPATH=src .venv/bin/python -m msalab.level03
"""
from __future__ import annotations

import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    PANEL_HIGH, RULE, SIGNAL_ALARM, SIGNAL_OK, rc,
)
from msalab.anova import (
    AT_ZERO, BAD_INTERACTION, DIRTY, OPERATORS, PARTS, SWEEP, TRIALS,
    anova, average_and_range, rr_from_anova, study,
)

mpl.rcParams.update(rc())
OP_COLOURS = [DATA_GAUGE, DATA_OBSERVED, ACCENT]


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


# --------------------------------------------------------------- sheet 1
def sheet_l03_parallel_or_not() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, wspace=0.20)

    cases = [(0.0, "no interaction — the lines run parallel"),
             (BAD_INTERACTION, f"interaction {BAD_INTERACTION} µm — they cross")]
    # One shared scale, computed from both studies. Two panels compared by eye
    # must share an axis, and the first version fixed the limit at ±4.4 and
    # clipped the right panel's own data - a figure cannot crop the evidence it
    # is presenting. The extra room at the bottom is a band for the F test.
    centred_all = []
    for interaction, _ in cases:
        cell = study(interaction=interaction)["readings"].mean(axis=2)
        centred_all.append(cell - cell.mean(axis=1, keepdims=True))
    lim = float(max(abs(c).max() for c in centred_all)) * 1.10
    band = lim * 0.34

    for col, (interaction, label) in enumerate(cases):
        s = study(interaction=interaction)
        centred = centred_all[col]

        ax = fig.add_subplot(gs[col])
        xs = np.arange(1, PARTS + 1)
        for i in range(OPERATORS):
            ax.plot(xs, centred[:, i], color=OP_COLOURS[i], lw=2.0, marker="s",
                    ms=4.6, markeredgecolor="none",
                    label=f"operator {chr(65+i)}")
        ax.axhline(0.0, color=RULE, lw=1.2)
        ax.set_xticks(xs)
        ax.set_xlabel("part", fontsize=10.5)
        if col == 0:
            ax.set_ylabel("operator's reading, relative to the part's mean µm",
                          fontsize=10.5)
        ax.set_title(label, fontsize=11.5, loc="left", pad=13)
        ax.grid(alpha=0.18, axis="y")
        ax.set_ylim(-lim - band, lim)

        a = anova(s["readings"])
        # inside the reserved band, below every line
        ax.text(0.03, 0.045,
                f"interaction F = {a['f']['interaction']:5.2f}   "
                f"p = {a['p']['interaction']:.3f}",
                transform=ax.transAxes, fontsize=10.5, family="monospace",
                color=SIGNAL_OK if a["p"]["interaction"] > 0.25 else SIGNAL_ALARM)
        if col == 0:
            leg = ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=3,
                            handlelength=1.4, columnspacing=1.1)
            for tx in leg.get_texts():
                tx.set_family("monospace")

    fig.suptitle("Non-parallel lines ARE the interaction. Nothing else in the "
                 "study shows it, and average-and-range has no term for it.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l03_1_parallel_or_not")


# --------------------------------------------------------------- sheet 2
def sheet_l03_what_omitting_it_costs() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.28)

    # ---- left: the sweep
    ax = fig.add_subplot(gs[0])
    xs = [r["interaction"] for r in SWEEP]
    ax.axhline(0.0, color=DATA_TRUTH, lw=1.5, ls=(0, (5, 3)))
    ax.plot(xs, [r["anova_err"] for r in SWEEP], color=SIGNAL_OK, lw=2.4,
            marker="s", ms=5.2, markeredgecolor="none", label="ANOVA")
    ax.plot(xs, [r["xbar_err"] for r in SWEEP], color=SIGNAL_ALARM, lw=2.4,
            marker="o", ms=5.2, markeredgecolor="none", label="average-and-range")
    ax.set_xlabel(r"interaction, $\mu$m", fontsize=10.5)
    ax.set_ylabel("error against the true gauge, %", fontsize=10.5)
    ax.set_title(f"300 studies at each point, {PARTS}\u00d7{OPERATORS}\u00d7{TRIALS}",
                 fontsize=11.5, loc="left", pad=13)
    ax.grid(alpha=0.18)
    ax.text(xs[-1], 1.5, "the truth", color=DATA_TRUTH, fontsize=10,
            ha="right", va="bottom")
    ax.annotate(f"{SWEEP[-1]['xbar_err']:.0f} %",
                xy=(xs[-1], SWEEP[-1]["xbar_err"]),
                xytext=(xs[-1] - 0.95, SWEEP[-1]["xbar_err"] + 9),
                color=SIGNAL_ALARM, fontsize=11,
                arrowprops=dict(arrowstyle="->", color=SIGNAL_ALARM, lw=1.1))
    leg = ax.legend(frameon=False, fontsize=10, loc="lower left")
    for tx in leg.get_texts():
        tx.set_family("monospace")

    # ---- right: where the variance goes, averaged over many studies
    #
    # The first version drew the single seeded dirty study, where ANOVA
    # overshoots to 143 % - which contradicts the left panel and would have made
    # ANOVA look like the worse method. The claim is about the average, so the
    # figure has to be about the average too. Same 300 studies as the sweep.
    ax2 = fig.add_subplot(gs[1])
    rng = np.random.default_rng(31337)
    acc = {"anova": {"repeat": [], "operator": [], "interaction": []},
           "xbar": {"repeat": [], "operator": []}}
    for _ in range(300):
        reads = study(seed=int(rng.integers(1 << 31)),
                      interaction=BAD_INTERACTION)["readings"]
        rr = rr_from_anova(anova(reads))
        ar = average_and_range(reads)
        for k in ("repeat", "operator", "interaction"):
            acc["anova"][k].append(rr[k])
        acc["xbar"]["repeat"].append(ar["ev"] ** 2)
        acc["xbar"]["operator"].append(ar["av"] ** 2)

    truth_var = 1.0 ** 2 + 1.8 ** 2 + BAD_INTERACTION ** 2
    rows = [
        ("the truth", [("repeat", 1.0 ** 2), ("operator", 1.8 ** 2),
                       ("interaction", BAD_INTERACTION ** 2)]),
        ("ANOVA", [(k, float(np.mean(acc["anova"][k])))
                   for k in ("repeat", "operator", "interaction")]),
        ("average-and-range", [("repeat", float(np.mean(acc["xbar"]["repeat"]))),
                               ("operator", float(np.mean(acc["xbar"]["operator"]))),
                               ("interaction", 0.0)]),
    ]
    cols = {"repeat": DATA_GAUGE, "operator": DATA_OBSERVED,
            "interaction": ACCENT}
    for k, (name, parts) in enumerate(rows):
        left = 0.0
        for term, v in parts:
            pct = v / truth_var * 100
            if pct <= 0:
                continue
            ax2.barh([-k], [pct], left=[left], color=cols[term], height=0.46,
                     label=term if k == 0 else None)
            left += pct
        ax2.text(left + 2.5, -k, f"{left:.0f} %", va="center", color=INK,
                 fontsize=10.5, family="monospace")

    ax2.set_yticks([0, -1, -2])
    ax2.set_yticklabels([r[0] for r in rows], fontsize=10.5)
    ax2.set_xlabel("gauge variance, % of the true gauge variance", fontsize=10.5)
    ax2.set_xlim(0, 124)
    # the legend gets its own row under the bars rather than sitting on one
    ax2.set_ylim(-3.05, 0.6)
    ax2.set_title(f"where the interaction goes: nowhere (mean of 300 studies at "
                  f"{BAD_INTERACTION} µm)", fontsize=11, loc="left", pad=13)
    ax2.grid(alpha=0.18, axis="x")
    leg2 = ax2.legend(frameon=False, fontsize=9.5, loc="lower center", ncol=3,
                      handlelength=1.3, columnspacing=1.2)
    for tx in leg2.get_texts():
        tx.set_family("monospace")

    fig.suptitle("The older method does not misplace the interaction. It omits it, "
                 "so the gauge comes out looking better than it is.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l03_2_what_omitting_it_costs")


if __name__ == "__main__":
    sheet_l03_parallel_or_not()
    sheet_l03_what_omitting_it_costs()
