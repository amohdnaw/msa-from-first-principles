"""LEVEL 4 - %GRR, ndc, and against what.

Levels 1 to 3 produced variances. A verdict is not a variance. Turning one into
the other needs a denominator, and choosing it is not arithmetic - it is a
decision about what the gauge is for. The two usual choices disagree on purpose,
and the standard prints both without saying which question you are asking.

    %GRR against study variation   can this gauge tell these parts apart?
    %GRR against tolerance         can it decide whether a part conforms?

Five claims, computed here and nowhere else:

1. Same numerator, two denominators, two questions. Neither is wrong; they are
   answers to things you might genuinely want to know.
2. They disagree, and the disagreement is not sampling noise - it is process
   capability. A tight process makes the study ratio look terrible while the
   tolerance ratio is fine, and a sloppy one does the reverse.
3. So a gauge passes one AIAG gate and fails the other, at the standard's own
   thresholds, and there is a computable band where that happens.
4. `ndc` adds nothing. It is a monotone function of the study ratio, so it
   cannot disagree with it - and its own threshold of 5 corresponds to a study
   ratio of 27.2 %, which contradicts the 30 % printed beside it in the same
   table.
5. What a conformance decision actually costs is a misclassification rate, and
   that depends on where the process sits relative to the limits. Neither the
   study ratio nor ndc knows anything about that.

    PYTHONPATH=src .venv/bin/python -m msalab.against_what
"""
from __future__ import annotations

import math

import numpy as np

from msalab.measurement import PART_SIGMA, observed_sigma
from msalab.reproducibility import SIGMA_REPEAT, SIGMA_REPRODUCE

# ---------------------------------------------------------------- the setting
#: The gauge Levels 2 and 3 built, carried forward whole.
GAUGE_SIGMA = math.hypot(SIGMA_REPEAT, SIGMA_REPRODUCE)

#: The bore has a drawing tolerance. Levels 1-3 never needed one, because none of
#: them made a decision about a part - and that is exactly what changes here.
TOLERANCE = 30.0
NOMINAL_OFFSET = 0.0

#: AIAG's gates, printed for both ratios without distinguishing the questions.
ACCEPT_PCT = 10.0
REJECT_PCT = 30.0
#: And ndc's own gate, in the same table.
NDC_MIN = 5

#: The constant in AIAG's ndc formula.
NDC_K = 1.41


def study_ratio(gauge: float = GAUGE_SIGMA, part: float = PART_SIGMA) -> float:
    """%GRR against study variation: the gauge as a share of what you observed.

    The 6-sigma multipliers AIAG writes on both terms cancel, so this is a ratio
    of standard deviations and nothing else. It answers: of the spread in this
    study, how much was the gauge?
    """
    total = observed_sigma(part, gauge)
    return gauge / total * 100.0


def tolerance_ratio(gauge: float = GAUGE_SIGMA,
                    tolerance: float = TOLERANCE) -> float:
    """%GRR against tolerance: the gauge as a share of the room you were given.

    Six sigma of gauge spread against the whole tolerance band. It answers a
    completely different question - whether the gauge can decide conformance -
    and it does not care how much the parts vary.
    """
    return 6.0 * gauge / tolerance * 100.0


def ndc(gauge: float = GAUGE_SIGMA, part: float = PART_SIGMA,
        k: float = NDC_K) -> float:
    """Number of distinct categories, as AIAG defines it.

    `k` is 1.41, which is the square root of two to two decimals - and the
    tests check that reading rather than take it on faith. It is a function of
    the part-to-gauge ratio and of nothing else.
    """
    return k * part / gauge


def ndc_from_study_ratio(pct: float, k: float = NDC_K) -> float:
    """ndc computed from the study ratio alone.

    This function is claim 4. If ndc can be recovered from the study ratio with
    no further information, then ndc carries no information the study ratio did
    not already have, and two gates on the two of them cannot disagree except by
    being inconsistent with each other.

        r = gauge / total,  so  part / gauge = sqrt(1 - r^2) / r
    """
    r = pct / 100.0
    if not 0.0 < r < 1.0:
        raise ValueError("a study ratio must be strictly between 0 and 100 %")
    return k * math.sqrt(1.0 - r * r) / r


def study_ratio_for_ndc(target: float = NDC_MIN, k: float = NDC_K) -> float:
    """Invert claim 4: the study ratio at which ndc hits `target`.

    The number this returns is the point of the level's sharpest finding. AIAG
    prints "ndc must reach 5" and "reject above 30 %" in the same table, and they
    are not the same line.
    """
    if target <= 0:
        raise ValueError("ndc must be positive")
    # ndc = k*sqrt(1-r^2)/r  ->  r = k / sqrt(k^2 + target^2)
    r = k / math.sqrt(k * k + target * target)
    return r * 100.0


