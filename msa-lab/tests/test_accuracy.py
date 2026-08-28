"""Level 5's claims.

The one that matters most is claim 1, and it is exact rather than statistical:
every ratio the first four levels built is a function of standard deviations, and
adding a constant to every reading changes no standard deviation. So a gauge that
reads three microns high passes every gate in Level 4 unchanged to floating point
while the conformance decision gets four times worse.

Claim 3 is the one I did not expect: linearity does not merely hide from %GRR, it
*improves* it, because the gauge's own defect inflates the apparent part spread -
which is the denominator. The closed form and a simulation are checked against
each other, because a claim that surprising should not rest on one derivation.
"""
import math

import numpy as np
import pytest

from msalab.accuracy import (
    misclassification_simulated,
    APPARENT_INFLATION_PCT, BIAS, BIASED_MISS, BIASED_RATIOS, CLEAN_MISS,
    CLEAN_RATIOS, DRIFT, DRIFT_OVER_GAUGE, DRIFT_PCT_TOL, DRIFT_PER_MONTH,
    DRIFT_TOTAL, GAUGE_SIGMA, GRR_BY_MONTH, GRR_IS_CONSTANT, LINEARITY,
    LINEAR_RATIOS, MASTER_CI, MASTER_READS, MONTHS, MONTH_MASTER_NOTICES,
    RATIOS_UNCHANGED, READS_FOR_BIAS, READS_FOR_HALF, READS_FOR_TENTH,
    REPEAT_BY_MONTH, REPEAT_SPREAD, SCRAP_MULTIPLE, STUDY_IMPROVEMENT,
    bias_interval, drift_studies, linear_error, misclassification,
    ratios_with_bias, ratios_with_linearity, reads_to_detect,
)
from msalab.against_what import TOLERANCE, study_ratio, tolerance_ratio
from msalab.measurement import PART_SIGMA


# --------------------------------- claim 1: every ratio is blind to bias
def test_neither_ratio_moves_when_the_gauge_reads_high():
    """Exact, not approximate. There is nowhere for a bias to enter."""
    assert RATIOS_UNCHANGED
    assert BIASED_RATIOS["study"] == pytest.approx(CLEAN_RATIOS["study"], rel=1e-15)
    assert BIASED_RATIOS["tolerance"] == pytest.approx(
        CLEAN_RATIOS["tolerance"], rel=1e-15)


@pytest.mark.parametrize("bias", [0.5, 3.0, 12.0, 100.0])
def test_the_blindness_does_not_depend_on_how_big_the_bias_is(bias):
    r = ratios_with_bias(bias=bias)
    assert r["study"] == pytest.approx(CLEAN_RATIOS["study"], rel=1e-15)
    assert r["tolerance"] == pytest.approx(CLEAN_RATIOS["tolerance"], rel=1e-15)


def test_a_biased_gauge_scraps_far_more_good_parts():
    assert BIASED_MISS["good_rejected_pct"] > CLEAN_MISS["good_rejected_pct"]
    assert SCRAP_MULTIPLE > 3


def test_and_the_damage_is_one_sided_which_noise_never_is():
    """The signature of bias, and the reason it is worth its own level.

    An unbiased gauge scraps at both limits about equally. A biased one pushes
    essentially everything to one side, which is visible on a shop floor long
    before anyone computes a ratio.
    """
    assert 40 < CLEAN_MISS["rejected_at_upper_pct"] < 60
    assert BIASED_MISS["rejected_at_upper_pct"] > 90


def test_a_gauge_reading_low_pushes_the_other_way():
    low = misclassification(bias=-BIAS)
    assert low["rejected_at_lower_pct"] > 90


# ------------------------------- claim 2: it takes a reference and a sample
def test_an_interval_on_the_mean_error_finds_a_real_bias():
    assert MASTER_CI["detected"]
    assert MASTER_CI["low"] > 0
    assert MASTER_CI["mean"] == pytest.approx(BIAS, abs=1.2)


def test_and_reports_nothing_when_there_is_nothing():
    rng = np.random.default_rng(9)
    found = 0
    for _ in range(200):
        r = rng.normal(0.0, GAUGE_SIGMA, MASTER_READS)
        found += bias_interval(r)["detected"]
    # a 95 % interval should cry wolf about one time in twenty
    assert found < 200 * 0.12, f"{found}/200 false detections"


