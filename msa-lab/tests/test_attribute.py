"""Level 6's claims.

The load-bearing test here is `test_kappa_is_not_a_free_parameter`: the level's
spine is that an attribute study reports a consequence of the variable gauge
rather than an independent property of the appraisers. If kappa could move while
the gauge stood still, the whole level would be wrong.
"""
import math

import numpy as np
import pytest

from msalab.attribute import (
    AGREE, BASE_RATE, BOUND_AT_50, CROSS, GRAY_BANDS, GUARDS, KAPPA,
    LAZY, MISS_RATE, PARADOX, appraiser_vs_appraiser, cross_table, gray_zone,
    guard_band_curve, kappa_from_gauge, kappa_from_table, parts_for_miss_rate,
    pass_everything, zero_escapes_bound, HALF,
)
from msalab.accuracy import GAUGE_SIGMA
from msalab.measurement import PART_SIGMA


# ------------------------------------------------------- the table itself
def test_the_four_cells_are_a_probability_distribution():
    """Four counts that must sum to one, or every rate built on them is wrong."""
    c = cross_table()
    total = c["good_pass"] + c["good_fail"] + c["bad_pass"] + c["bad_fail"]
    assert total == pytest.approx(1.0, abs=1e-9)
    assert c["good"] + c["bad"] == pytest.approx(1.0, abs=1e-9)


def test_effectiveness_is_the_two_correct_cells():
    c = cross_table()
    assert c["effectiveness"] == pytest.approx(c["good_pass"] + c["bad_fail"],
                                               abs=1e-12)


def test_the_two_error_rates_use_their_own_denominators():
    """A miss rate is per bad part, not per part. Dividing both by the total is
    the most common way to make an attribute study look good."""
    c = cross_table()
    assert c["miss_rate"] == pytest.approx(c["bad_pass"] / c["bad"], abs=1e-12)
    assert c["false_alarm_rate"] == pytest.approx(c["good_fail"] / c["good"],
                                                 abs=1e-12)
    # and they are genuinely different scales on this process
    assert c["miss_rate"] > 50 * c["false_alarm_rate"]


# ------------------------------------------------- claim 1: the base rate trap
def test_an_appraiser_who_never_looks_scores_well():
    z = pass_everything()
    assert z["self_agreement"] == 1.0
    assert z["cross_agreement"] == 1.0
    assert z["vs_truth"] > 0.99
    assert z["miss_rate"] == 1.0


def test_kappa_refuses_to_score_a_constant_appraiser():
    """Not a high kappa, not a low one - undefined.

    Both marginals are 1.0, so chance agreement is also 1.0 and the ratio is
    0/0. Reporting any number there would be inventing information.
    """
    k = pass_everything()["kappa"]
    assert k["degenerate"] is True
    assert math.isnan(k["kappa"])


def test_the_base_rate_is_where_the_lazy_score_comes_from():
    """It is the process being capable, not the appraiser being competent."""
    assert pass_everything()["vs_truth"] == pytest.approx(BASE_RATE, abs=1e-12)


# ------------------------------------------------ claim 2: the kappa paradox
def test_identical_agreement_gives_wildly_different_kappa():
    obs = {round(r["observed"], 12) for r in PARADOX}
    assert len(obs) == 1, "the tables must share one percent agreement"
    ks = [r["kappa"] for r in PARADOX]
    assert ks[0] > 0.75 and ks[-1] < 0.15
    assert ks == sorted(ks, reverse=True)


def test_a_skewed_stream_depresses_kappa_on_its_own():
    """Which is the trap: the better the process, the worse kappa looks."""
    balanced = kappa_from_table(0.45, 0.05, 0.05, 0.45)
    skewed = kappa_from_table(0.891, 0.05, 0.05, 0.009)
    assert balanced["observed"] == pytest.approx(skewed["observed"], abs=1e-9)
    assert balanced["kappa"] > 4 * skewed["kappa"]


def test_kappa_is_zero_when_agreement_is_exactly_chance():
    """A calibration point that does not depend on any of this level's setup."""
    # two raters each passing 70 % independently
    p = 0.7
    k = kappa_from_table(p * p, p * (1 - p), (1 - p) * p, (1 - p) * (1 - p))
    assert k["kappa"] == pytest.approx(0.0, abs=1e-12)


# --------------------------------- claim 3: kappa is derived, not chosen
def test_kappa_is_not_a_free_parameter():
    """The spine of the level.

    Kappa, agreement, effectiveness and both error rates are all functions of
    the variable gauge's sigma. Worsen the gauge and every one of them moves in
    the direction it must, monotonically. Nothing here is an appraiser property.
    """
    rows = kappa_from_gauge()
    assert [r["kappa"] for r in rows] == sorted(
        [r["kappa"] for r in rows], reverse=True)
    assert [r["agreement"] for r in rows] == sorted(
        [r["agreement"] for r in rows], reverse=True)
    assert [r["miss_rate"] for r in rows] == sorted([r["miss_rate"] for r in rows])
    assert [r["false_alarm_rate"] for r in rows] == sorted(
        [r["false_alarm_rate"] for r in rows])


