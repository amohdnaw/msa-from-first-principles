"""LEVEL 2 - figure sheets.

Sheet 1: the split. Left, one part read nine times - three operators, three
    trials each - so the two kinds of spread are visible as two different
    distances: scatter inside an operator's column is repeatability, distance
    between the columns is reproducibility. Right, the same two numbers as a
    variance bar with both fixes priced on it.

Sheet 2: why the operator term is the one you cannot trust. Left, the sampling
    distribution of the naive estimator and of the corrected one on a
    repeatability-dominant gauge, with the spike at zero that the clamp
    produces. Right, relative error against degrees of freedom, with the two
    points a standard study actually occupies.

    PYTHONPATH=src .venv/bin/python -m msalab.level02
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
from msalab.reproducibility import (
    CORRECTED_MEAN, HALVE_REPEAT_PCT, HALVE_REPRODUCE_PCT, NAIVE_MEAN,
    NEGATIVE_PCT, NOISY_EXPECTED_NAIVE, NOISY_REPEAT, NOISY_REPRODUCE,
    OPERATORS, PARTS, REPEAT_DF, REPRODUCE_DF, SIGMA_REPEAT, SIGMA_REPRODUCE,
    TRIALS, gauge_sigma, operator_mean_spread, relative_error, repeatability,
    reproducibility, study,
)

mpl.rcParams.update(rc())


def _save(fig, name: str) -> None:
    os.makedirs("docs", exist_ok=True)
    fig.savefig(f"docs/{name}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote docs/{name}.png")


# --------------------------------------------------------------- sheet 1
def sheet_l02_two_distances() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.28)

    s = study()
    reads = s["readings"]                        # (parts, operators, trials)
    op_means = reads.mean(axis=2)                # (parts, operators)

    # ---- left: every part, every operator
    #
    # Drawn across all ten parts rather than on one, because on a single part the
    # within-operator scatter can be as large as the between-operator gap - it was,
    # on the first version of this sheet - and the picture then argues against the
    # distinction it is making. Reproducibility is an offset that PERSISTS across
    # parts, so the persistence is the thing to draw. The lines coming out roughly
    # parallel is also exactly what Level 3 breaks.
    ax = fig.add_subplot(gs[0])
    xs = np.arange(1, PARTS + 1)
    colours = [DATA_GAUGE, DATA_OBSERVED, ACCENT]
    for i in range(OPERATORS):
        ax.plot(xs, op_means[:, i], color=colours[i], lw=1.8, marker="s", ms=4.2,
                markeredgecolor="none", label=f"operator {chr(65+i)}", zorder=4)
        for k in range(PARTS):
            ax.scatter([xs[k]] * TRIALS, reads[k, i], s=9, color=colours[i],
                       alpha=0.5, marker="o", edgecolors="none", zorder=3)

    # the two distances, marked where they are largest. The arrows carry the
    # measurement and a key carries the words: labelling the arrows in place put
    # text straight across three operator lines, and the reader lost both.
    k = int(np.argmax(op_means.max(axis=1) - op_means.min(axis=1)))
    hi, lo = op_means[k].max(), op_means[k].min()
    ax.annotate("", xy=(xs[k] + 0.30, lo), xytext=(xs[k] + 0.30, hi),
                arrowprops=dict(arrowstyle="<->", color=INK_BRIGHT, lw=1.5))
    j = int(np.argmax(reads[k].std(axis=1)))
    cell = reads[k, j]
    ax.annotate("", xy=(xs[k] - 0.30, cell.min()), xytext=(xs[k] - 0.30, cell.max()),
                arrowprops=dict(arrowstyle="<->", color=INK_DIM, lw=1.5))

    # the key gets its own band rather than hunting for a gap: every candidate
    # region already had a line or a trial dot in it at some part
    ymin, ymax = ax.get_ylim()
    ax.set_ylim(ymin - (ymax - ymin) * 0.19, ymax)
    ax.text(0.03, 0.105,
            f"scatter at one point   = repeatability   {SIGMA_REPEAT} " + r"$\mu$m",
            transform=ax.transAxes, color=INK_DIM, fontsize=10.5)
    ax.text(0.03, 0.035,
            f"gap between the lines  = reproducibility {SIGMA_REPRODUCE} " + r"$\mu$m",
            transform=ax.transAxes, color=INK_BRIGHT, fontsize=10.5)

    ax.set_xlabel("part", fontsize=10.5)
    ax.set_ylabel(r"reading, $\mu$m from nominal", fontsize=10.5)
    ax.set_title(f"{PARTS} parts, {OPERATORS} operators, {TRIALS} trials each",
                 fontsize=11.5, loc="left", pad=13)
    ax.set_xticks(xs)
    ax.set_xlim(0.2, PARTS + 0.8)
    ax.grid(alpha=0.18, axis="y")
    leg = ax.legend(frameon=False, fontsize=9.5, loc="upper left", ncol=3,
                    handlelength=1.4, columnspacing=1.1)
    for tx in leg.get_texts():
        tx.set_family("monospace")

    # ---- right: the variance bar, with both fixes priced
    ax2 = fig.add_subplot(gs[1])
    rep_var = SIGMA_REPEAT ** 2
    rpr_var = SIGMA_REPRODUCE ** 2
    total = rep_var + rpr_var
    ax2.barh([0], [rep_var / total * 100], color=DATA_GAUGE, height=0.40,
             label=f"repeatability  {SIGMA_REPEAT} " + r"$\mu$m")
    ax2.barh([0], [rpr_var / total * 100], left=[rep_var / total * 100],
             color=DATA_OBSERVED, height=0.40,
             label=f"reproducibility {SIGMA_REPRODUCE} " + r"$\mu$m")
    ax2.text(rep_var / total * 50, 0, f"{rep_var/total*100:.0f} %",
             ha="center", va="center", color=INK_BRIGHT, fontsize=11,
             family="monospace")
    ax2.text(rep_var / total * 100 + rpr_var / total * 50, 0,
             f"{rpr_var/total*100:.0f} %", ha="center", va="center",
             color=INK_BRIGHT, fontsize=11, family="monospace")

    ax2.barh([-0.9], [HALVE_REPEAT_PCT], color=DATA_GAUGE, height=0.30, alpha=0.6)
    ax2.barh([-1.4], [HALVE_REPRODUCE_PCT], color=DATA_OBSERVED, height=0.30,
             alpha=0.6)
    ax2.text(HALVE_REPEAT_PCT + 2, -0.9,
             f"halve repeatability: {HALVE_REPEAT_PCT:.1f} % better",
             va="center", color=DATA_GAUGE, fontsize=10)
    ax2.text(HALVE_REPRODUCE_PCT + 2, -1.4,
             f"halve reproducibility: {HALVE_REPRODUCE_PCT:.1f} %",
             va="center", color=DATA_OBSERVED, fontsize=10)

    ax2.set_yticks([0, -0.9, -1.4])
    ax2.set_yticklabels(["variance", "fix A", "fix B"], fontsize=10)
    ax2.set_xlim(0, 100)
    ax2.set_ylim(-1.9, 0.5)
    ax2.set_xlabel("percent", fontsize=10.5)
    ax2.set_title(f"the gauge term split — total {gauge_sigma():.2f} " + r"$\mu$m",
                  fontsize=11.5, loc="left", pad=13)
    ax2.grid(alpha=0.18, axis="x")
    leg2 = ax2.legend(frameon=False, fontsize=9.5, loc="lower right")
    for tx in leg2.get_texts():
        tx.set_family("monospace")

    fig.suptitle("Two questions, one word. The distances are different sizes and "
                 "they have different fixes.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l02_1_two_distances")


# --------------------------------------------------------------- sheet 2
def sheet_l02_the_operator_term() -> None:
    fig = plt.figure(figsize=(12.6, 4.9))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.3, 1.0], wspace=0.26)

    # ---- left: the two estimators, sampled
    rng = np.random.default_rng(4242)
    naive, corr = [], []
    for _ in range(3000):
        r = study(seed=int(rng.integers(1 << 31)), repeat=NOISY_REPEAT,
                  reproduce=NOISY_REPRODUCE)["readings"]
        naive.append(operator_mean_spread(r))
        corr.append(reproducibility(r))
    naive, corr = np.array(naive), np.array(corr)

    ax = fig.add_subplot(gs[0])
    bins = np.linspace(0, max(naive.max(), 1.4), 62)
    n_naive, _, _ = ax.hist(naive, bins=bins, color=SIGNAL_ALARM, alpha=0.45,
                            edgecolor="none",
                            label=f"uncorrected  mean {naive.mean():.3f}")
    n_corr, _, patches = ax.hist(corr, bins=bins, color=SIGNAL_OK, alpha=0.45,
                                 edgecolor="none",
                                 label=f"clamped     mean {corr.mean():.3f}")

    # The clamp piles 47 % of studies into the first bin, which is nine times
    # the tallest real bar and flattens both distributions to nothing. The axis
    # is clipped so the shapes are readable, and the spike's true height is
    # printed on it - hiding it would be worse than squashing them.
    spike = int(n_corr[0])
    tallest_real = max(n_naive.max(), n_corr[1:].max())
    ax.set_ylim(0, tallest_real * 1.55)
    ax.annotate(f"{spike} studies\n({NEGATIVE_PCT:.0f} %) land at zero:\n"
                f"the correction went\nnegative and was clamped",
                xy=(bins[1] * 1.1, tallest_real * 1.42),
                xytext=(NOISY_REPRODUCE + 0.22, tallest_real * 1.46),
                color=ACCENT, fontsize=10.5, va="top",
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=1.1))

    ax.axvline(NOISY_REPRODUCE, color=DATA_TRUTH, lw=1.8)
    ax.text(NOISY_REPRODUCE + 0.02, tallest_real * 0.62,
            f"the truth\n{NOISY_REPRODUCE}", color=DATA_TRUTH, fontsize=10.5,
            va="center")
    ax.set_xlabel(r"estimated reproducibility, $\mu$m", fontsize=10.5)
    ax.set_ylabel("studies", fontsize=10.5)
    ax.set_title(f"3000 studies · repeat {NOISY_REPEAT}, reproduce "
                 f"{NOISY_REPRODUCE}", fontsize=11.5, loc="left", pad=13)
    ax.grid(alpha=0.18, axis="y")
    leg = ax.legend(frameon=False, fontsize=9.5, loc="center right")
    for tx in leg.get_texts():
        tx.set_family("monospace")

    # ---- right: what df buys
    ax2 = fig.add_subplot(gs[1])
    dfs = np.arange(1, 81)
    err = np.array([relative_error(int(d)) * 100 for d in dfs])
    ax2.plot(dfs, err, color=INK, lw=2.0)
    for d, colour, label in [(REPRODUCE_DF, DATA_OBSERVED,
                              f"reproducibility\n{OPERATORS} operators, "
                              f"{REPRODUCE_DF} df"),
                             (REPEAT_DF, DATA_GAUGE,
                              f"repeatability\n{REPEAT_DF} df")]:
        e = relative_error(d) * 100
        ax2.scatter([d], [e], s=64, color=colour, zorder=5, marker="s",
                    edgecolors="none")
        ax2.annotate(f"{label}\n{e:.0f} % error",
                     xy=(d, e), xytext=(d + 8, e + (7 if d < 10 else 9)),
                     color=colour, fontsize=10,
                     arrowprops=dict(arrowstyle="-", color=colour, lw=0.9))
    ax2.set_xlabel("degrees of freedom", fontsize=10.5)
    ax2.set_ylabel("relative error of the estimate, %", fontsize=10.5)
    ax2.set_title("what a standard study can know", fontsize=11.5, loc="left",
                  pad=13)
    ax2.grid(alpha=0.18)
    ax2.set_xlim(0, 82)
    ax2.set_ylim(0, 78)

    fig.suptitle("The operator term is the one a standard study cannot pin: too "
                 "high uncorrected, too low once clamped, and two degrees of freedom.",
                 fontsize=13.5, color=INK_BRIGHT, x=0.055, ha="left", y=1.045)
    _save(fig, "l02_2_the_operator_term")


if __name__ == "__main__":
    sheet_l02_two_distances()
    sheet_l02_the_operator_term()
