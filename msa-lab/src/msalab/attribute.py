"""LEVEL 6 - Attribute agreement.

Five levels of arithmetic, all of it dividing one spread by another. Now the
gauge says "pass" and nothing else. There is no reading to subtract, no variance
to decompose, no sigma to put in a denominator.

The three questions survive the loss of the number:

    repeatability    does one appraiser agree with himself, twice
    reproducibility  do two appraisers agree with each other
    bias             does either of them agree with the truth

And the answers have to be built out of counts.

Six claims, computed here and nowhere else:

1. Percent agreement is worthless on a good process. An appraiser who passes
   every part without looking scores as high as the base rate - 99 % agreement
   with himself, and the same with a colleague who also passes everything.
   Nothing about the gauge enters the number.
2. Kappa removes the chance agreement, and brings its own trap. Two tables with
   *identical* percent agreement give wildly different kappa depending only on
   how skewed the stream is, so a good process depresses kappa on its own.
3. An attribute gauge is a variable gauge with the numbers thrown away. Behind
   every go/no-go there is a real dimension and real gauge noise, and the
   misclassification rate follows from Level 5's sigma. Kappa is not a free
   parameter - it is derived.
4. Which means the disagreement lives in a narrow band. Parts within two gauge
   sigmas of the limit are two percent of production and seven eighths of every
   mistake ever made; within three sigmas, six percent of production and
   ninety-nine percent of the mistakes. The band's width is set by the
   instrument, so 'appraiser error' is mostly a property of the gauge.
5. The two errors are not symmetric and cannot be traded freely: shifting the
   decision inward buys fewer escapes at a steep price in false rejects, and the
   exchange rate depends on where the process sits.
6. And a count needs far more parts than a measurement did. Level 2 settled
   repeatability with ten parts; bounding a miss rate to plus or minus two
   points needs hundreds of known-bad ones.

    PYTHONPATH=src .venv/bin/python -m msalab.attribute
"""
from __future__ import annotations

import math

import numpy as np

from msalab.accuracy import GAUGE_SIGMA, _Phi, _phi, _simpson
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA

#: Half the tolerance: the go/no-go limit, either side of nominal.
HALF = TOLERANCE / 2.0

#: The appraiser's own decision limit, which need not be the drawing's. Shifting
#: it inward is the standard response to escapes, and claim 5 prices it.
GUARD_BAND = 0.0

#: How many known-bad parts a study has, and the miss rate it wants to bound.
MISS_RATE_TARGET = 0.05
MISS_HALF_WIDTH = 0.02

#: For claim 4: the band around the limit, measured in gauge sigmas.
BAND_SIGMAS = 1.0


# --------------------------------------------------------------- the machinery
def _p_good(part: float = PART_SIGMA, half: float = HALF) -> float:
    """The share of parts genuinely inside tolerance."""
    return 2.0 * _Phi(half / part) - 1.0


def _pass_prob(x: float, gauge: float = GAUGE_SIGMA, half: float = HALF,
               guard: float = GUARD_BAND) -> float:
    """Probability one appraisal of a part truly at `x` comes back 'pass'.

    The appraiser has no number - but the instrument he is holding does, and it
    is the Level 5 gauge. He passes when the reading lands inside his own limit.
    """
    lim = half - guard
    return _Phi((lim - x) / gauge) - _Phi((-lim - x) / gauge)


def cross_table(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
                half: float = HALF, guard: float = GUARD_BAND) -> dict:
    """The appraiser against the truth, as the four counts AIAG asks for.

    Integrated rather than simulated, for the same reason Level 5 switched: the
    claims here are about exact relations between these rates and the gauge that
    produced them.
    """
    lim = 12.0 * part

    def good_pass(x):
        return _phi(x, part) * _pass_prob(x, gauge, half, guard)

    def good_fail(x):
        return _phi(x, part) * (1.0 - _pass_prob(x, gauge, half, guard))

    def bad_pass(x):
        return _phi(x, part) * _pass_prob(x, gauge, half, guard)

    def bad_fail(x):
        return _phi(x, part) * (1.0 - _pass_prob(x, gauge, half, guard))

    gp = _simpson(good_pass, -half, half)
    gf = _simpson(good_fail, -half, half)
    bp = _simpson(bad_pass, half, lim) + _simpson(bad_pass, -lim, -half)
    bf = _simpson(bad_fail, half, lim) + _simpson(bad_fail, -lim, -half)
    good, bad = gp + gf, bp + bf
    return {
        "good_pass": gp, "good_fail": gf, "bad_pass": bp, "bad_fail": bf,
        "good": good, "bad": bad,
        # AIAG's three, named as the standard names them
        "effectiveness": gp + bf,
        "miss_rate": bp / bad if bad else 0.0,
        "false_alarm_rate": gf / good if good else 0.0,
    }


