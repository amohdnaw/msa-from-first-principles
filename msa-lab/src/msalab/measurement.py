"""LEVEL 1 - Measurement as a process.

The whole subject rests on one sentence: **a gauge is not a window onto the
truth, it is a process, and it has variation.** Everything after this level is
arithmetic about that variation - splitting it, naming its parts, deciding
whether it is small enough. This level earns the sentence.

Five claims, each computed here and nowhere else:

1. The spread you observe is not the spread of the parts. Measure the same
   parts with a noisier gauge and the histogram widens while the parts sit
   untouched on the bench.
2. A single part, measured repeatedly, **is a distribution**. That is the
   claim: not that the readings are unreliable, but that they have a shape
   with a mean and a spread of its own, the way any process does.
3. Variances add; standard deviations do not. So measurement error is cheap at
   first and expensive later - a gauge at 30 % of the part spread widens what
   you see by 4.4 %, and one at 100 % widens it by 41 %.
4. Averaging repeats divides the *measurement* variance by the number of
   repeats and leaves the part variance exactly where it was. There is a floor,
   and no amount of measuring gets under it.
5. Therefore "how good is this gauge" has no absolute answer. It is a ratio,
   and the next level asks what the denominator should be.

Every number the page, the act and the figure sheets speak is imported from
here. Nothing is typed twice.

    PYTHONPATH=src .venv/bin/python -m msalab.measurement
"""
from __future__ import annotations

import math

import numpy as np

# ---------------------------------------------------------------- the instance
# A bench micrometer measuring machined bores, in microns from nominal. Real
# units matter: "0.3 sigma of noise" is an abstraction, "1.4 microns on a part
# spread of 4.7" is a thing an engineer can picture and disagree with.
SEED = 11
PARTS = 40
REPEATS = 3

#: True part-to-part standard deviation, microns. The parts genuinely differ by
#: this much; no gauge is involved.
PART_SIGMA = 4.7
#: True measurement standard deviation of the gauge, microns. One operator, one
#: part, repeated readings scatter by this much. Level 2 splits this term.
GAUGE_SIGMA = 1.4
#: The gauge has no bias in this level. Bias is Level 5, and mixing it in here
#: would let a reader attribute the widening to the wrong cause.
GAUGE_BIAS = 0.0


def observed_sigma(part_sigma: float = PART_SIGMA,
                   gauge_sigma: float = GAUGE_SIGMA) -> float:
    """The standard deviation of what the gauge reports.

    Independent variation adds in quadrature. This one line is the level:
    the reading is the part plus the gauge's own error, and the spread of a sum
    of independent terms is the root of the sum of their variances.
    """
    return math.hypot(part_sigma, gauge_sigma)


def inflation(ratio: float) -> float:
    """How much wider the observed spread is than the true part spread.

    `ratio` is gauge sigma as a fraction of part sigma. Returns the multiplier
    on the observed standard deviation, so 1.044 means "4.4 % wider".
    """
    return math.sqrt(1.0 + ratio * ratio)


def ratio_for_inflation(target: float) -> float:
    """Invert `inflation`: what gauge ratio widens the spread by `target`.

    The inverse is the more useful direction. Asking "how bad may my gauge be
    before the histogram lies to me by ten percent" has an exact answer, and it
    is a much larger number than people expect.
    """
    if target < 1.0:
        raise ValueError("a gauge cannot narrow the observed spread")
    return math.sqrt(target * target - 1.0)


def study(seed: int = SEED, parts: int = PARTS, repeats: int = REPEATS,
          part_sigma: float = PART_SIGMA, gauge_sigma: float = GAUGE_SIGMA,
          bias: float = GAUGE_BIAS) -> dict:
    """One simulated study: `parts` bores, each read `repeats` times.

    Returns the truth alongside the readings, which is the point - on a real
    bench the true part value is unknowable, and the only reason this level can
    show what the gauge did is that here it is known.
    """
    rng = np.random.default_rng(seed)
    truth = rng.normal(0.0, part_sigma, parts)
    error = rng.normal(bias, gauge_sigma, (parts, repeats))
    readings = truth[:, None] + error
    return {
        "truth": truth,
        "readings": readings,
        "first_pass": readings[:, 0],
        "part_means": readings.mean(axis=1),
        # ddof=1: these are samples, and the level's own claim is that every
        # number here is an estimate
        "sd_truth": float(truth.std(ddof=1)),
        "sd_observed": float(readings[:, 0].std(ddof=1)),
        "sd_of_means": float(readings.mean(axis=1).std(ddof=1)),
        # within-part scatter, pooled across parts: the gauge talking to itself
        "sd_within": float(np.sqrt(
            ((readings - readings.mean(axis=1, keepdims=True)) ** 2).sum()
            / (parts * (repeats - 1)))),
    }


