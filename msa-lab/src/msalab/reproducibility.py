"""LEVEL 2 - Repeatability and reproducibility.

Level 1 measured the gauge term whole: the spread of readings on one part, taken
by one operator on one afternoon. This level splits it, because that spread was
answering only half a question.

    same operator, same part, again    -> repeatability
    different operator, same part      -> reproducibility

The plant calls the pair one word. They have different sizes, different causes
and different fixes, and aiming the wrong fix at the wrong term is the most
expensive ordinary mistake in this subject.

Five claims, each computed here and nowhere else:

1. The same law as Level 1, one level down: the two terms add in quadrature to
   the gauge spread Level 1 measured.
2. The fixes are not interchangeable, and the asymmetry is arithmetic rather
   than rhetorical. On the study here, halving repeatability buys 9 % and
   halving reproducibility buys 35 %.
3. Reproducibility cannot be read off the spread of the operator averages,
   because that spread *contains repeatability* - each average is itself noisy.
   The naive number overstates, and on a repeatability-dominant gauge it
   overstates enormously.
4. The correction that removes it can drive the estimate below zero, which is
   not a coding error but an estimator meeting a boundary. It happens often
   enough to matter and it is reported as zero, which hides it.
5. Three operators give two degrees of freedom. Whatever reproducibility number
   a standard study produces, it is a very poor estimate, and this level says
   so with a number rather than a caveat.

    PYTHONPATH=src .venv/bin/python -m msalab.reproducibility
"""
from __future__ import annotations

import math

import numpy as np

from msalab.measurement import PART_SIGMA, c4

# ---------------------------------------------------------------- the study
# The AIAG-shaped study: ten parts, three operators, three trials each. Same
# bores as Level 1, so the part spread carries over and the two levels are
# measuring one process.
PARTS = 10
OPERATORS = 3
TRIALS = 3
SEED = 202

#: The instance this level argues from: reproducibility is the bigger term.
#: Chosen because it is the case where the wrong fix is tempting - the
#: instrument looks fine when you check it yourself.
SIGMA_REPEAT = 1.0
SIGMA_REPRODUCE = 1.8

#: A second instance, for claim 3. When repeatability dominates and the study is
#: small, the naive reproducibility estimator is badly wrong - and this is the
#: common shape in practice, because a noisy instrument is easy to buy.
NOISY_REPEAT = 3.0
NOISY_REPRODUCE = 0.4


def gauge_sigma(repeat: float = SIGMA_REPEAT,
                reproduce: float = SIGMA_REPRODUCE) -> float:
    """The whole gauge term, which is what Level 1 measured.

    Same quadrature law as Level 1, applied one level down. This is the only
    line connecting the two levels, and it is deliberately the same function
    shape so the reader recognises it.
    """
    return math.hypot(repeat, reproduce)


def study(seed: int = SEED, parts: int = PARTS, operators: int = OPERATORS,
          trials: int = TRIALS, part_sigma: float = PART_SIGMA,
          repeat: float = SIGMA_REPEAT, reproduce: float = SIGMA_REPRODUCE,
          ) -> dict:
    """One R&R study. Shape is (parts, operators, trials).

    The operator effect is drawn once per operator and applied to every reading
    that operator takes - that is what reproducibility *is*, an offset that
    persists across the parts rather than fresh noise on each reading. Getting
    this wrong turns reproducibility into extra repeatability, which is exactly
    the confusion the level is about.
    """
    rng = np.random.default_rng(seed)
    truth = rng.normal(0.0, part_sigma, parts)
    op_effect = rng.normal(0.0, reproduce, operators)
    noise = rng.normal(0.0, repeat, (parts, operators, trials))
    reads = truth[:, None, None] + op_effect[None, :, None] + noise
    return {"readings": reads, "truth": truth, "op_effect": op_effect,
            "parts": parts, "operators": operators, "trials": trials}


def repeatability(reads: np.ndarray) -> float:
    """Pooled within-operator-within-part spread: the instrument talking to itself.

    Every part-operator cell contributes `trials - 1` degrees of freedom, so this
    is the well-estimated term in any R&R study - and the reason Level 1 could
    trust its within-part number.
    """
    cell_means = reads.mean(axis=2, keepdims=True)
    dev = reads - cell_means
    df = reads.shape[0] * reads.shape[1] * (reads.shape[2] - 1)
    return float(math.sqrt((dev ** 2).sum() / df))


def operator_mean_spread(reads: np.ndarray) -> float:
    """Standard deviation of the operator averages. NOT reproducibility.

    This is the number people report, and it is wrong in a specific direction:
    each operator average is itself measured with error, so its spread carries
    repeatability as well as the operator effect.
    """
    return float(reads.mean(axis=(0, 2)).std(ddof=1))


