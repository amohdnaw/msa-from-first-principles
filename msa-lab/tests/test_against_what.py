"""Level 4's claims.

The load-bearing one is claim 4: `ndc` is a monotone function of the study ratio,
so it cannot carry information the study ratio does not already have. That is
algebra, not statistics, and the test is exact rather than tolerant.

The second is that the two ratios answer different questions and can therefore
land on opposite sides of the same printed gate. The first draft of the library
used one tolerance where both said "reject" - a true statement that demonstrated
nothing - so the instances here are the ones that straddle.
"""
import math

import pytest

from msalab.against_what import (
    ACCEPT_PCT, A_PART, A_STUDY, A_TOL, A_TOLPCT, BAND, B_PART, B_STUDY, B_TOL,
    B_TOLPCT, CAP, CENTRED, GAUGE_SIGMA, NDC, NDC_FROM_RATIO, NDC_GATE_GAP,
    NDC_IS_REDUNDANT, NDC_K, NDC_K_IS_ROOT_TWO, NDC_MIN, REJECT_PCT, SHIFTED,
    STUDY_PCT, STUDY_PCT_AT_NDC5, STUDY_AFTER, STUDY_BEFORE, TOLERANCE,
    TOL_PCT, TOL_UNCHANGED, capability, misclassification, ndc,
    ndc_from_study_ratio, study_ratio, study_ratio_for_ndc, tolerance_ratio,
    verdict,
)
from msalab.measurement import PART_SIGMA


# ------------------------------------- claim 4: ndc is algebraically redundant
def test_ndc_can_be_recovered_from_the_study_ratio_alone():
    """The whole of claim 4, and it is exact.

    If ndc is a function of the study ratio then two gates on the two of them
    cannot disagree except by being inconsistent with each other.
    """
    assert NDC_IS_REDUNDANT
    assert NDC_FROM_RATIO == pytest.approx(NDC, rel=1e-12)


@pytest.mark.parametrize("gauge,part", [
    (0.2, 9.0), (1.0, 4.7), (2.06, 3.0), (4.0, 4.0), (9.0, 1.0),
])
def test_the_recovery_holds_everywhere_not_just_on_one_study(gauge, part):
    assert ndc_from_study_ratio(study_ratio(gauge, part)) == pytest.approx(
        ndc(gauge, part), rel=1e-12)


def test_ndc_is_strictly_decreasing_in_the_study_ratio():
    """Monotone, so it can never rank two gauges differently."""
    vals = [ndc_from_study_ratio(r) for r in (5, 10, 20, 27.1, 30, 50, 80)]
    assert vals == sorted(vals, reverse=True)


def test_the_ndc_gate_and_the_percent_gate_are_different_lines():
    """The finding. Both are printed in the same AIAG table."""
    assert STUDY_PCT_AT_NDC5 == pytest.approx(27.14, abs=0.02)
    assert STUDY_PCT_AT_NDC5 < REJECT_PCT
    assert NDC_GATE_GAP == pytest.approx(2.86, abs=0.02)


def test_rounding_the_constant_moves_the_gate_too():
    """A smaller finding inside the first one, and it cost a failed test.

    The gate sits at 27.14 % using the printed 1.41 and at 27.22 % using the
    exact sqrt(2). The constant's own rounding shifts an acceptance boundary by
    0.08 points - small, and a reminder that a rounded constant in a threshold is
    not the same object as the number it was rounded from.
    """
    with_exact = study_ratio_for_ndc(NDC_MIN, k=math.sqrt(2.0))
    with_printed = study_ratio_for_ndc(NDC_MIN, k=1.41)
    assert with_printed == pytest.approx(STUDY_PCT_AT_NDC5, rel=1e-12)
    assert abs(with_exact - with_printed) == pytest.approx(0.075, abs=0.01)
    assert with_exact > with_printed, "sqrt(2) is the more permissive gate"


def test_the_ndc_constant_is_root_two():
    """1.41 is not a measurement, it is sqrt(2) rounded to two places."""
    assert NDC_K_IS_ROOT_TWO < 0.005
    assert NDC_K == pytest.approx(math.sqrt(2.0), abs=0.005)


def test_a_study_ratio_outside_zero_to_one_hundred_is_refused():
    for bad in (0.0, 100.0, -3.0, 140.0):
        with pytest.raises(ValueError):
            ndc_from_study_ratio(bad)


def test_the_ndc_inversion_round_trips():
    for target in (2.0, 5.0, 10.0):
        r = study_ratio_for_ndc(target)
        assert ndc_from_study_ratio(r) == pytest.approx(target, rel=1e-12)
    with pytest.raises(ValueError):
        study_ratio_for_ndc(0)


# ------------------------------- claims 1 and 2: what each ratio depends on
def test_the_two_ratios_share_a_numerator_and_nothing_else():
    assert study_ratio(2.0, 4.0) == pytest.approx(2.0 / math.hypot(2.0, 4.0) * 100)
    assert tolerance_ratio(2.0, 60.0) == pytest.approx(20.0)


def test_the_tolerance_ratio_cannot_see_the_parts():
    """Claim 2, as an independence statement."""
    a = tolerance_ratio(GAUGE_SIGMA, TOLERANCE)
    assert TOL_UNCHANGED == pytest.approx(a, rel=1e-12)
    # and the study ratio very much can
    assert STUDY_AFTER > STUDY_BEFORE * 1.5


def test_tightening_the_process_makes_the_study_ratio_worse():
    """The counter-intuitive direction, and it is the right one.

    A gauge measuring nearly identical parts cannot tell them apart. Nothing
    about the gauge changed.
    """
    assert STUDY_BEFORE == pytest.approx(40.1, abs=0.2)
    assert STUDY_AFTER == pytest.approx(86.4, abs=0.2)