def capability(part: float = PART_SIGMA, tolerance: float = TOLERANCE) -> float:
    """The process spread as a share of the tolerance. Cp, without saying Cp.

    Named `capability` rather than borrowed from the SPC site on purpose: this
    level needs the ratio to explain why two denominators disagree, and it is
    not allowed to teach capability. One number, used once.
    """
    return 6.0 * part / tolerance


def disagreement_band(gauge: float = GAUGE_SIGMA,
                      tolerance: float = TOLERANCE) -> dict:
    """The part spreads at which the two ratios land on opposite sides of a gate.

    With the gauge and the tolerance fixed, the tolerance ratio is fixed too -
    it does not know about the parts. So the disagreement is driven entirely by
    the part spread, and the band has closed-form edges.
    """
    tol = tolerance_ratio(gauge, tolerance)
    verdict_tol = ("accept" if tol <= ACCEPT_PCT
                   else "reject" if tol > REJECT_PCT else "conditional")

    def part_for_study(pct: float) -> float:
        r = pct / 100.0
        return gauge * math.sqrt(1.0 - r * r) / r

    return {"tolerance_pct": tol, "tolerance_verdict": verdict_tol,
            # part spread that puts the study ratio exactly on each gate
            "part_at_10": part_for_study(ACCEPT_PCT),
            "part_at_30": part_for_study(REJECT_PCT),
            "part_at_ndc5": part_for_study(study_ratio_for_ndc())}


def verdict(pct: float) -> str:
    if pct <= ACCEPT_PCT:
        return "accept"
    if pct > REJECT_PCT:
        return "reject"
    return "conditional"


def misclassification(gauge: float = GAUGE_SIGMA, part: float = PART_SIGMA,
                      tolerance: float = TOLERANCE, offset: float = 0.0,
                      n: int = 400_000, seed: int = 404) -> dict:
    """What the decision actually costs, by simulation.

    A conformance decision compares a *reading* to a limit, so a part inside the
    limits can be rejected and a part outside them accepted. That is the thing a
    percentage is standing in for, and it depends on where the process sits -
    which neither the study ratio nor ndc knows.

    Returns rates as percentages of all parts, and also conditioned on the
    truth, because "1 % of parts are false accepts" and "8 % of bad parts are
    accepted" are different sentences and the second is the one that ships.
    """
    rng = np.random.default_rng(seed)
    truth = rng.normal(offset, part, n)
    read = truth + rng.normal(0.0, gauge, n)
    half = tolerance / 2.0
    good = np.abs(truth) <= half
    passed = np.abs(read) <= half

    false_accept = int((~good & passed).sum())
    false_reject = int((good & ~passed).sum())
    bad = int((~good).sum())
    return {
        "scrap_rate_pct": (1 - good.mean()) * 100.0,
        "false_accept_pct": false_accept / n * 100.0,
        "false_reject_pct": false_reject / n * 100.0,
        # the sentence that ships
        "bad_parts_accepted_pct": (false_accept / bad * 100.0) if bad else 0.0,
        "good_parts_rejected_pct": (false_reject / int(good.sum()) * 100.0),
    }


# ------------------------------------------------------------ computed facts
STUDY_PCT = study_ratio()
TOL_PCT = tolerance_ratio()
NDC = ndc()
CAP = capability()

STUDY_VERDICT = verdict(STUDY_PCT)
TOL_VERDICT = verdict(TOL_PCT)
VERDICTS_DISAGREE = STUDY_VERDICT != TOL_VERDICT

#: Claim 4, exactly. ndc recovered from the study ratio with nothing else.
NDC_FROM_RATIO = ndc_from_study_ratio(STUDY_PCT)
NDC_IS_REDUNDANT = abs(NDC_FROM_RATIO - NDC) < 1e-9
#: And the line ndc's threshold really draws, against the one printed beside it.
STUDY_PCT_AT_NDC5 = study_ratio_for_ndc()
NDC_GATE_GAP = REJECT_PCT - STUDY_PCT_AT_NDC5

#: Claims 2 and 3. The first draft used one tolerance and one part spread, and
#: both ratios said "reject" - a true statement about that gauge and no
#: demonstration of anything. The claim needs two settings that straddle the
#: gates in opposite directions, with the SAME gauge in both, because the whole
#: point is that the gauge did not change.
#:
#: A: a well-controlled process on a generous drawing. The gauge cannot tell
#: these parts apart, and has no trouble at all deciding conformance.
A_PART, A_TOL = 3.0, 150.0
A_STUDY = study_ratio(part=A_PART)
A_TOLPCT = tolerance_ratio(tolerance=A_TOL)
#: B: a sloppy process on a tight drawing. The gauge distinguishes these parts
#: easily and cannot be trusted with a conformance call.
B_PART, B_TOL = 25.0, 35.0
B_STUDY = study_ratio(part=B_PART)
B_TOLPCT = tolerance_ratio(tolerance=B_TOL)

