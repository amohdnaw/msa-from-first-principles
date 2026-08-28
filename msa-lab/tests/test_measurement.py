"""Level 1's claims.

Each test is one sentence the level says out loud. If a test can be deleted
without some claim on screen becoming unsupported, the test is decoration.

The interesting ones here are the honesty tests. This level's headline - that
measurement error widens the spread you observe - is a 4.3 % effect that a
40-part study cannot resolve, and the seeded study in the library reports the
widening in the *wrong direction*. Two tests pin that on purpose, because the
temptation is to reseed until the picture looks like the claim.
"""
import math

import numpy as np
import pytest

from msalab.measurement import (
    AVERAGE_TABLE, C4_PARTS, C4_SHORTFALL_PCT, C4_WITHIN, EXPECTED_OBSERVED,
    EXPECTED_TRUTH, EXPECTED_WITHIN, FLOOR, GAUGE_SIGMA, INFLATION_TABLE,
    ONE_PART_RANGE, ONE_PART_SD, OBSERVED_EXACT, OBSERVED_SIM, PART_SIGMA,
    PARTS, RATIO_FOR_10PCT, RATIO_FOR_1PCT, REPEATS, REPL, REPL_OBSERVED,
    REPL_TRUTH, REPL_WITHIN, REPEATS_FOR_1PCT, SE_OBSERVED_PCT, SE_WITHIN_PCT,
    STUDY, WIDENING_PCT, WITHIN_DF, WRONG_DIRECTION_PCT, averaging_floor, c4,
    inflation, observed_sigma, population, ratio_for_inflation,
    repeats_for_fraction, study,
)


# ---------------------------------------------------- claim 1: variances add
def test_the_observed_spread_is_the_quadrature_sum():
    assert observed_sigma(3.0, 4.0) == pytest.approx(5.0, rel=1e-12)


def test_standard_deviations_do_not_add():
    """The whole level turns on this. 4.7 + 1.4 is 6.1; the answer is 4.90."""
    assert observed_sigma() == pytest.approx(4.90408, abs=1e-5)
    assert observed_sigma() < PART_SIGMA + GAUGE_SIGMA


def test_a_gauge_can_only_ever_widen():
    """A measurement process cannot make the observed spread narrower."""
    for gauge in (0.01, 0.5, 1.4, 5.0, 50.0):
        assert observed_sigma(PART_SIGMA, gauge) > PART_SIGMA


def test_a_perfect_gauge_shows_the_parts_exactly():
    assert observed_sigma(PART_SIGMA, 0.0) == pytest.approx(PART_SIGMA, rel=1e-12)


# ------------------------------------- claim 2: one part IS a distribution
def test_one_part_measured_repeatedly_has_a_spread():
    """A single bore has one size. Two hundred readings of it do not."""
    assert ONE_PART_SD == pytest.approx(GAUGE_SIGMA, rel=0.12)
    assert ONE_PART_RANGE > 4 * GAUGE_SIGMA


def test_the_within_part_scatter_estimates_the_gauge_and_not_the_parts():
    """The load-bearing property: it does not depend on the part spread at all.

    This is why gauge error is estimated by repeating on one part rather than by
    comparing histograms, and it is the sentence Level 2 starts from.
    """
    wide = study(part_sigma=PART_SIGMA * 10)
    assert wide["sd_within"] == pytest.approx(STUDY["sd_within"], rel=1e-12)


# ------------------------------- claim 3: cheap at first, expensive later
def test_the_inflation_table_is_the_quadrature_law():
    for ratio, pct in INFLATION_TABLE:
        assert pct == pytest.approx((math.sqrt(1 + ratio ** 2) - 1) * 100, rel=1e-12)


def test_a_gauge_at_thirty_percent_costs_four_percent():
    """The number the level leads with."""
    assert dict(INFLATION_TABLE)[0.3] == pytest.approx(4.4031, abs=1e-4)


def test_a_gauge_as_big_as_the_parts_costs_forty_one_percent():
    assert dict(INFLATION_TABLE)[1.0] == pytest.approx((math.sqrt(2) - 1) * 100, rel=1e-12)


def test_the_inverse_is_the_surprising_direction():
    """Nearly half the part spread buys only ten percent of widening."""
    assert RATIO_FOR_10PCT == pytest.approx(0.45826, abs=1e-5)
    assert RATIO_FOR_1PCT == pytest.approx(0.14178, abs=1e-5)
    assert inflation(RATIO_FOR_10PCT) == pytest.approx(1.10, rel=1e-12)


def test_a_gauge_cannot_narrow_the_spread_by_request():
    with pytest.raises(ValueError):
        ratio_for_inflation(0.9)


# ----------------------------------------- claim 4: averaging has a floor
def test_averaging_divides_the_measurement_variance_and_nothing_else():
    assert averaging_floor(4) == pytest.approx(
        math.sqrt(PART_SIGMA ** 2 + GAUGE_SIGMA ** 2 / 4), rel=1e-12)


def test_the_floor_is_the_part_spread_and_is_never_reached():
    prev = math.inf
    for m, sd, _ in AVERAGE_TABLE:
        assert sd > FLOOR, "averaging cannot get under the part spread"
        assert sd < prev, "more repeats must not make it worse"
        prev = sd
    assert averaging_floor(10_000) == pytest.approx(FLOOR, abs=1e-3)


def test_the_improvement_goes_as_one_over_m_under_a_root():
    """Doubling the repeats does not halve anything, which is the point."""
    excess = lambda m: averaging_floor(m) - FLOOR          # noqa: E731
    assert excess(2) / excess(1) == pytest.approx(0.504, abs=0.01)