def kappa_from_table(n11: float, n10: float, n01: float, n00: float) -> dict:
    """Cohen's kappa for a 2x2 agreement table, with its pieces exposed.

    `n11` both said pass, `n00` both said fail, the others disagree. The pieces
    are returned because the whole of claim 2 is that `observed` can be pinned
    while `expected` moves, and only the difference is reported.
    """
    n = n11 + n10 + n01 + n00
    if n <= 0:
        raise ValueError("an agreement table needs observations")
    po = (n11 + n00) / n
    # marginal probabilities of each rater saying pass
    p1, p2 = (n11 + n10) / n, (n11 + n01) / n
    pe = p1 * p2 + (1.0 - p1) * (1.0 - p2)
    if pe >= 1.0:
        # both raters said the same thing to everything: chance explains it all
        return {"observed": po, "expected": pe, "kappa": float("nan"),
                "degenerate": True}
    return {"observed": po, "expected": pe, "kappa": (po - pe) / (1.0 - pe),
            "degenerate": False}


def appraiser_vs_appraiser(part: float = PART_SIGMA,
                           gauge: float = GAUGE_SIGMA, half: float = HALF,
                           guard: float = GUARD_BAND) -> dict:
    """Two appraisers, or one appraiser twice - the arithmetic is identical.

    Two independent noise draws on the same part. That is exactly what a second
    trial is, which is why repeatability and reproducibility have the same shape
    here: neither has any term the other lacks. In a variable study they were
    two different variance components. With counts they are one calculation
    applied to two pairings.
    """
    lim = 12.0 * part

    def both_pass(x):
        p = _pass_prob(x, gauge, half, guard)
        return _phi(x, part) * p * p

    def both_fail(x):
        p = _pass_prob(x, gauge, half, guard)
        return _phi(x, part) * (1.0 - p) * (1.0 - p)

    def split(x):
        p = _pass_prob(x, gauge, half, guard)
        return _phi(x, part) * 2.0 * p * (1.0 - p)

    pp = _simpson(both_pass, -lim, lim, 8000)
    ff = _simpson(both_fail, -lim, lim, 8000)
    sp = _simpson(split, -lim, lim, 8000)
    k = kappa_from_table(pp, sp / 2.0, sp / 2.0, ff)
    return {"both_pass": pp, "both_fail": ff, "disagree": sp,
            "agreement": pp + ff, **k}


# ------------------------------------------------------- claim 1: the base rate
def pass_everything(part: float = PART_SIGMA, half: float = HALF) -> dict:
    """An appraiser who passes every part without looking at it.

    Against himself he is perfect. Against a colleague with the same habit he is
    perfect. Against the truth he scores the base rate, which on a capable
    process is a number that looks like success.
    """
    good = _p_good(part, half)
    return {
        "self_agreement": 1.0,
        "cross_agreement": 1.0,
        "vs_truth": good,
        "effectiveness": good,
        "miss_rate": 1.0,
        "false_alarm_rate": 0.0,
        # kappa sees straight through it: no variation, so no agreement above
        # chance can be computed at all
        "kappa": kappa_from_table(1.0, 0.0, 0.0, 0.0),
    }


# ------------------------------------------------- claim 2: the kappa paradox
def kappa_paradox(observed: float = 0.90) -> list[dict]:
    """Tables sharing one percent agreement, differing only in how skewed.

    Built by construction rather than found: fix `observed`, then walk the split
    between the two agreeing cells from balanced to lopsided. Percent agreement
    cannot tell these apart. Kappa can, and it collapses on the skewed ones -
    which is a problem, because a good process *is* the skewed one.
    """
    rows = []
    dis = 1.0 - observed
    for share in (0.5, 0.7, 0.85, 0.95, 0.99):
        n11 = observed * share
        n00 = observed * (1.0 - share)
        k = kappa_from_table(n11, dis / 2.0, dis / 2.0, n00)
        rows.append({"share_of_agreement_in_pass": share,
                     "both_pass": n11, "both_fail": n00, **k})
    return rows


# ------------------------------- claims 3 and 4: it was a variable gauge always
def kappa_from_gauge(gauges: tuple[float, ...] = (0.5, 1.0, 2.0591260281974,
                                                 4.0, 8.0)) -> list[dict]:
    """Kappa as a function of the gauge underneath the pass/fail decision.

    This is the level's spine. Nobody chooses a kappa; it falls out of the
    variable gauge's sigma, the part spread and the tolerance. An attribute
    study that reports kappa and stops has measured a consequence.
    """
    rows = []
    for g in gauges:
        aa = appraiser_vs_appraiser(gauge=g)
        ct = cross_table(gauge=g)
        rows.append({"gauge": g,
                     "grr_tolerance_pct": 6.0 * g / TOLERANCE * 100.0,
                     "agreement": aa["agreement"], "kappa": aa["kappa"],
                     "effectiveness": ct["effectiveness"],
                     "miss_rate": ct["miss_rate"],
                     "false_alarm_rate": ct["false_alarm_rate"]})
    return rows