def test_the_interval_uses_the_t_quantile_and_not_1_96():
    """A sabotage replaced the t quantile with a flat 1.96 and passed all 27.

    At ten readings t is 2.262, so 1.96 gives an interval 13 % too narrow and
    cries wolf about twice as often as it should. The false-detection test alone
    was too loose to notice, so the half-width is now checked against the
    quantile directly.
    """
    from scipy import stats as _st
    rng = np.random.default_rng(41)
    r = rng.normal(0.0, GAUGE_SIGMA, MASTER_READS)
    ci = bias_interval(r)
    se = float(r.std(ddof=1) / math.sqrt(MASTER_READS))
    t_exact = float(_st.t.ppf(0.975, MASTER_READS - 1))
    assert ci["half_width"] == pytest.approx(t_exact * se, rel=1e-12)
    assert t_exact == pytest.approx(2.262, abs=0.001)
    assert ci["half_width"] > 1.96 * se, "a normal quantile would be too narrow"


def test_the_interval_widens_as_the_readings_get_fewer():
    """Another way the t quantile shows itself: it is not a constant."""
    rng = np.random.default_rng(42)
    big = bias_interval(rng.normal(0.0, GAUGE_SIGMA, 200))
    small = bias_interval(rng.normal(0.0, GAUGE_SIGMA, 4))
    assert small["half_width"] > big["half_width"] * 2


def test_an_interval_needs_more_than_one_reading():
    with pytest.raises(ValueError):
        bias_interval(np.array([1.0]))


def test_the_sample_size_grows_as_the_square_of_the_precision_wanted():
    """Halving the bias you want to catch roughly quadruples the readings."""
    assert READS_FOR_BIAS == 8
    assert READS_FOR_HALF == pytest.approx(22, abs=2)
    assert READS_FOR_TENTH == pytest.approx(498, abs=20)
    assert READS_FOR_HALF / READS_FOR_BIAS == pytest.approx(4, rel=0.35)


def test_a_zero_bias_is_never_detectable():
    with pytest.raises(ValueError):
        reads_to_detect(bias=0.0)


def test_repeating_one_unknown_part_can_never_find_bias():
    """The structural point: without a reference there is no bias information.

    Two gauges, one unbiased and one three microns high, measuring the same
    unknown part. The spread of the readings is identical; only their level
    differs, and 'level' means nothing without something to compare it to.
    """
    rng = np.random.default_rng(3)
    part = 7.31
    a = part + rng.normal(0.0, GAUGE_SIGMA, 400)
    rng = np.random.default_rng(3)
    b = part + BIAS + rng.normal(0.0, GAUGE_SIGMA, 400)
    assert a.std(ddof=1) == pytest.approx(b.std(ddof=1), rel=1e-12)
    assert b.mean() - a.mean() == pytest.approx(BIAS, rel=1e-12)


# ------------------------- claim 3: linearity improves the study ratio
def test_linearity_makes_the_study_ratio_better_not_worse():
    assert LINEAR_RATIOS["study"] < CLEAN_RATIOS["study"]
    assert STUDY_IMPROVEMENT > 3.0


def test_it_does_so_by_inflating_the_apparent_part_spread():
    assert LINEAR_RATIOS["apparent_part"] > PART_SIGMA
    assert APPARENT_INFLATION_PCT == pytest.approx(LINEARITY * 100, abs=0.01)


def test_the_closed_form_matches_a_simulation():
    """A claim this counter-intuitive should not rest on one derivation."""
    rng = np.random.default_rng(1234)
    n = 400_000
    truth = rng.normal(0.0, PART_SIGMA, n)
    read = truth + linear_error(truth) + rng.normal(0.0, GAUGE_SIGMA, n)
    simulated = GAUGE_SIGMA / read.std(ddof=1) * 100
    assert simulated == pytest.approx(LINEAR_RATIOS["study"], rel=0.01)


def test_the_tolerance_ratio_is_untouched_by_linearity_too():
    assert LINEAR_RATIOS["tolerance"] == pytest.approx(
        CLEAN_RATIOS["tolerance"], rel=1e-15)


def test_a_steeper_slope_flatters_the_gauge_further():
    ratios = [ratios_with_linearity(slope=s)["study"] for s in (0.0, 0.1, 0.3, 0.6)]
    assert ratios == sorted(ratios, reverse=True)


def test_linear_error_is_zero_at_the_centre_of_the_range():
    assert linear_error(np.array([0.0]))[0] == pytest.approx(0.0)
    assert linear_error(np.array([10.0]))[0] == pytest.approx(LINEARITY * 10)


# --------------------- claim 4: no single study can see a drift
def test_every_month_reports_the_same_grr():
    """The bias is constant inside one study, so nothing variance-based moves."""
    assert GRR_IS_CONSTANT
    assert len(set(round(g, 12) for g in GRR_BY_MONTH)) == 1


def test_and_the_repeatability_estimate_barely_moves_either():
    assert REPEAT_SPREAD < 0.4
    for r in REPEAT_BY_MONTH:
        assert r == pytest.approx(GAUGE_SIGMA, rel=0.12)


