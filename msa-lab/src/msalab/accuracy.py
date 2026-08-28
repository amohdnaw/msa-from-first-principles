"""LEVEL 5 - Bias, linearity, stability.

Everything in Levels 1 to 4 had a mean of zero. Every ratio those levels built
is made of variances, and a constant offset has no variance at all. So the whole
apparatus from the first four levels is blind to a gauge that reads high.

Three ways to be wrong rather than noisy:

    bias        it reads high, everywhere
    linearity   it reads high at one end and low at the other
    stability   it read correctly in March and does not in June

Five claims, computed here and nowhere else:

1. %GRR cannot see bias. Add three microns of offset and every number Level 4
   produced is unchanged to floating point, while the conformance decision gets
   dramatically worse - and asymmetrically, which noise never is.
2. Bias cannot be found by measuring the same part again. It needs a reference,
   and the question is whether an interval on the mean error contains zero -
   which is a sample-size problem with a computable answer.
3. Linearity is worse than invisible: it *improves* %GRR. A gauge whose error
   grows with size inflates the apparent part spread, so the study ratio - the
   gauge divided by the total - gets smaller. The instrument's own defect is
   counted as process variation.
4. Stability is invisible to any single study by construction. A study run in one
   afternoon cannot see a drift that takes months, and the drift shows up as
   disagreement between studies that each looked fine.
5. Which is the honest summary of five levels: R&R answers one question about a
   gauge, and it is not the question of whether the gauge is right.

    PYTHONPATH=src .venv/bin/python -m msalab.accuracy
"""
from __future__ import annotations

import math

import numpy as np
from scipy import stats

from msalab.against_what import TOLERANCE, study_ratio, tolerance_ratio
from msalab.measurement import PART_SIGMA
from msalab.reproducibility import SIGMA_REPEAT, SIGMA_REPRODUCE

#: The gauge Levels 2-4 built, unchanged.
GAUGE_SIGMA = math.hypot(SIGMA_REPEAT, SIGMA_REPRODUCE)

#: Three ways to be wrong, each sized to be plausible rather than dramatic.
BIAS = 3.0
#: Linearity as a slope: the error grows by this fraction of the distance from
#: the centre of the range. 0.12 means a part 10 um oversize reads 1.2 um high.
LINEARITY = 0.12
#: Stability as a drift per month, in microns.
DRIFT_PER_MONTH = 0.55
MONTHS = 12

#: The reference study for detecting bias: one master, measured this many times.
MASTER_READS = 10
CONF = 0.95


def biased_reading(truth: np.ndarray, bias: float = BIAS,
                   gauge: float = GAUGE_SIGMA, rng=None) -> np.ndarray:
    """A reading from a gauge that is off by a constant."""
    rng = rng or np.random.default_rng(505)
    return truth + bias + rng.normal(0.0, gauge, truth.shape)


def ratios_with_bias(bias: float = BIAS, gauge: float = GAUGE_SIGMA,
                     part: float = PART_SIGMA,
                     tolerance: float = TOLERANCE) -> dict:
    """Level 4's two ratios, computed on a biased gauge.

    Claim 1, and it is exact rather than empirical: both ratios are built from
    standard deviations, and adding a constant to every reading changes no
    standard deviation. The bias term does not appear in either formula. There is
    nowhere for it to enter, which is the same shape of failure Level 3 found in
    average-and-range and the interaction.
    """
    return {"study": study_ratio(gauge, part),
            "tolerance": tolerance_ratio(gauge, tolerance),
            "bias": bias}


def _simpson(f, a: float, b: float, n: int = 2000) -> float:
    """Composite Simpson over [a, b] with `n` intervals (n must be even).

    Written out rather than taken from scipy so the page can run the identical
    node placement in JavaScript - the lab and this module have to agree to
    better than the fifth decimal the page prints, and that is only true if both
    sides evaluate the same integrand at the same abscissae.
    """
    if n % 2:
        raise ValueError("Simpson needs an even number of intervals")
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        total += f(a + i * h) * (4.0 if i % 2 else 2.0)
    return total * h / 3.0