def gray_zone(part: float = PART_SIGMA, gauge: float = GAUGE_SIGMA,
              half: float = HALF, sigmas: float = BAND_SIGMAS) -> dict:
    """Where the mistakes are, against where the parts are.

    A part far inside the limit is never failed and a part far outside is never
    passed, so the disagreements in a study concentrate in a band around the
    limit whose width is set by the gauge, not by the appraiser. Reported as a
    ratio, because the share alone means nothing without the share of parts.
    """
    lim = 12.0 * part
    w = sigmas * gauge

    def dis(x):
        p = _pass_prob(x, gauge, half)
        return _phi(x, part) * 2.0 * p * (1.0 - p)

    total = _simpson(dis, -lim, lim, 8000)
    in_band = (_simpson(dis, half - w, half + w, 4000)
               + _simpson(dis, -half - w, -half + w, 4000))
    parts_in_band = (_simpson(lambda x: _phi(x, part), half - w, half + w, 4000)
                     + _simpson(lambda x: _phi(x, part), -half - w, -half + w,
                                4000))
    return {"band_half_width": w,
            "parts_in_band_pct": parts_in_band * 100.0,
            "disagreements_in_band_pct": in_band / total * 100.0 if total else 0.0,
            "concentration": (in_band / total) / parts_in_band if parts_in_band
                             else float("inf")}


# --------------------------------------------- claim 5: the guard band's price
def guard_band_curve(guards: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 3.0, 4.0)
                     ) -> list[dict]:
    """Moving the decision inward: what it buys and what it costs.

    The usual response to an escape is to tighten the acceptance limit. It works
    on escapes. The price is paid entirely in good parts, and the exchange rate
    gets worse the further in you go.
    """
    rows = []
    base = cross_table(guard=0.0)
    for g in guards:
        ct = cross_table(guard=g)
        d_miss = base["miss_rate"] - ct["miss_rate"]
        d_fa = ct["false_alarm_rate"] - base["false_alarm_rate"]
        rows.append({"guard": g, "miss_rate": ct["miss_rate"],
                     "false_alarm_rate": ct["false_alarm_rate"],
                     "effectiveness": ct["effectiveness"],
                     "good_parts_lost_per_escape_saved":
                         (d_fa * base["good"]) / (d_miss * base["bad"])
                         if d_miss > 1e-15 else float("nan")})
    return rows


# ----------------------------------------------- claim 6: a count is expensive
def parts_for_miss_rate(p: float = MISS_RATE_TARGET,
                        half_width: float = MISS_HALF_WIDTH,
                        conf: float = 0.95) -> int:
    """Known-bad parts needed to bound a miss rate to +/- `half_width`.

    A proportion's standard error is sqrt(p(1-p)/n), so the parts needed go as
    one over the square of the precision wanted. There is no averaging trick
    here of the kind Level 1 had - a count carries less information than a
    measurement, and this is the bill for that.
    """
    from scipy import stats
    z = float(stats.norm.ppf(0.5 + conf / 2.0))
    return int(math.ceil(z * z * p * (1.0 - p) / (half_width * half_width)))


def zero_escapes_bound(n: int, conf: float = 0.95) -> float:
    """The miss rate still consistent with seeing zero escapes in `n` bad parts.

    The most common attribute study result is "no misses", and it is much weaker
    than it sounds: the one-sided bound is 1 - (1-conf)^(1/n), which for a
    fifty-part study leaves room for a miss rate near six percent.
    """
    if n < 1:
        raise ValueError("a bound needs at least one part")
    return 1.0 - (1.0 - conf) ** (1.0 / n)


# ------------------------------------------------------------ computed facts
BASE_RATE = _p_good()
LAZY = pass_everything()
CROSS = cross_table()
AGREE = appraiser_vs_appraiser()
PARADOX = kappa_paradox()
BY_GAUGE = kappa_from_gauge()
GRAY = gray_zone()
GRAY_BANDS = [gray_zone(sigmas=s) for s in (1.0, 2.0, 3.0)]
GUARDS = guard_band_curve()