def test_meanwhile_the_gauge_has_moved_a_long_way():
    assert DRIFT_TOTAL == pytest.approx(DRIFT_PER_MONTH * (MONTHS - 1), rel=1e-12)
    assert DRIFT_OVER_GAUGE > 2.5
    assert DRIFT_PCT_TOL > 15


def test_a_master_catches_it_eventually_but_not_at_once():
    assert MONTH_MASTER_NOTICES is not None
    assert MONTH_MASTER_NOTICES >= 1, "month zero has no bias to find"
    assert DRIFT["months_undetected"] >= 1


def test_the_drift_happens_between_studies_and_not_inside_one():
    """A sabotage turned the constant monthly offset into a ramp across the ten
    readings of each study, and passed all 27 tests.

    That is a different physical situation: a gauge drifting DURING a study
    inflates its repeatability, and the level's claim - that no single study can
    see the drift - would be false. The within-month spread has to stay at the
    gauge's own sigma every month, however far the bias has moved.
    """
    d = drift_studies(per_month=2.0, months=10, reads=40)
    for m, sd in enumerate(d["within_sd_by_month"]):
        assert sd == pytest.approx(GAUGE_SIGMA, rel=0.35), (
            f"month {m}: within-study spread {sd:.3f} against a gauge of "
            f"{GAUGE_SIGMA:.3f} - the drift is leaking into the study")
    spread = max(d["within_sd_by_month"]) - min(d["within_sd_by_month"])
    assert spread < GAUGE_SIGMA * 0.8, (
        "the within-study spread must not grow with the accumulated bias")


def test_a_faster_drift_is_caught_sooner():
    slow = drift_studies(per_month=0.2)
    fast = drift_studies(per_month=2.0)
    assert fast["months_before_a_master_notices"] <= slow["months_before_a_master_notices"]
    assert fast["total_drift"] > slow["total_drift"]


def test_no_drift_means_no_detections_beyond_chance():
    flat = drift_studies(per_month=0.0)
    assert flat["total_drift"] == 0.0
    assert flat["months_undetected"] >= MONTHS - 2


# ------------------------------------- the summary claim, as arithmetic
def test_none_of_the_three_defects_appears_in_either_ratio():
    """Level 5 in one test: all three are invisible to Level 4's numbers.

    Bias and stability change no variance at all. Linearity changes one, and in
    the direction that helps.
    """
    base = study_ratio(GAUGE_SIGMA, PART_SIGMA)
    assert ratios_with_bias(bias=9.0)["study"] == pytest.approx(base, rel=1e-15)
    assert drift_studies(per_month=3.0) and GRR_IS_CONSTANT
    assert ratios_with_linearity(slope=0.4)["study"] < base


def test_the_unbiased_split_is_exactly_even():
    """Not 'about half' - exactly half, because the integrand is symmetric.

    The simulated version this replaced reported 51.7 %, and the level's claim is
    that bias makes the split one-sided. A claim about a departure from symmetry
    is worth nothing if the symmetric case is only symmetric to two figures.
    """
    m = misclassification(bias=0.0)
    assert m["rejected_at_upper_pct"] == pytest.approx(50.0, abs=1e-9)
    assert m["rejected_at_lower_pct"] == pytest.approx(50.0, abs=1e-9)


def test_the_quadrature_agrees_with_the_simulation():
    """The exact computation against four hundred thousand simulated parts.

    This is the test that earns the switch from sampling to quadrature: if they
    disagree by more than the simulation's own standard error, one of them is
    wrong. At n=400k the standard error on a 0.25 % rate is about 0.008 %.
    """
    for bias in (0.0, 1.5, 3.0):
        exact = misclassification(bias=bias)
        sim = misclassification_simulated(bias=bias, n=400_000)
        assert exact["good_rejected_pct"] == pytest.approx(
            sim["good_rejected_pct"], abs=0.05)
        assert exact["rejected_at_upper_pct"] == pytest.approx(
            sim["rejected_at_upper_pct"], abs=1.5)


def test_the_quadrature_converges():
    """Halving the step must not move the answer at the printed precision.

    A quadrature that is not converged is a lookup table with extra steps.
    """
    from msalab.accuracy import _Phi, _phi, _simpson
    coarse = _simpson(lambda x: _phi(x, 4.7), -15.0, 15.0, 500)
    fine = _simpson(lambda x: _phi(x, 4.7), -15.0, 15.0, 4000)
    exact = 2.0 * _Phi(15.0 / 4.7) - 1.0
    assert fine == pytest.approx(exact, abs=1e-12)
    assert abs(fine - exact) <= abs(coarse - exact)