#: Claim 2 in one sentence: one of these ratios depends on the parts and the
#: other does not. Tighten the process and the study ratio gets worse while the
#: tolerance ratio does not move - the gauge did not get worse, the question got
#: harder.
TIGHTEN_FROM, TIGHTEN_TO = 4.7, 1.2
STUDY_BEFORE = study_ratio(part=TIGHTEN_FROM)
STUDY_AFTER = study_ratio(part=TIGHTEN_TO)
TOL_UNCHANGED = tolerance_ratio()

BAND = disagreement_band()

#: Claim 5: what the decision costs, at two process positions with one gauge.
CENTRED = misclassification()
SHIFTED = misclassification(offset=TOLERANCE * 0.25)

#: The 1.41, read as what it is.
NDC_K_IS_ROOT_TWO = abs(NDC_K - math.sqrt(2.0))


def main() -> None:
    print(f"the gauge from Levels 2-3: {GAUGE_SIGMA:.4f} um")
    print(f"the drawing tolerance:     {TOLERANCE} um")
    print(f"the parts:                 {PART_SIGMA} um  "
          f"(spread is {CAP*100:.0f} % of tolerance)")
    print()
    print("1. same numerator, two denominators")
    print(f"  against study variation  {STUDY_PCT:5.1f} %  -> {STUDY_VERDICT}")
    print(f"  against tolerance        {TOL_PCT:5.1f} %  -> {TOL_VERDICT}")
    print(f"  on THIS tolerance they happen to agree ({VERDICTS_DISAGREE} that")
    print(f"  they differ) - which is a fact about 30 um, not about the ratios.")
    print(f"  claim 3 shows what happens when the tolerance changes.")
    print()
    print("2. one ratio depends on the parts; the other does not")
    print(f"  tighten the process from {TIGHTEN_FROM} um to {TIGHTEN_TO} um:")
    print(f"    study ratio     {STUDY_BEFORE:5.1f} % -> {STUDY_AFTER:5.1f} % "
          f"(worse)")
    print(f"    tolerance ratio {TOL_UNCHANGED:5.1f} % -> {TOL_UNCHANGED:5.1f} % "
          f"(unmoved)")
    print(f"  the gauge did not get worse. the question got harder.")
    print()
    print("3. so the same gauge passes one gate and fails the other")
    print(f"  A  well-controlled process, generous drawing "
          f"(parts {A_PART} um, tolerance {A_TOL} um)")
    print(f"     study {A_STUDY:5.1f} % -> {verdict(A_STUDY):<11}  "
          f"tolerance {A_TOLPCT:5.1f} % -> {verdict(A_TOLPCT)}")
    print(f"  B  sloppy process, tight drawing "
          f"(parts {B_PART} um, tolerance {B_TOL} um)")
    print(f"     study {B_STUDY:5.1f} % -> {verdict(B_STUDY):<11}  "
          f"tolerance {B_TOLPCT:5.1f} % -> {verdict(B_TOLPCT)}")
    print(f"  identical gauge, {GAUGE_SIGMA:.2f} um, in both rows")
    print()
    print("4. ndc adds nothing")
    print(f"  ndc from the components   {NDC:.4f}")
    print(f"  ndc from the study ratio  {NDC_FROM_RATIO:.4f}  "
          f"identical: {NDC_IS_REDUNDANT}")
    print(f"  so ndc >= {NDC_MIN} is exactly study ratio <= "
          f"{STUDY_PCT_AT_NDC5:.1f} %")
    print(f"  which is {NDC_GATE_GAP:.1f} points tighter than the {REJECT_PCT:.0f} % "
          f"printed beside it in the same table")
    print(f"  and the 1.41 is sqrt(2), off by {NDC_K_IS_ROOT_TWO:.5f}")
    print()
    print("5. what the decision costs, which no percentage tells you")
    for name, m in (("centred", CENTRED), ("shifted a quarter of tolerance", SHIFTED)):
        print(f"  {name}:")
        print(f"    parts genuinely out of tolerance {m['scrap_rate_pct']:6.3f} %")
        print(f"    false accepts, of all parts      {m['false_accept_pct']:6.3f} %")
        print(f"    of the BAD parts, accepted       {m['bad_parts_accepted_pct']:6.2f} %")
        print(f"    of the GOOD parts, rejected      {m['good_parts_rejected_pct']:6.2f} %")
    print()
    print("same gauge, same %GRR, and the risk moved. so a percentage is a proxy,")
    print("and Level 5 asks what happens when the gauge is not merely noisy but wrong.")


if __name__ == "__main__":
    main()