def test_the_study_ratio_cannot_reach_zero_or_exceed_one_hundred():
    for part in (0.001, 1.0, 1e6):
        r = study_ratio(GAUGE_SIGMA, part)
        assert 0.0 < r < 100.0


def test_a_perfect_gauge_gives_a_zero_study_ratio():
    assert study_ratio(0.0, 4.7) == pytest.approx(0.0)


# --------------------------- claim 3: the same gauge, opposite verdicts
def test_the_same_gauge_fails_one_gate_and_passes_the_other():
    assert verdict(A_STUDY) == "reject"
    assert verdict(A_TOLPCT) == "accept"
    assert verdict(B_STUDY) == "accept"
    assert verdict(B_TOLPCT) == "reject"


def test_both_scenarios_use_the_identical_gauge():
    """Otherwise the demonstration proves nothing."""
    assert study_ratio(GAUGE_SIGMA, A_PART) == pytest.approx(A_STUDY, rel=1e-12)
    assert study_ratio(GAUGE_SIGMA, B_PART) == pytest.approx(B_STUDY, rel=1e-12)
    assert tolerance_ratio(GAUGE_SIGMA, A_TOL) == pytest.approx(A_TOLPCT, rel=1e-12)
    assert tolerance_ratio(GAUGE_SIGMA, B_TOL) == pytest.approx(B_TOLPCT, rel=1e-12)


def test_the_disagreement_band_edges_are_where_the_gates_are():
    assert study_ratio(GAUGE_SIGMA, BAND["part_at_10"]) == pytest.approx(
        ACCEPT_PCT, rel=1e-9)
    assert study_ratio(GAUGE_SIGMA, BAND["part_at_30"]) == pytest.approx(
        REJECT_PCT, rel=1e-9)
    assert BAND["part_at_10"] > BAND["part_at_30"], (
        "a smaller study ratio needs MORE part variation, not less")


def test_the_gates_are_the_numbers_aiag_prints():
    """A sabotage moved ACCEPT_PCT from 10 to 20 and every test still passed.

    The boundary test below compared `verdict()` against `ACCEPT_PCT`, which is
    the code checking itself - it can confirm the function is self-consistent and
    can never notice that the constant changed. The published thresholds belong in
    the test as literals, because here the test IS the specification.
    """
    assert ACCEPT_PCT == 10.0
    assert REJECT_PCT == 30.0
    assert NDC_MIN == 5
    assert verdict(9.9) == "accept"
    assert verdict(10.1) == "conditional"
    assert verdict(29.9) == "conditional"
    assert verdict(30.1) == "reject"


def test_the_verdict_boundaries_are_inclusive_the_way_the_table_reads():
    assert verdict(ACCEPT_PCT) == "accept"
    assert verdict(ACCEPT_PCT + 0.01) == "conditional"
    assert verdict(REJECT_PCT) == "conditional"
    assert verdict(REJECT_PCT + 0.01) == "reject"


# ------------------- claim 5: the decision cost, which no ratio reports
def test_a_conformance_decision_can_go_wrong_in_both_directions():
    assert CENTRED["false_accept_pct"] > 0
    assert CENTRED["false_reject_pct"] > 0


def test_a_large_share_of_bad_parts_is_accepted_even_when_centred():
    """The sentence that ships, and it is not the same as the headline rate."""
    assert CENTRED["false_accept_pct"] < 0.1
    assert CENTRED["bad_parts_accepted_pct"] > 20
    assert CENTRED["bad_parts_accepted_pct"] > 100 * CENTRED["false_accept_pct"]


def test_shifting_the_process_moves_the_risk_without_touching_the_gauge():
    assert SHIFTED["scrap_rate_pct"] > 20 * CENTRED["scrap_rate_pct"]
    assert SHIFTED["false_accept_pct"] > 10 * CENTRED["false_accept_pct"]
    assert SHIFTED["good_parts_rejected_pct"] > CENTRED["good_parts_rejected_pct"]


def test_the_percentages_are_identical_across_that_shift():
    """The point of claim 5: %GRR did not change and the risk did."""
    assert study_ratio() == pytest.approx(STUDY_PCT, rel=1e-12)
    assert tolerance_ratio() == pytest.approx(TOL_PCT, rel=1e-12)


def test_a_perfect_gauge_misclassifies_nothing():
    m = misclassification(gauge=1e-9, n=40_000)
    assert m["false_accept_pct"] == pytest.approx(0.0, abs=0.01)
    assert m["false_reject_pct"] == pytest.approx(0.0, abs=0.01)


def test_a_worse_gauge_misclassifies_more():
    a = misclassification(gauge=GAUGE_SIGMA, n=60_000, seed=1)
    b = misclassification(gauge=GAUGE_SIGMA * 3, n=60_000, seed=1)
    assert b["false_accept_pct"] > a["false_accept_pct"]
    assert b["good_parts_rejected_pct"] > a["good_parts_rejected_pct"]


# --------------------------------------------------- the setting itself
def test_the_capability_number_is_used_once_and_named_plainly():
    assert capability() == pytest.approx(6.0 * PART_SIGMA / TOLERANCE, rel=1e-12)
    assert CAP == pytest.approx(0.94, abs=0.01)


def test_the_gauge_is_the_one_levels_two_and_three_built():
    from msalab.reproducibility import SIGMA_REPEAT, SIGMA_REPRODUCE
    assert GAUGE_SIGMA == pytest.approx(
        math.hypot(SIGMA_REPEAT, SIGMA_REPRODUCE), rel=1e-12)