def reproducibility(reads: np.ndarray, clamp: bool = True) -> float:
    """Reproducibility, with the repeatability removed from the operator spread.

    Each operator average is over `parts * trials` readings, so it carries
    `repeat^2 / (parts * trials)` of variance that has nothing to do with the
    operator. Subtracting it is not a refinement - on a repeatability-dominant
    gauge the uncorrected number can be several times too large.

    The subtraction can also go negative, because a variance estimate minus
    another variance estimate is not a variance. AIAG reports zero. `clamp=False`
    returns the raw value so the negative rate can be counted rather than hidden.
    """
    parts, operators, trials = reads.shape
    var = operator_mean_spread(reads) ** 2 - repeatability(reads) ** 2 / (parts * trials)
    if var < 0.0:
        return 0.0 if clamp else -math.sqrt(-var)
    return math.sqrt(var)


def expected_naive(repeat: float = SIGMA_REPEAT,
                   reproduce: float = SIGMA_REPRODUCE,
                   parts: int = PARTS, trials: int = TRIALS) -> float:
    """What the operator-mean spread estimates *in expectation*.

    Added after the first run of this module printed "overstates by -35 %".
    With three operators the naive number has two degrees of freedom and about
    50 % of error, so one study says almost nothing about the direction of the
    bias - the seeded study here happens to land below the truth.

    The bias is exact and worth stating as such:

        E[s^2 of operator means] = reproduce^2 + repeat^2 / (parts * trials)

    That is the whole of claim 3. It is the same lesson Level 1 ended on, one
    level down: the law lives in the expectation, and a single small study
    cannot show it.
    """
    return math.sqrt(reproduce ** 2 + repeat ** 2 / (parts * trials))


def negative_rate(n: int = 4000, seed: int = 77, **kw) -> dict:
    """How often the correction drives the estimate below zero.

    Claim 4 as a frequency. A boundary that is hit one time in ten is a property
    of the design, not an accident, and reporting it as zero means the study
    silently says "no operator effect" when it means "cannot tell".
    """
    rng = np.random.default_rng(seed)
    neg = 0
    naive, corrected = [], []
    for _ in range(n):
        s = study(seed=int(rng.integers(1 << 31)), **kw)
        reads = s["readings"]
        raw = (operator_mean_spread(reads) ** 2
               - repeatability(reads) ** 2 / (reads.shape[0] * reads.shape[2]))
        neg += raw < 0.0
        naive.append(operator_mean_spread(reads))
        corrected.append(reproducibility(reads))
    return {"negative_fraction": neg / n,
            "naive_mean": float(np.mean(naive)),
            "corrected_mean": float(np.mean(corrected))}


def fix_value(target: str, factor: float = 0.5,
              repeat: float = SIGMA_REPEAT,
              reproduce: float = SIGMA_REPRODUCE) -> float:
    """What improving one term by `factor` buys, as a percent of the gauge spread.

    The whole of claim 2 in one function. It is a ratio of quadrature sums, so
    the answer depends only on which term was larger to begin with - which is
    why "fix the gauge" is not advice until you know which half is the problem.
    """
    before = gauge_sigma(repeat, reproduce)
    if target == "repeat":
        after = gauge_sigma(repeat * factor, reproduce)
    elif target == "reproduce":
        after = gauge_sigma(repeat, reproduce * factor)
    else:
        raise ValueError("target must be 'repeat' or 'reproduce'")
    return (1.0 - after / before) * 100.0


def reproducibility_df(operators: int = OPERATORS) -> int:
    """Degrees of freedom on the operator term. Three operators give two."""
    return operators - 1


def relative_error(df: int) -> float:
    """Approximate relative standard error of a standard deviation on `df` df.

    1 / sqrt(2 * df) is the standard large-sample result. At two degrees of
    freedom it is 50 %, which is the number claim 5 exists to say out loud.
    """
    if df < 1:
        raise ValueError("need at least one degree of freedom")
    return 1.0 / math.sqrt(2.0 * df)


# ------------------------------------------------------------ computed facts
STUDY = study()
READS = STUDY["readings"]

GAUGE_EXACT = gauge_sigma()
REPEAT_EST = repeatability(READS)
REPRODUCE_EST = reproducibility(READS)
GAUGE_EST = math.hypot(REPEAT_EST, REPRODUCE_EST)

#: Claim 2: the two fixes, priced.
HALVE_REPEAT_PCT = fix_value("repeat")
HALVE_REPRODUCE_PCT = fix_value("reproduce")
FIX_RATIO = HALVE_REPRODUCE_PCT / HALVE_REPEAT_PCT

