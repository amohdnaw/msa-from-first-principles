"""Level 7's claims.

The load-bearing test is `test_the_seam_identity_is_exact`. Everything else in
this level is a consequence worth showing, but the identity is the reason the
level exists and the reason the parent contract was amended to let it be stated:

    Cpk_max = T / (6 sigma_gauge) = 100 / %GRR_tol

If that ever became approximate, the claim would have to be withdrawn.
"""
import math

import pytest

from msalab.handshake import (
    AIAG_GATES, ARLS, CAP, CEILINGS, DRIFT_CHART, INFLATION, LIMITS, SAME_CHART,
    SHIFTS, SUBGROUP, WITHIN, WRONG_N, arl, capability, ceiling_table,
    chart_limits, drift_on_the_chart, grr_for_cpk, indistinguishable_pairs,
    inflation, within_subgroup_content, wrong_subgroup,
)
from msalab.accuracy import GAUGE_SIGMA
from msalab.against_what import TOLERANCE, tolerance_ratio
from msalab.measurement import PART_SIGMA
from msalab.reproducibility import SIGMA_REPEAT


# ---------------------------------------------------- claim 1: the width
def test_the_inflation_is_level_ones_identity():
    """Nothing new is introduced here. sqrt(1 + (sg/sp)^2) is Level 1's variance
    addition with the root taken, and if it drifted from that the rest of the
    level would be measuring something else."""
    assert inflation() == pytest.approx(
        math.hypot(PART_SIGMA, GAUGE_SIGMA) / PART_SIGMA, rel=1e-15)
    assert inflation(gauge=0.0) == pytest.approx(1.0, abs=1e-15)


def test_the_limits_inflate_by_exactly_that_factor():
    """The subgroup size cancels: it divides both the true and the observed
    standard error, so the widening is the same at any n. A version that let n
    into the ratio would look plausible and be wrong."""
    for n in (2, 5, 9, 25):
        lim = chart_limits(n=n)
        assert lim["inflation"] == pytest.approx(INFLATION, rel=1e-14)


def test_a_perfect_gauge_costs_no_width():
    lim = chart_limits(gauge=1e-12)
    assert lim["wider_pct"] == pytest.approx(0.0, abs=1e-9)


# ------------------------------------------------- claim 2: the detection
def test_measurement_error_always_costs_detection():
    for a in ARLS:
        assert a["arl_as_charted"] >= a["arl_if_gauge_were_perfect"]
        assert a["subgroups_lost"] >= 0.0


def test_the_penalty_is_worst_on_a_moderate_shift():
    """A three-sigma shift is caught immediately either way, and a tiny one is
    missed either way. The cost lands in between, which is exactly the range a
    chart is run to cover - so the penalty is not a curiosity at the extremes.
    """
    ratios = {a["shift"]: a["penalty_ratio"] for a in ARLS}
    assert ratios[3.0] < 1.01
    assert ratios[1.0] > ratios[3.0]
    assert ratios[1.0] > 1.2
    peak = max(ratios, key=lambda s: ratios[s])
    assert 0.5 <= peak <= 1.5


def test_a_perfect_gauge_costs_no_detection():
    a = arl(1.0, gauge=1e-12)
    assert a["subgroups_lost"] == pytest.approx(0.0, abs=1e-6)
    assert a["penalty_ratio"] == pytest.approx(1.0, abs=1e-9)


def test_the_arl_is_the_reciprocal_of_a_probability():
    """A run length below one would mean signalling more often than every
    subgroup, which is not a thing. Cheap, and it caught a sign error."""
    for a in ARLS:
        assert a["arl_if_gauge_were_perfect"] >= 1.0
        assert a["arl_as_charted"] >= 1.0


# --------------------------------------- claims 3 and 4: the identity
def test_observed_capability_is_true_capability_over_the_inflation():
    assert CAP["observed_cpk"] == pytest.approx(
        CAP["true_cpk"] / INFLATION, rel=1e-14)