def averaging_floor(m: int, part_sigma: float = PART_SIGMA,
                    gauge_sigma: float = GAUGE_SIGMA) -> float:
    """Observed sigma when every part is measured `m` times and averaged.

    The measurement variance divides by `m`; the part variance does not move at
    all. So this decreases towards `part_sigma` and never below it, which is the
    floor claim - and the reason %GRR is a ratio rather than a quantity.
    """
    if m < 1:
        raise ValueError("m must be at least 1")
    return math.sqrt(part_sigma ** 2 + gauge_sigma ** 2 / m)


def c4(n: int) -> float:
    """The bias factor of the sample standard deviation: E[s] = c4(n) * sigma.

    Added because the replication above appeared to be 0.6 % low against the
    exact law, and 0.6 % across four thousand studies is not simulation error.
    It is not error at all: `s` is a biased estimator of sigma, low by exactly
    this factor, and the gap closes only as n grows.

    Deriving it rather than quoting a table keeps this level's own rule, and it
    lets the replication test be exact instead of merely close. The AIAG
    d2 constants at Level 3 are the same kind of animal.
    """
    if n < 2:
        raise ValueError("c4 needs at least two observations")
    return math.sqrt(2.0 / (n - 1)) * math.exp(
        math.lgamma(n / 2.0) - math.lgamma((n - 1) / 2.0))


def replicate(n_studies: int = 4000, seed: int = 500,
              part_sigma: float = PART_SIGMA,
              gauge_sigma: float = GAUGE_SIGMA) -> dict:
    """Run the same study `n_studies` times and average what it estimated.

    This function exists because of a defect found by reading the output: at 40
    parts the sampling error of a standard deviation is about 11 %, and the
    inflation this level is about is 4.3 %. So one study cannot see it, and the
    seeded study here happens to report an observed spread *narrower* than the
    true part spread. Seeding around that would be a lie about what a study can
    do.

    Averaged over many studies the law reappears exactly, which is the honest
    form of the claim: the widening is a property of the process, not something
    a single sample displays. It also puts a number on why nobody estimates gauge
    error by comparing histograms.
    """
    rng = np.random.default_rng(seed)
    obs, tru, wit = [], [], []
    for _ in range(n_studies):
        truth = rng.normal(0.0, part_sigma, PARTS)
        err = rng.normal(0.0, gauge_sigma, (PARTS, REPEATS))
        reads = truth[:, None] + err
        obs.append(reads[:, 0].std(ddof=1))
        tru.append(truth.std(ddof=1))
        wit.append(np.sqrt(((reads - reads.mean(axis=1, keepdims=True)) ** 2).sum()
                           / (PARTS * (REPEATS - 1))))
    obs, tru, wit = np.array(obs), np.array(tru), np.array(wit)
    return {
        "observed_mean": float(obs.mean()), "observed_sd": float(obs.std(ddof=1)),
        "truth_mean": float(tru.mean()), "truth_sd": float(tru.std(ddof=1)),
        "within_mean": float(wit.mean()), "within_sd": float(wit.std(ddof=1)),
        # how often a single study reports an observed spread NARROWER than the
        # true part spread, which the law says is impossible in expectation
        "wrong_direction": float((obs < part_sigma).mean()),
    }


def population(n: int = 6000, seed: int = 77,
               part_sigma: float = PART_SIGMA,
               gauge_sigma: float = GAUGE_SIGMA) -> dict:
    """A population large enough to *draw* the law rather than estimate it.

    The figure that shows the histogram widening must not be a 40-part study,
    because at 40 parts the two histograms differ by less than their own
    sampling noise and the picture would be claiming something it cannot show.
    Six thousand parts draws the distributions themselves.
    """
    rng = np.random.default_rng(seed)
    truth = rng.normal(0.0, part_sigma, n)
    return {"truth": truth,
            "observed": truth + rng.normal(0.0, gauge_sigma, n),
            "n": n}