#: Claim 3, stated where it belongs: in the expectation, on a gauge whose
#: repeatability dominates. One study of three operators cannot show it.
NOISY = study(seed=SEED + 5, repeat=NOISY_REPEAT, reproduce=NOISY_REPRODUCE)
NOISY_READS = NOISY["readings"]
NOISY_NAIVE = operator_mean_spread(NOISY_READS)
NOISY_CORRECTED = reproducibility(NOISY_READS)
#: The exact bias, and how much of the naive variance is not the operator at all.
NOISY_EXPECTED_NAIVE = expected_naive(NOISY_REPEAT, NOISY_REPRODUCE)
NOISY_INFLATION = (NOISY_EXPECTED_NAIVE / NOISY_REPRODUCE - 1.0) * 100.0
NOISY_BORROWED_PCT = (NOISY_REPEAT ** 2 / (PARTS * TRIALS)
                      / NOISY_EXPECTED_NAIVE ** 2) * 100.0

#: Claim 4: the boundary, as a rate, on the same noisy gauge - plus the second
#: half of the finding. Clamping a negative estimate to zero is not neutral: it
#: is a one-sided truncation, so the reported number runs LOW while the
#: uncorrected one runs high. The study is wrong in both directions at once.
NEG = negative_rate(repeat=NOISY_REPEAT, reproduce=NOISY_REPRODUCE)
NEGATIVE_PCT = NEG["negative_fraction"] * 100.0
NAIVE_MEAN = NEG["naive_mean"]
CORRECTED_MEAN = NEG["corrected_mean"]
NAIVE_OVER_PCT = (NAIVE_MEAN / NOISY_REPRODUCE - 1.0) * 100.0
CLAMPED_UNDER_PCT = (1.0 - CORRECTED_MEAN / NOISY_REPRODUCE) * 100.0

#: Claim 5: how well a standard study can know the operator term at all.
REPRODUCE_DF = reproducibility_df()
REPEAT_DF = PARTS * OPERATORS * (TRIALS - 1)
REPRODUCE_ERR_PCT = relative_error(REPRODUCE_DF) * 100.0
REPEAT_ERR_PCT = relative_error(REPEAT_DF) * 100.0
#: The bias factor of each estimate, because Level 1 established that s is low.
C4_REPRODUCE = c4(OPERATORS)
C4_REPEAT = c4(REPEAT_DF + 1)


def main() -> None:
    print(f"the study: {PARTS} parts x {OPERATORS} operators x {TRIALS} trials")
    print(f"  true repeatability   {SIGMA_REPEAT} um")
    print(f"  true reproducibility {SIGMA_REPRODUCE} um")
    print()
    print("1. the two terms add to the gauge term Level 1 measured")
    print(f"  exact      sqrt({SIGMA_REPEAT}^2 + {SIGMA_REPRODUCE}^2) = {GAUGE_EXACT:.4f}")
    print(f"  estimated  repeat {REPEAT_EST:.4f}  reproduce {REPRODUCE_EST:.4f} "
          f"-> {GAUGE_EST:.4f}")
    print()
    print("2. the two fixes are not interchangeable")
    print(f"  halve repeatability   -> {HALVE_REPEAT_PCT:5.2f} % better")
    print(f"  halve reproducibility -> {HALVE_REPRODUCE_PCT:5.2f} % better  "
          f"({FIX_RATIO:.1f}x)")
    print()
    print("3. the operator-mean spread is not reproducibility")
    print(f"  on a noisy gauge (repeat {NOISY_REPEAT}, reproduce {NOISY_REPRODUCE}):")
    print(f"    exact:  sqrt({NOISY_REPRODUCE}^2 + {NOISY_REPEAT}^2/{PARTS*TRIALS}) "
          f"= {NOISY_EXPECTED_NAIVE:.4f}, so it overstates by {NOISY_INFLATION:.0f} %")
    print(f"    {NOISY_BORROWED_PCT:.0f} % of that variance is repeatability, "
          f"not the operators")
    print(f"    one study of {OPERATORS} operators said {NOISY_NAIVE:.4f} - it has "
          f"{REPRODUCE_DF} df, so it cannot show the direction")
    print(f"    over 4000 studies: naive {NAIVE_MEAN:.3f} vs true "
          f"{NOISY_REPRODUCE} ({NAIVE_OVER_PCT:+.0f} %)")
    print()
    print("4. and the correction can go below zero")
    print(f"  on that gauge it does {NEGATIVE_PCT:.0f} % of the time, reported as zero")
    print(f"  which truncates one side only, so the corrected number runs LOW:")
    print(f"    corrected {CORRECTED_MEAN:.3f} vs true {NOISY_REPRODUCE} "
          f"({-CLAMPED_UNDER_PCT:+.0f} %)")
    print(f"  uncorrected too high, clamped too low, on the same study")
    print()
    print("5. three operators give two degrees of freedom")
    print(f"  reproducibility: {REPRODUCE_DF} df -> about {REPRODUCE_ERR_PCT:.0f} % error")
    print(f"  repeatability:   {REPEAT_DF} df -> about {REPEAT_ERR_PCT:.0f} % error")
    print()
    print("so which half is your problem, and do the operators disagree about")
    print("particular parts? that last question is Level 3.")


if __name__ == "__main__":
    main()