def test_the_gauge_alone_moves_this_process_across_one():
    """Not a general law - a fact about this gauge and this process, and the
    reason the level is worth a reader's time: 1.0638 true, 0.9744 as reported.
    A plant would fail an audit on the gauge, having done nothing wrong."""
    assert CAP["true_cpk"] > 1.0
    assert CAP["observed_cpk"] < 1.0


def test_the_seam_identity_is_exact():
    """The whole level. T/(6 sigma_g) and 100/%GRR_tol are the same number
    because %GRR_tol is defined as 6 sigma_g / T - so this is an identity, and
    it must hold at machine precision for every gauge, not just ours.
    """
    for g in (0.1, 0.5, 1.0, GAUGE_SIGMA, 4.0, 12.0):
        ceiling = TOLERANCE / (6.0 * g)
        from_grr = 100.0 / tolerance_ratio(g, TOLERANCE)
        assert ceiling == pytest.approx(from_grr, rel=1e-15)
    assert CAP["identity_holds"] is True


def test_the_ceiling_is_actually_a_ceiling():
    """Approached from below as the process improves, and never crossed."""
    prev = 0.0
    for part in (8.0, 4.7, 2.0, 0.5, 0.05):
        c = capability(part=part)
        assert c["observed_cpk"] < c["ceiling"]
        assert c["observed_cpk"] > prev
        prev = c["observed_cpk"]
    # in the limit it arrives
    assert capability(part=1e-9)["observed_cpk"] == pytest.approx(
        CAP["ceiling"], rel=1e-6)


def test_the_published_gates_are_capability_limits():
    """The table that should be printed beside the AIAG gates and never is."""
    table = {r["grr_tolerance_pct"]: r["cpk_ceiling"] for r in ceiling_table()}
    assert table[10.0] == pytest.approx(10.0, rel=1e-15)
    assert table[30.0] == pytest.approx(10.0 / 3.0, rel=1e-15)
    assert sorted(table) == list(AIAG_GATES)


def test_reading_it_backwards_admits_when_a_target_is_unreachable():
    """The first version of this reported only the gauge-only ceiling, which said
    Cpk 1.33 needs a gauge under 75 % of tolerance - reassuring and useless. On
    this process 1.33 cannot be reached with a perfect gauge, because the whole
    sigma budget is smaller than the parts.
    """
    easy = grr_for_cpk(1.00)
    assert easy["reachable_on_this_process"] is True
    assert easy["gauge_sigma_required"] < GAUGE_SIGMA

    for target in (1.33, 1.67, 2.00):
        r = grr_for_cpk(target)
        assert r["reachable_on_this_process"] is False
        assert r["observed_sigma_budget"] < PART_SIGMA
        assert math.isnan(r["gauge_sigma_required"])


def test_the_required_gauge_actually_delivers_the_target():
    """A necessary condition is not enough; the number handed back has to work."""
    r = grr_for_cpk(1.00)
    got = capability(gauge=r["gauge_sigma_required"])
    assert got["observed_cpk"] == pytest.approx(1.00, rel=1e-9)


# ------------------------------------------- claim 5: inseparable, demonstrated
def test_one_chart_cannot_distinguish_five_different_factories():
    """Inseparability demonstrated rather than asserted: every split produces the
    identical within-subgroup number, while the true capability underneath ranges
    over more than a factor of two."""
    seen = {round(r["within_estimate"], 12) for r in SAME_CHART}
    assert len(seen) == 1, "the rows must be indistinguishable on the chart"
    cpks = [r["true_cpk"] for r in SAME_CHART]
    assert max(cpks) > 2 * min(cpks)


def test_the_gauge_is_inside_the_within_subgroup_estimate():
    w = within_subgroup_content()
    assert w["within_estimate"] == pytest.approx(
        math.hypot(PART_SIGMA, SIGMA_REPEAT), rel=1e-15)
    assert w["within_estimate"] > PART_SIGMA
    assert w["gauge_share_of_variance"] > 0.0