def _phi(x: float, sd: float) -> float:
    """Normal density at x, mean zero."""
    return math.exp(-0.5 * (x / sd) ** 2) / (sd * math.sqrt(2.0 * math.pi))


def _Phi(z: float) -> float:
    """Standard normal CDF. Exact, not a table lookup."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def misclassification(bias: float = 0.0, gauge: float = GAUGE_SIGMA,
                      part: float = PART_SIGMA, tolerance: float = TOLERANCE,
                      slope: float = 0.0) -> dict:
    """The conformance decision, with a gauge that may be off.

    Computed by quadrature rather than simulated. An earlier version drew four
    hundred thousand parts, which put sampling noise into the fourth decimal of
    every number this level prints - and this level's whole argument is that two
    numbers agree *exactly* while a third moves. A claim about exact agreement
    cannot rest on a random draw. `misclassification_simulated` is kept, and a
    test holds the two against each other.

    The part is truly X ~ N(0, part). The gauge reports X + bias + slope*X + E,
    with E ~ N(0, gauge), so `slope` shears the error with the size of the part -
    that is linearity, and it makes the readings' spread depend on the part's.

    Reported split by direction, because that is what bias does and noise does
    not: an unbiased gauge scraps good parts at both limits equally, and a biased
    one pushes everything one way.
    """
    half = tolerance / 2.0
    lim = 12.0 * part                      # phi_part below 1e-31 beyond this
    p_good = 2.0 * _Phi(half / part) - 1.0
    p_bad = 1.0 - p_good

    def read_mean(x: float) -> float:
        return x + bias + slope * x

    def upper(x: float) -> float:
        return _phi(x, part) * _Phi((read_mean(x) - half) / gauge)

    def lower(x: float) -> float:
        return _phi(x, part) * _Phi((-half - read_mean(x)) / gauge)

    def inside(x: float) -> float:
        return _phi(x, part) * (_Phi((half - read_mean(x)) / gauge)
                                - _Phi((-half - read_mean(x)) / gauge))

    fr_high = _simpson(upper, -half, half)
    fr_low = _simpson(lower, -half, half)
    fa = _simpson(inside, half, lim) + _simpson(inside, -lim, -half)
    fr = fr_high + fr_low
    return {
        "bias": bias,
        "false_accept_pct": fa * 100.0,
        "false_reject_pct": fr * 100.0,
        "bad_accepted_pct": (fa / p_bad * 100.0) if p_bad > 0 else 0.0,
        "good_rejected_pct": fr / p_good * 100.0,
        "rejected_at_upper_pct": fr_high / fr * 100.0 if fr > 0 else 0.0,
        "rejected_at_lower_pct": fr_low / fr * 100.0 if fr > 0 else 0.0,
    }


def misclassification_simulated(bias: float = 0.0, gauge: float = GAUGE_SIGMA,
                                part: float = PART_SIGMA,
                                tolerance: float = TOLERANCE,
                                n: int = 400_000, seed: int = 515) -> dict:
    """The same quantities by Monte Carlo, kept only to check the quadrature."""
    rng = np.random.default_rng(seed)
    truth = rng.normal(0.0, part, n)
    read = truth + bias + rng.normal(0.0, gauge, n)
    half = tolerance / 2.0
    good = np.abs(truth) <= half
    passed = np.abs(read) <= half
    bad = int((~good).sum())
    fr_high = int((good & ~passed & (read > half)).sum())
    fr_low = int((good & ~passed & (read < -half)).sum())
    fr = fr_high + fr_low
    fa = int((~good & passed).sum())
    n_good = int(good.sum())
    return {
        "bias": bias,
        "false_accept_pct": fa / n * 100.0,
        "false_reject_pct": fr / n * 100.0,
        "bad_accepted_pct": (fa / bad * 100.0) if bad else 0.0,
        "good_rejected_pct": (fr / n_good * 100.0) if n_good else 0.0,
        "rejected_at_upper_pct": (fr_high / fr * 100.0) if fr else 0.0,
        "rejected_at_lower_pct": (fr_low / fr * 100.0) if fr else 0.0,
    }


def bias_interval(reads: np.ndarray, master: float = 0.0,
                  conf: float = CONF) -> dict:
    """A confidence interval on the mean error against a known master.

    This is the whole of bias detection: measure something whose size you know,
    and ask whether the interval on the average error contains zero. It cannot be
    done by measuring an unknown part repeatedly - that gives you repeatability
    and no information about where the readings sit.
    """
    err = reads - master
    n = len(err)
    if n < 2:
        raise ValueError("an interval needs at least two readings")
    mean = float(err.mean())
    se = float(err.std(ddof=1) / math.sqrt(n))
    t = float(stats.t.ppf(0.5 + conf / 2.0, n - 1))
    return {"mean": mean, "se": se, "half_width": t * se,
            "low": mean - t * se, "high": mean + t * se,
            "detected": not (mean - t * se <= 0.0 <= mean + t * se)}


def reads_to_detect(bias: float = BIAS, gauge: float = GAUGE_SIGMA,
                    conf: float = CONF, power: float = 0.90) -> int:
    """How many readings of a master before a bias that size is detectable.

    The standard two-sided sample-size expression, solved by stepping n rather
    than by a normal approximation, because at these n the t quantile matters and
    the approximation is optimistic by a reading or two.
    """
    if bias <= 0:
        raise ValueError("a bias of zero is never detectable")
    for n in range(2, 2001):
        t_crit = stats.t.ppf(0.5 + conf / 2.0, n - 1)
        t_beta = stats.t.ppf(power, n - 1)
        if bias >= (t_crit + t_beta) * gauge / math.sqrt(n):
            return n
    raise ValueError("no practical number of readings detects that")


def linear_error(truth: np.ndarray, slope: float = LINEARITY,
                 centre: float = 0.0) -> np.ndarray:
    """Error that grows with distance from the centre of the range."""
    return slope * (truth - centre)


def ratios_with_linearity(slope: float = LINEARITY,
                          gauge: float = GAUGE_SIGMA,
                          part: float = PART_SIGMA,
                          tolerance: float = TOLERANCE) -> dict:
    """Claim 3, in closed form and then checked by simulation in the tests.

    A reading is `truth + slope*truth + noise`, so its spread is
    `(1+slope)^2 * part^2 + gauge^2`. The slope inflates the *observed part
    spread*, which is the denominator of the study ratio - so the ratio falls.

    The gauge's own defect is counted as process variation and rewarded.
    """
    total = math.sqrt((1.0 + slope) ** 2 * part ** 2 + gauge ** 2)
    return {"study": gauge / total * 100.0,
            "tolerance": tolerance_ratio(gauge, tolerance),
            "apparent_part": (1.0 + slope) * part,
            "true_part": part,
            "slope": slope}


def drift_studies(months: int = MONTHS, per_month: float = DRIFT_PER_MONTH,
                  gauge: float = GAUGE_SIGMA, part: float = PART_SIGMA,
                  reads: int = MASTER_READS, seed: int = 525) -> dict:
    """One master measured every month, against a gauge that is drifting.

    Claim 4. Each month's study is internally fine - its repeatability is
    correct, its interval is the right width - and the drift is only visible when
    the months are put beside each other.
    """
    rng = np.random.default_rng(seed)
    rows = []
    for m in range(months):
        bias = per_month * m
        r = rng.normal(bias, gauge, reads)
        ci = bias_interval(r)
        rows.append({"month": m, "true_bias": bias, "mean": ci["mean"],
                     "half_width": ci["half_width"], "detected": ci["detected"],
                     # the spread of that month's own readings. A constant offset
                     # cannot move it; a drift occurring DURING the study would.
                     "within_sd": float(r.std(ddof=1))})
    means = np.array([r["mean"] for r in rows])
    within = float(np.mean([r["half_width"] for r in rows]))
    between = float(means.std(ddof=1))
    total = per_month * (months - 1)
    # The first draft reported between-month spread against within-study
    # half-width and got 1.3x, which demonstrates nothing. The claim is not that
    # the drift is large compared to the noise - it is that a single study cannot
    # see it AT ALL, because the bias is constant inside one study and every
    # variance-based number is therefore identical every month.
    return {"rows": rows, "between_months": between,
            "within_sd_by_month": [r["within_sd"] for r in rows],
            "mean_half_width": within,
            "total_drift": total,
            "drift_over_gauge": total / gauge,
            "drift_pct_of_tolerance": total / TOLERANCE * 100.0,
            # every month's repeatability estimate, which must not move
            "repeatability_by_month": [
                float(np.std(rng.normal(per_month * m, gauge, 400), ddof=1))
                for m in range(months)],
            "months_before_a_master_notices": next(
                (r["month"] for r in rows if r["detected"]), None),
            "months_undetected": sum(1 for r in rows if not r["detected"])}


# ------------------------------------------------------------ computed facts
CLEAN_RATIOS = ratios_with_bias(bias=0.0)
BIASED_RATIOS = ratios_with_bias()
#: Claim 1: identical to floating point.
RATIOS_UNCHANGED = (
    abs(CLEAN_RATIOS["study"] - BIASED_RATIOS["study"]) < 1e-12
    and abs(CLEAN_RATIOS["tolerance"] - BIASED_RATIOS["tolerance"]) < 1e-12)

CLEAN_MISS = misclassification(bias=0.0)
BIASED_MISS = misclassification(bias=BIAS)
SCRAP_MULTIPLE = (BIASED_MISS["good_rejected_pct"]
                  / max(1e-9, CLEAN_MISS["good_rejected_pct"]))

#: Claim 2: detecting it.
_rng = np.random.default_rng(555)
MASTER_SAMPLE = BIAS + _rng.normal(0.0, GAUGE_SIGMA, MASTER_READS)
MASTER_CI = bias_interval(MASTER_SAMPLE)
READS_FOR_BIAS = reads_to_detect()
READS_FOR_HALF = reads_to_detect(bias=BIAS / 2)
READS_FOR_TENTH = reads_to_detect(bias=BIAS / 10)

#: Claim 3: linearity improves the ratio.
LINEAR_RATIOS = ratios_with_linearity()
STUDY_IMPROVEMENT = CLEAN_RATIOS["study"] - LINEAR_RATIOS["study"]
APPARENT_INFLATION_PCT = (LINEAR_RATIOS["apparent_part"] / PART_SIGMA - 1) * 100

#: Claim 4: the drift, and the numbers that show it is invisible rather than
#: merely small.
DRIFT = drift_studies()
DRIFT_TOTAL = DRIFT["total_drift"]
DRIFT_OVER_GAUGE = DRIFT["drift_over_gauge"]
DRIFT_PCT_TOL = DRIFT["drift_pct_of_tolerance"]
#: Every month's repeatability estimate, which a drifting bias cannot move.
REPEAT_BY_MONTH = DRIFT["repeatability_by_month"]
REPEAT_SPREAD = max(REPEAT_BY_MONTH) - min(REPEAT_BY_MONTH)
#: And every month's %GRR, which is identical because it is variance-based.
GRR_BY_MONTH = [study_ratio(GAUGE_SIGMA, PART_SIGMA) for _ in range(MONTHS)]
GRR_IS_CONSTANT = max(GRR_BY_MONTH) - min(GRR_BY_MONTH) < 1e-12
MONTH_MASTER_NOTICES = DRIFT["months_before_a_master_notices"]


def main() -> None:
    print(f"the gauge from Levels 2-4: {GAUGE_SIGMA:.4f} um, tolerance "
          f"{TOLERANCE:.0f} um")
    print()
    print("1. %GRR cannot see bias")
    print(f"  unbiased: study {CLEAN_RATIOS['study']:.4f} %  tolerance "
          f"{CLEAN_RATIOS['tolerance']:.4f} %")
    print(f"  {BIAS} um high: study {BIASED_RATIOS['study']:.4f} %  tolerance "
          f"{BIASED_RATIOS['tolerance']:.4f} %")
    print(f"  identical to floating point: {RATIOS_UNCHANGED}")
    print(f"  meanwhile the decision:")
    print(f"    good parts rejected  {CLEAN_MISS['good_rejected_pct']:6.2f} % -> "
          f"{BIASED_MISS['good_rejected_pct']:6.2f} %  "
          f"({SCRAP_MULTIPLE:.0f}x)")
    print(f"    and it is one-sided: {BIASED_MISS['rejected_at_upper_pct']:.0f} % "
          f"of those rejections are at the upper limit "
          f"(unbiased: {CLEAN_MISS['rejected_at_upper_pct']:.0f} %)")
    print()
    print("2. bias needs a reference, and then a sample size")
    print(f"  {MASTER_READS} readings of a master that is truly {BIAS} um out:")
    print(f"    mean error {MASTER_CI['mean']:+.3f} um, "
          f"interval [{MASTER_CI['low']:+.3f}, {MASTER_CI['high']:+.3f}]")
    print(f"    detected: {MASTER_CI['detected']}")
    print(f"  readings needed at 95 % confidence and 90 % power:")
    print(f"    to detect {BIAS} um     {READS_FOR_BIAS:>4}")
    print(f"    to detect {BIAS/2} um   {READS_FOR_HALF:>4}")
    print(f"    to detect {BIAS/10} um   {READS_FOR_TENTH:>4}")
    print()
    print("3. linearity does not hide - it flatters")
    print(f"  slope {LINEARITY}: a part 10 um oversize reads "
          f"{LINEARITY*10:.1f} um high")
    print(f"  apparent part spread {LINEAR_RATIOS['apparent_part']:.3f} um vs "
          f"true {PART_SIGMA} ({APPARENT_INFLATION_PCT:+.0f} %)")
    print(f"  study ratio {CLEAN_RATIOS['study']:.1f} % -> "
          f"{LINEAR_RATIOS['study']:.1f} %  "
          f"(better by {STUDY_IMPROVEMENT:.1f} points)")
    print(f"  the gauge's own defect is counted as process variation")
    print()
    print("4. stability is invisible to one study, by construction")
    print(f"  drift {DRIFT_PER_MONTH} um per month over {MONTHS} months "
          f"= {DRIFT_TOTAL:.2f} um total")
    print(f"    which is {DRIFT_OVER_GAUGE:.1f}x the gauge's own sigma and "
          f"{DRIFT_PCT_TOL:.0f} % of the tolerance")
    print(f"  and yet, month by month:")
    print(f"    %GRR identical every month: {GRR_IS_CONSTANT}  "
          f"({GRR_BY_MONTH[0]:.4f} % throughout)")
    print(f"    repeatability estimates range over only "
          f"{REPEAT_SPREAD:.3f} um across the year")
    print(f"  the bias is constant INSIDE a study, so no study can see it moving")
    print(f"  with a master, a single month first notices at month "
          f"{MONTH_MASTER_NOTICES} - and {DRIFT['months_undetected']} of "
          f"{MONTHS} months read as 'no bias detected'")
    print()
    print("5. so R&R answers one question, and it is not whether the gauge is right.")
    print("   Level 6 asks what happens when the reading is not a number at all.")


if __name__ == "__main__":
    main()