def repeats_for_fraction(fraction: float, part_sigma: float = PART_SIGMA,
                         gauge_sigma: float = GAUGE_SIGMA) -> int:
    """Smallest `m` whose averaged inflation is within `fraction` of the floor.

    Answers "how many repeats until measurement stops mattering", and the answer
    is unpleasant because the improvement goes as 1/m inside a square root.
    """
    target = part_sigma * (1.0 + fraction)
    m = 1
    while averaging_floor(m, part_sigma, gauge_sigma) > target:
        m += 1
        if m > 10_000:
            raise ValueError("no practical number of repeats reaches that")
    return m


# ------------------------------------------------------------- computed facts
# Everything below is what the page, the act and the sheets are allowed to say.

STUDY = study()

#: Exact observed sigma from the variance law, and what one study estimated.
OBSERVED_EXACT = observed_sigma()
OBSERVED_SIM = STUDY["sd_observed"]

#: The honest correction. One study of 40 parts cannot see a 4.3 % widening,
#: because the sampling error of a standard deviation at n = 40 is around 11 %.
#: This seeded study reports an observed spread NARROWER than the true part
#: spread, which the law forbids in expectation and sampling permits often.
REPL = replicate()
#: Averaged over 4000 studies the law reappears to three decimals.
REPL_OBSERVED = REPL["observed_mean"]
REPL_TRUTH = REPL["truth_mean"]
REPL_WITHIN = REPL["within_mean"]
#: How often one study points the wrong way. This number is the reason nobody
#: estimates gauge error by comparing histograms.
WRONG_DIRECTION_PCT = REPL["wrong_direction"] * 100.0
#: The sampling error of the two estimates, side by side. The within-part
#: estimate is the trustworthy one: it has PARTS x (REPEATS - 1) degrees of
#: freedom on the gauge alone and does not depend on the part spread at all.
SE_OBSERVED_PCT = REPL["observed_sd"] / REPL["observed_mean"] * 100.0
SE_WITHIN_PCT = REPL["within_sd"] / REPL["within_mean"] * 100.0
WITHIN_DF = PARTS * (REPEATS - 1)

#: What `s` actually estimates. The replication has to be checked against these,
#: not against sigma, or the check is loose by more than the effect it guards.
C4_PARTS = c4(PARTS)
C4_WITHIN = c4(WITHIN_DF + 1)
EXPECTED_OBSERVED = OBSERVED_EXACT * C4_PARTS
EXPECTED_TRUTH = PART_SIGMA * C4_PARTS
EXPECTED_WITHIN = GAUGE_SIGMA * C4_WITHIN
#: How much of the apparent shortfall was bias rather than noise.
C4_SHORTFALL_PCT = (1.0 - C4_PARTS) * 100.0

#: A population large enough to draw the law instead of estimating it.
POP = population()

#: The gauge as a fraction of the part spread, and what that costs.
GAUGE_RATIO = GAUGE_SIGMA / PART_SIGMA
INFLATION_HERE = inflation(GAUGE_RATIO)
WIDENING_PCT = (INFLATION_HERE - 1.0) * 100.0

#: The quadrature table the page prints. Ratio -> percent wider.
RATIO_GRID = (0.1, 0.2, 0.3, 0.5, 0.75, 1.0)
INFLATION_TABLE = tuple((r, (inflation(r) - 1.0) * 100.0) for r in RATIO_GRID)

#: The inverse, which is the counter-intuitive one: a gauge may be nearly half
#: the part spread before the histogram is 10 % too wide.
RATIO_FOR_10PCT = ratio_for_inflation(1.10)
RATIO_FOR_1PCT = ratio_for_inflation(1.01)

#: Averaging. The floor is PART_SIGMA and m buys less and less.
FLOOR = PART_SIGMA
AVERAGE_GRID = (1, 2, 3, 5, 10, 25)
AVERAGE_TABLE = tuple(
    (m, averaging_floor(m), (averaging_floor(m) / FLOOR - 1.0) * 100.0)
    for m in AVERAGE_GRID)