def test_reaching_one_percent_above_the_floor_needs_five_repeats():
    assert REPEATS_FOR_1PCT == 5
    assert averaging_floor(5) <= FLOOR * 1.01
    assert averaging_floor(4) > FLOOR * 1.01


def test_averaging_zero_times_is_not_a_thing():
    with pytest.raises(ValueError):
        averaging_floor(0)


# ------------------------------------------- the honesty tests, on purpose
def test_one_study_of_forty_parts_reports_the_wrong_direction():
    """Kept deliberately. The seeded study contradicts the level's headline.

    Its observed spread is NARROWER than the true part spread, which the
    variance law forbids in expectation. That is sampling error, not a bug, and
    reseeding until the picture agreed with the claim would be the dishonest fix.
    """
    assert OBSERVED_SIM < PART_SIGMA
    assert OBSERVED_SIM < OBSERVED_EXACT


def test_the_sampling_error_is_larger_than_the_effect():
    """Why the above happens, as a number: 11 % of noise against 4.3 % of signal."""
    assert SE_OBSERVED_PCT > 2 * WIDENING_PCT
    assert SE_OBSERVED_PCT == pytest.approx(100 / math.sqrt(2 * (PARTS - 1)), rel=0.08)


def test_one_study_points_the_wrong_way_about_forty_percent_of_the_time():
    assert 35 < WRONG_DIRECTION_PCT < 45


def test_the_gauge_estimate_is_the_precise_one():
    """80 degrees of freedom on the gauge against 39 on the observed spread."""
    assert WITHIN_DF == PARTS * (REPEATS - 1) == 80
    assert SE_WITHIN_PCT < SE_OBSERVED_PCT / 1.3


# ----------------------------------- c4: derived, then checked against print
@pytest.mark.parametrize("n,published", [
    (2, 0.7979), (3, 0.8862), (4, 0.9213), (5, 0.9400),
    (10, 0.9727), (25, 0.9896),
])
def test_c4_reproduces_the_published_constants(n, published):
    """The library has to earn the constant before anything rests on it."""
    assert c4(n) == pytest.approx(published, abs=5e-5)


def test_c4_rises_towards_one_and_never_reaches_it():
    prev = 0.0
    for n in (2, 3, 5, 10, 40, 200, 5000):
        assert prev < c4(n) < 1.0
        prev = c4(n)


def test_c4_needs_two_observations():
    with pytest.raises(ValueError):
        c4(1)


def test_the_replication_matches_what_s_actually_estimates():
    """The tight one.

    Averaged over four thousand studies the estimates sit on c4 * sigma, not on
    sigma. Checking against sigma would need a 1 % tolerance - wider than the
    whole effect this level teaches - so the check would pass while the maths
    was wrong. Against c4 * sigma it holds to four significant figures.
    """
    assert REPL_OBSERVED == pytest.approx(EXPECTED_OBSERVED, rel=2e-3)
    assert REPL_TRUTH == pytest.approx(EXPECTED_TRUTH, rel=2e-3)
    assert REPL_WITHIN == pytest.approx(EXPECTED_WITHIN, rel=2e-3)


def test_the_bias_is_the_whole_apparent_shortfall():
    """0.64 % of construction, not of chance."""
    assert C4_SHORTFALL_PCT == pytest.approx(0.639, abs=0.01)
    naive_gap = abs(REPL_OBSERVED - OBSERVED_EXACT) / OBSERVED_EXACT * 100
    c4_gap = abs(REPL_OBSERVED - EXPECTED_OBSERVED) / EXPECTED_OBSERVED * 100
    assert naive_gap > 20 * c4_gap, "c4 must explain essentially all of it"


def test_the_within_bias_uses_its_own_degrees_of_freedom():
    """A real trap: the within estimate pools 80 df, so its c4 is not c4(40)."""
    assert C4_WITHIN == pytest.approx(c4(WITHIN_DF + 1), rel=1e-12)
    assert C4_WITHIN > C4_PARTS


# -------------------------------------------------- the drawable population
def test_the_population_is_large_enough_to_draw_the_law():
    """The figure must not be a 40-part study, or it claims what it cannot show."""
    pop = population()
    assert pop["n"] >= 2000
    obs = pop["observed"].std(ddof=1)
    tru = pop["truth"].std(ddof=1)
    assert obs > tru, "at this n the widening must be visible"
    assert obs / tru == pytest.approx(OBSERVED_EXACT / PART_SIGMA, rel=0.03)


def test_the_population_observation_is_the_truth_plus_error():
    pop = population()
    residual = pop["observed"] - pop["truth"]
    assert residual.std(ddof=1) == pytest.approx(GAUGE_SIGMA, rel=0.05)
    assert abs(residual.mean()) < 0.1 * GAUGE_SIGMA


# ------------------------------------------------------- the study structure
def test_the_study_has_the_shape_the_page_describes():
    assert STUDY["readings"].shape == (PARTS, REPEATS)
    assert STUDY["truth"].shape == (PARTS,)


def test_averaging_the_repeats_narrows_what_you_see():
    """Claim 4, inside the seeded study rather than in the closed form."""
    assert STUDY["sd_of_means"] < STUDY["sd_observed"]


def test_every_reading_is_its_part_plus_an_error():
    err = STUDY["readings"] - STUDY["truth"][:, None]
    assert err.std(ddof=1) == pytest.approx(GAUGE_SIGMA, rel=0.15)
    assert np.abs(err.mean()) < 0.25 * GAUGE_SIGMA