#: The gauge Level 5 left us, expressed as this level's numbers.
EFFECTIVENESS = CROSS["effectiveness"]
MISS_RATE = CROSS["miss_rate"]
FALSE_ALARM = CROSS["false_alarm_rate"]
KAPPA = AGREE["kappa"]
AGREEMENT = AGREE["agreement"]

#: Claim 1's headline: the base rate an idle appraiser scores.
LAZY_VS_TRUTH = LAZY["vs_truth"]

#: Claim 2: same observed agreement, kappa from balanced to skewed.
KAPPA_BALANCED = PARADOX[0]["kappa"]
KAPPA_SKEWED = PARADOX[-1]["kappa"]

#: Claim 4.
PARTS_IN_BAND = GRAY["parts_in_band_pct"]
MISTAKES_IN_BAND = GRAY["disagreements_in_band_pct"]
CONCENTRATION = GRAY["concentration"]

#: Claim 6.
PARTS_FOR_MISS = parts_for_miss_rate()
BOUND_AT_50 = zero_escapes_bound(50)
BOUND_AT_300 = zero_escapes_bound(300)


def main() -> None:
    print(f"the gauge from Level 5: {GAUGE_SIGMA:.4f} um, "
          f"tolerance {TOLERANCE:.0f} um, go/no-go at +/-{HALF:.0f}")
    print()

    print("1. percent agreement cannot see an appraiser who never looks")
    print(f"  an appraiser who passes everything:")
    print(f"    agrees with himself       {LAZY['self_agreement']*100:6.2f} %")
    print(f"    agrees with a colleague   {LAZY['cross_agreement']*100:6.2f} %")
    print(f"    agrees with the truth     {LAZY['vs_truth']*100:6.2f} %")
    print(f"    and misses                {LAZY['miss_rate']*100:6.2f} % "
          f"of the bad parts")
    print(f"  kappa: {'undefined - no variation to explain' if LAZY['kappa']['degenerate'] else LAZY['kappa']['kappa']}")
    print()

    print("2. kappa removes chance, and then punishes a good process")
    print(f"  five tables, all with {PARADOX[0]['observed']*100:.0f} % "
          f"observed agreement:")
    for r in PARADOX:
        print(f"    agreement {r['share_of_agreement_in_pass']*100:5.1f} % "
              f"in the pass cell -> kappa {r['kappa']:6.3f}")
    print(f"  same percent agreement throughout, kappa "
          f"{KAPPA_BALANCED:.3f} -> {KAPPA_SKEWED:.3f}")
    print()

    print("3. nobody chooses a kappa - it falls out of the variable gauge")
    print("     gauge     %GRR/tol   agreement    kappa   effective   miss")
    for r in BY_GAUGE:
        print(f"    {r['gauge']:6.3f} um  {r['grr_tolerance_pct']:7.1f} %  "
              f"{r['agreement']*100:8.3f} %  {r['kappa']:7.3f}  "
              f"{r['effectiveness']*100:8.3f} %  {r['miss_rate']*100:6.2f} %")
    print()

    print("4. and the mistakes come from a band the gauge sets, not the appraiser")
    print("     band around the limit      share of parts   share of mistakes   ratio")
    for s, r in zip((1, 2, 3), GRAY_BANDS):
        print(f"    +/-{s} gauge sigma "
              f"({r['band_half_width']:5.2f} um)  "
              f"{r['parts_in_band_pct']:9.2f} %  "
              f"{r['disagreements_in_band_pct']:15.2f} %  "
              f"{r['concentration']:6.1f}x")
    print()

    print("5. tightening the limit is not free, and the price rises")
    print("     guard     miss      false alarm   good parts lost per escape saved")
    for r in GUARDS:
        cost = ("        -" if math.isnan(r["good_parts_lost_per_escape_saved"])
                else f"{r['good_parts_lost_per_escape_saved']:9.1f}")
        print(f"    {r['guard']:5.1f} um  {r['miss_rate']*100:6.2f} %  "
              f"{r['false_alarm_rate']*100:11.3f} %  {cost}")
    print()

    print("6. a count costs far more parts than a measurement did")
    print(f"  to bound a {MISS_RATE_TARGET*100:.0f} % miss rate to "
          f"+/-{MISS_HALF_WIDTH*100:.0f} points: "
          f"{PARTS_FOR_MISS} known-bad parts")
    print(f"  and 'no escapes' is weak evidence:")
    print(f"    zero misses in  50 bad parts still allows "
          f"{BOUND_AT_50*100:5.2f} %")
    print(f"    zero misses in 300 bad parts still allows "
          f"{BOUND_AT_300*100:5.2f} %")
    print()
    print("  so six levels have described one measurement system. Level 7 hands")
    print("  it back to the process it was built to watch.")


if __name__ == "__main__":
    main()