REPEATS_FOR_1PCT = repeats_for_fraction(0.01)

#: One part, measured many times, is a distribution with a shape of its own.
ONE_PART_READS = 200
_rng = np.random.default_rng(SEED + 1)
ONE_PART_TRUE = float(STUDY["truth"][0])
ONE_PART_SAMPLE = ONE_PART_TRUE + _rng.normal(GAUGE_BIAS, GAUGE_SIGMA, ONE_PART_READS)
ONE_PART_MEAN = float(ONE_PART_SAMPLE.mean())
ONE_PART_SD = float(ONE_PART_SAMPLE.std(ddof=1))
#: The full width a reader would actually see across 200 readings of one part
#: that has exactly one true size.
ONE_PART_RANGE = float(ONE_PART_SAMPLE.max() - ONE_PART_SAMPLE.min())


def main() -> None:
    print("the instance: bench micrometer, machined bores, microns from nominal")
    print(f"  {PARTS} parts x {REPEATS} repeats, seed {SEED}")
    print(f"  true part sigma {PART_SIGMA} um, true gauge sigma {GAUGE_SIGMA} um")
    print()
    print("1. one part is a distribution")
    print(f"  part 1 true size {ONE_PART_TRUE:+.2f} um, {ONE_PART_READS} readings")
    print(f"  mean {ONE_PART_MEAN:+.3f}  sd {ONE_PART_SD:.3f}  "
          f"full range {ONE_PART_RANGE:.2f} um")
    print(f"  one true size, {ONE_PART_RANGE:.1f} um of spread on the screen")
    print()
    print("2. the observed spread is not the part spread")
    print(f"  exact      sqrt({PART_SIGMA}^2 + {GAUGE_SIGMA}^2) = {OBSERVED_EXACT:.4f}")
    print(f"  one study  first pass sd              = {OBSERVED_SIM:.4f}  <- narrower!")
    print(f"  one study  sd of the parts themselves = {STUDY['sd_truth']:.4f}")
    print(f"  one study  the gauge on its own       = {STUDY['sd_within']:.4f}")
    print("  one study of 40 parts cannot see a 4.3 % widening:")
    print(f"    sampling error of an observed sd  = {SE_OBSERVED_PCT:.1f} %")
    print(f"    so it points the wrong way          {WRONG_DIRECTION_PCT:.0f} % of the time")
    print("  averaged over 4000 studies, against what s actually estimates:")
    print(f"    observed {REPL_OBSERVED:.4f} vs c4*exact {EXPECTED_OBSERVED:.4f} "
          f"(sigma itself is {OBSERVED_EXACT:.4f})")
    print(f"    parts    {REPL_TRUTH:.4f} vs c4*true  {EXPECTED_TRUTH:.4f}")
    print(f"    gauge    {REPL_WITHIN:.4f} vs c4*true  {EXPECTED_WITHIN:.4f}")
    print(f"    c4({PARTS}) = {C4_PARTS:.5f}, so s runs {C4_SHORTFALL_PCT:.2f} % low "
          f"by construction, not by chance")
    print(f"  and the gauge estimate is the trustworthy one: {SE_WITHIN_PCT:.1f} % error "
          f"on {WITHIN_DF} degrees of freedom, independent of the part spread")
    print()
    print("3. variances add, so error is cheap then brutal")
    for r, pct in INFLATION_TABLE:
        print(f"  gauge at {r*100:5.1f} % of part sigma -> {pct:6.2f} % wider")
    print(f"  a gauge may reach {RATIO_FOR_10PCT*100:.1f} % of the part spread "
          f"before the histogram is 10 % too wide")
    print(f"  but only {RATIO_FOR_1PCT*100:.1f} % to stay inside 1 %")
    print()
    print("4. averaging has a floor")
    for m, sd, pct in AVERAGE_TABLE:
        print(f"  m = {m:>2} repeats -> observed {sd:.4f} um "
              f"({pct:5.2f} % above the {FLOOR} um floor)")
    print(f"  reaching 1 % above the floor needs m = {REPEATS_FOR_1PCT}")
    print()
    print("5. so the question is a ratio, and Level 2 asks whose spread it is")


if __name__ == "__main__":
    main()