def test_a_capable_gauge_still_produces_a_mediocre_kappa():
    """The number every published guideline would call unacceptable, on the
    gauge Levels 2 to 5 built - while percent agreement reads over 99 %."""
    a = appraiser_vs_appraiser()
    assert a["agreement"] > 0.99
    assert a["kappa"] < 0.5


def test_repeatability_and_reproducibility_are_one_calculation_here():
    """In a variable study they were separate variance components. Two
    independent noise draws is two independent noise draws, so with counts there
    is no arithmetic that distinguishes a second trial from a second appraiser.
    """
    same = appraiser_vs_appraiser(gauge=GAUGE_SIGMA)
    also = appraiser_vs_appraiser(gauge=GAUGE_SIGMA)
    assert same["kappa"] == pytest.approx(also["kappa"], abs=1e-15)


def test_a_perfect_gauge_drives_agreement_to_certainty():
    """A limit check with no noise cannot disagree with itself."""
    a = appraiser_vs_appraiser(gauge=1e-6)
    assert a["agreement"] == pytest.approx(1.0, abs=1e-6)
    assert a["disagree"] == pytest.approx(0.0, abs=1e-6)


# ------------------------------------------------------- claim 4: the gray zone
def test_the_mistakes_concentrate_where_the_gauge_says_they_must():
    for r in GRAY_BANDS:
        assert r["disagreements_in_band_pct"] > r["parts_in_band_pct"]
        assert r["concentration"] > 10.0
    assert GRAY_BANDS[-1]["disagreements_in_band_pct"] > 95.0
    assert GRAY_BANDS[-1]["parts_in_band_pct"] < 10.0


def test_the_band_width_follows_the_gauge_not_the_tolerance():
    """Double the gauge and the band doubles. That is the claim that makes
    'appraiser error' a property of the instrument."""
    a = gray_zone(gauge=1.0)
    b = gray_zone(gauge=2.0)
    assert b["band_half_width"] == pytest.approx(2 * a["band_half_width"],
                                                 abs=1e-12)
    assert b["parts_in_band_pct"] > a["parts_in_band_pct"]


# ---------------------------------------------------- claim 5: the guard band
def test_a_guard_band_trades_escapes_for_good_parts():
    rows = guard_band_curve()
    assert [r["miss_rate"] for r in rows] == sorted(
        [r["miss_rate"] for r in rows], reverse=True)
    assert [r["false_alarm_rate"] for r in rows] == sorted(
        [r["false_alarm_rate"] for r in rows])


def test_the_exchange_rate_gets_worse_the_further_in_you_go():
    """The reason 'just tighten it' stops working: the cost per escape saved is
    not constant, it rises, so each extra micron of guard band buys less."""
    costs = [r["good_parts_lost_per_escape_saved"] for r in guard_band_curve()
             if not math.isnan(r["good_parts_lost_per_escape_saved"])]
    assert costs == sorted(costs)
    assert costs[-1] > 3 * costs[0]


def test_no_guard_band_is_the_baseline():
    assert guard_band_curve(guards=(0.0,))[0]["miss_rate"] == pytest.approx(
        cross_table()["miss_rate"], abs=1e-12)


# ------------------------------------------------- claim 6: counts are dear
def test_bounding_a_proportion_costs_hundreds_of_parts():
    assert parts_for_miss_rate(0.05, 0.02) > 400
    # and it goes as one over the square of the precision
    assert parts_for_miss_rate(0.05, 0.01) == pytest.approx(
        4 * parts_for_miss_rate(0.05, 0.02), rel=0.01)


def test_seeing_no_escapes_is_weak_evidence():
    """The most common attribute study result, and the most over-read."""
    assert zero_escapes_bound(50) > 0.05
    assert zero_escapes_bound(300) < zero_escapes_bound(50)
    # the bound is exact, not an approximation: (1-conf) is the chance of
    # missing every one of n misses at exactly that rate
    p = zero_escapes_bound(50)
    assert (1 - p) ** 50 == pytest.approx(0.05, abs=1e-12)


def test_a_count_is_dearer_than_a_measurement():
    """Level 2 settled a variance with 10 parts x 3 operators x 3 trials = 90
    readings. This needs several hundred known-bad parts for one rate."""
    assert parts_for_miss_rate() > 4 * 90