def test_a_bigger_gauge_share_means_a_better_hidden_process():
    """The direction that makes the point: holding the chart's number fixed, more
    gauge means the real parts are tighter than they look. So the chart cannot
    tell a capable process with a bad gauge from a poor one with a good gauge."""
    rows = indistinguishable_pairs()
    shares = [r["gauge_share_of_variance"] for r in rows]
    cpks = [r["true_cpk"] for r in rows]
    assert shares == sorted(shares)
    assert cpks == sorted(cpks)


# ----------------------------------------- claim 6: what the chart may assume
def test_a_drifting_gauge_signals_as_a_process_problem():
    """Level 5's invisible drift, arriving on somebody else's chart. It shows up
    as a run long before it reaches the limits, so it will be investigated as a
    process change - which is the cost of the assumption the chart is making."""
    d = DRIFT_CHART
    assert d["points_outside"] == 0
    assert d["first_run_of_seven"] is not None
    assert d["total_drift"] < d["limit_half_width"]


def test_a_stable_gauge_puts_no_run_on_the_chart():
    d = drift_on_the_chart(drift_per_subgroup=0.0)
    assert d["first_run_of_seven"] is None
    assert d["points_outside"] == 0


# --------------------------------- claim 7: the study owes the chart its shape
def test_a_study_that_averages_understates_the_limits():
    """Level 1's averaging result, misapplied on purpose: a gauge reported as the
    mean of three readings is not the gauge the chart is using."""
    w = wrong_subgroup()
    assert w["gauge_as_studied"] == pytest.approx(
        GAUGE_SIGMA / math.sqrt(3), rel=1e-14)
    assert w["spread_as_charted"] > w["spread_as_studied"]
    assert w["limits_understated_pct"] > 0.0


def test_matching_the_structure_costs_nothing():
    w = wrong_subgroup(study_n=1)
    assert w["limits_understated_pct"] == pytest.approx(0.0, abs=1e-12)


# ------------------------------------------------------- closing two holes
def test_the_in_control_run_length_needs_both_tails():
    """Sabotage 3 survived: with a positive shift the lower tail is negligible,
    so dropping it changes almost nothing at any shift this level prints.

    At zero shift it changes everything. A three-sigma chart signals on 0.27 % of
    subgroups when nothing has moved, giving the ARL every textbook quotes - and
    that 0.27 % is two tails. One tail halves it.
    """
    a = arl(0.0)
    assert a["arl_if_gauge_were_perfect"] == pytest.approx(370.4, rel=0.005)
    assert a["arl_as_charted"] == pytest.approx(370.4, rel=0.005)
    # and a false alarm cannot depend on the gauge: both sides are standardised
    # against their own spread, so the in-control rate is identical
    assert a["penalty_ratio"] == pytest.approx(1.0, abs=1e-12)


def test_the_reported_identity_field_is_the_one_that_is_checked():
    """Sabotage 5 survived: `test_the_seam_identity_is_exact` recomputed
    100/%GRR itself instead of reading what the module reports, so replacing the
    100 with a 6 in `ceiling_from_grr` changed a published number and no test
    noticed. The same shape of mistake as Level 4's self-referential gate.

    Read the field. Then pin it to a literal, so a units slip has nowhere to hide.
    """
    assert CAP["ceiling_from_grr"] == pytest.approx(CAP["ceiling"], rel=1e-15)
    assert CAP["ceiling_from_grr"] == pytest.approx(2.4282153, rel=1e-6)
    assert CAP["grr_tolerance_pct"] == pytest.approx(41.1825206, rel=1e-6)
    # and the table is built from the same expression
    for r in ceiling_table():
        assert r["cpk_ceiling"] == pytest.approx(100.0 / r["grr_tolerance_pct"],
                                                 rel=1e-15)