# ------------------------------------------------------------ the simulation
def test_the_quadrature_agrees_with_a_simulation():
    """Independent check on the whole integration scheme.

    Draw parts, draw two noise terms, count. If the closed-form table and the
    counted one disagree by more than the sampling error, one of them is wrong.
    """
    rng = np.random.default_rng(606)
    n = 400_000
    truth = rng.normal(0.0, PART_SIGMA, n)
    r1 = truth + rng.normal(0.0, GAUGE_SIGMA, n)
    r2 = truth + rng.normal(0.0, GAUGE_SIGMA, n)
    good = np.abs(truth) <= HALF
    p1, p2 = np.abs(r1) <= HALF, np.abs(r2) <= HALF

    sim_eff = float(((good & p1) | (~good & ~p1)).mean())
    sim_agree = float((p1 == p2).mean())
    sim_miss = float((~good & p1).sum() / (~good).sum())

    assert CROSS["effectiveness"] == pytest.approx(sim_eff, abs=0.002)
    assert AGREE["agreement"] == pytest.approx(sim_agree, abs=0.002)
    assert CROSS["miss_rate"] == pytest.approx(sim_miss, abs=0.05)


# ---------------------------------------------------------- closing four holes
def test_kappa_uses_each_raters_own_marginal():
    """Sabotage 3 survived: this level's tables are symmetric, so using one
    rater's marginal twice is invisible in every number the page prints.

    kappa_from_table is a general function and has to be right off the diagonal
    too. Here the raters pass at different rates, so the chance term must be
    p1*p2 + (1-p1)*(1-p2) and nothing else.
    """
    # rater A passes 80 %, rater B passes 40 %, and they agree on 50 %
    n11, n10, n01, n00 = 0.30, 0.50, 0.10, 0.10
    k = kappa_from_table(n11, n10, n01, n00)
    p1, p2 = n11 + n10, n11 + n01
    assert p1 == pytest.approx(0.80) and p2 == pytest.approx(0.40)
    assert k["expected"] == pytest.approx(p1 * p2 + (1 - p1) * (1 - p2),
                                         abs=1e-12)
    # the symmetric mistake would give p1^2 + (1-p1)^2 = 0.68, not 0.44
    assert k["expected"] == pytest.approx(0.44, abs=1e-12)
    assert k["expected"] != pytest.approx(0.68, abs=1e-3)


def test_the_guard_band_cost_is_counted_in_parts_not_rates():
    """Sabotage 6 survived: a ratio of two rates is monotone in the same
    direction as a ratio of two counts, so ordering alone cannot tell them apart.

    What a plant loses is parts. Good parts outnumber bad ones by the base rate
    here - over seven hundred to one - so a cost quoted in rates understates the
    true exchange by exactly that factor.
    """
    base = cross_table()
    ratio = base["good"] / base["bad"]
    assert ratio > 500, "this process must be lopsided for the test to bite"
    rows = guard_band_curve(guards=(0.0, 2.0))
    row = rows[1]
    d_miss = base["miss_rate"] - row["miss_rate"]
    d_fa = row["false_alarm_rate"] - base["false_alarm_rate"]
    assert row["good_parts_lost_per_escape_saved"] == pytest.approx(
        (d_fa * base["good"]) / (d_miss * base["bad"]), rel=1e-12)
    # and it is emphatically not the bare ratio of rates
    assert row["good_parts_lost_per_escape_saved"] > 100 * (d_fa / d_miss)


def test_the_sample_size_depends_on_the_rate_being_estimated():
    """Sabotage 7 survived: substituting the worst case p=0.5 keeps every
    scaling relation intact and only changes the number, from 457 to 2401.

    p(1-p) is the variance of one Bernoulli trial. A rare event is cheaper to
    bound than a coin flip, and a formula that cannot see that is not the
    formula for a proportion.
    """
    at_half = parts_for_miss_rate(0.50, 0.02)
    at_five = parts_for_miss_rate(0.05, 0.02)
    at_one = parts_for_miss_rate(0.01, 0.02)
    assert at_half > at_five > at_one
    # p(1-p) at 0.5 is 0.25 against 0.0475 at 0.05: a factor of 5.26
    assert at_half / at_five == pytest.approx(0.25 / (0.05 * 0.95), rel=0.01)


def test_the_guard_band_moves_both_limits():
    """Sabotage 9 survived: tightening only the upper limit still reduces
    escapes and still costs good parts, so every monotonic check passes.

    A guard band is a band. On a symmetric process the two limits must remove
    equal probability, and a one-sided version breaks that at once.
    """
    from msalab.attribute import _pass_prob
    for guard in (1.0, 3.0):
        # a part the same distance outside each limit must be equally likely to
        # be passed, and equally so for a part inside each limit
        for d in (0.5, 2.0, 5.0):
            assert _pass_prob(HALF + d, guard=guard) == pytest.approx(
                _pass_prob(-HALF - d, guard=guard), abs=1e-12)
            assert _pass_prob(HALF - d, guard=guard) == pytest.approx(
                _pass_prob(-HALF + d, guard=guard), abs=1e-12)
        # and the pass window must be exactly 2*(HALF - guard) wide
        assert _pass_prob(0.0, gauge=1e-7, guard=guard) == pytest.approx(1.0,
                                                                        abs=1e-6)
        assert _pass_prob(HALF - guard + 0.01, gauge=1e-7,
                          guard=guard) == pytest.approx(0.0, abs=1e-6)
