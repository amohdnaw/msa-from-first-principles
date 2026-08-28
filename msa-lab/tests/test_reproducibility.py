"""Level 2's claims.

The interesting ones are 3 and 4, which say a standard R&R study reports the
operator term wrong in both directions at once: too high if you take the operator
spread at face value, too low once the correction is clamped at zero. Both are
pinned here, and so is the fact that a single three-operator study cannot show
either - because that is the trap this level walked into on its first run.
"""
import math

import numpy as np
import pytest

from msalab.measurement import PART_SIGMA, c4
from msalab.reproducibility import (
    C4_REPEAT, C4_REPRODUCE, CLAMPED_UNDER_PCT, CORRECTED_MEAN, FIX_RATIO,
    GAUGE_EST, GAUGE_EXACT, HALVE_REPEAT_PCT, HALVE_REPRODUCE_PCT, NAIVE_MEAN,
    NAIVE_OVER_PCT, NEGATIVE_PCT, NOISY_BORROWED_PCT, NOISY_CORRECTED,
    NOISY_EXPECTED_NAIVE, NOISY_INFLATION, NOISY_NAIVE, NOISY_READS,
    NOISY_REPEAT,
    NOISY_REPRODUCE, OPERATORS, PARTS, READS, REPEAT_DF, REPEAT_EST,
    REPEAT_ERR_PCT, REPRODUCE_DF, REPRODUCE_ERR_PCT, REPRODUCE_EST,
    SIGMA_REPEAT, SIGMA_REPRODUCE, TRIALS, expected_naive, fix_value,
    gauge_sigma, negative_rate, operator_mean_spread, relative_error,
    repeatability, reproducibility, reproducibility_df, study,
)


# ---------------------------------- claim 1: the same law, one level down
def test_the_two_terms_add_in_quadrature_to_the_gauge_term():
    assert gauge_sigma(3.0, 4.0) == pytest.approx(5.0, rel=1e-12)
    assert gauge_sigma() == pytest.approx(
        math.sqrt(SIGMA_REPEAT ** 2 + SIGMA_REPRODUCE ** 2), rel=1e-12)


def test_the_study_recovers_both_terms():
    assert REPEAT_EST == pytest.approx(SIGMA_REPEAT, rel=0.15)
    assert REPRODUCE_EST == pytest.approx(SIGMA_REPRODUCE, rel=0.30)
    assert GAUGE_EST == pytest.approx(GAUGE_EXACT, rel=0.05)


def test_reproducibility_is_an_offset_that_persists_across_parts():
    """The modelling point, and the one that is easy to get wrong.

    An operator effect that were redrawn per reading would be repeatability
    wearing a different name. Removing each operator's own mean must therefore
    leave the repeatability behind, unchanged.
    """
    s = study(reproduce=0.0)
    assert repeatability(s["readings"]) == pytest.approx(
        repeatability(study()["readings"]), rel=1e-12), (
        "the operator effect must not touch the within-cell scatter")


def test_repeatability_does_not_depend_on_the_parts_or_the_operators():
    """It is the instrument talking to itself, which is why it is trustworthy."""
    base = repeatability(study()["readings"])
    assert repeatability(study(part_sigma=PART_SIGMA * 8)["readings"]) == \
        pytest.approx(base, rel=1e-12)
    assert repeatability(study(reproduce=SIGMA_REPRODUCE * 6)["readings"]) == \
        pytest.approx(base, rel=1e-12)


# ------------------------------- claim 2: the fixes are not interchangeable
def test_halving_the_bigger_term_buys_much_more():
    assert HALVE_REPRODUCE_PCT > HALVE_REPEAT_PCT
    assert FIX_RATIO == pytest.approx(3.74, abs=0.05)
    assert HALVE_REPEAT_PCT == pytest.approx(9.27, abs=0.02)
    assert HALVE_REPRODUCE_PCT == pytest.approx(34.66, abs=0.02)


def test_the_asymmetry_reverses_when_the_terms_do():
    """It is not a fact about reproducibility, it is a fact about which is bigger."""
    a = fix_value("repeat", repeat=3.0, reproduce=0.5)
    b = fix_value("reproduce", repeat=3.0, reproduce=0.5)
    assert a > b


def test_improving_a_term_to_nothing_cannot_beat_the_other_term():
    assert gauge_sigma(0.0, SIGMA_REPRODUCE) == pytest.approx(SIGMA_REPRODUCE)
    assert fix_value("repeat", factor=0.0) < 100.0


def test_fix_value_rejects_an_unknown_target():
    with pytest.raises(ValueError):
        fix_value("operator")


# ------------------ claim 3: the operator spread is not reproducibility
def test_the_naive_estimator_carries_repeatability_by_construction():
    """The exact expectation, which is where the claim lives."""
    assert expected_naive(3.0, 0.4, parts=10, trials=3) == pytest.approx(
        math.sqrt(0.4 ** 2 + 9.0 / 30), rel=1e-12)
    assert NOISY_EXPECTED_NAIVE == pytest.approx(0.67823, abs=1e-5)
    assert NOISY_INFLATION == pytest.approx(69.6, abs=0.5)


def test_most_of_the_naive_variance_is_not_the_operators():
    assert NOISY_BORROWED_PCT == pytest.approx(65.2, abs=0.5)


def test_the_borrowed_variance_shrinks_with_the_study_size():
    """It is repeat^2/(parts*trials), so a bigger study borrows less."""
    small = expected_naive(3.0, 0.4, parts=5, trials=2)
    big = expected_naive(3.0, 0.4, parts=40, trials=3)
    assert small > big > 0.4


def test_one_three_operator_study_cannot_show_the_direction():
    """Kept deliberately: the seeded study lands BELOW the truth.

    This is the same shape as Level 1's honesty test. The first run of the module
    printed "overstates by -35 %" because it was reading one study, and the fix
    was to state the expectation rather than to reseed until the study agreed.
    """
    assert NOISY_NAIVE < NOISY_REPRODUCE, (
        "this seed is chosen to contradict the naive reading of claim 3")
    assert REPRODUCE_DF == 2


def test_averaged_over_many_studies_the_naive_estimator_does_overstate():
    assert NAIVE_OVER_PCT == pytest.approx(51, abs=4)
    assert NAIVE_MEAN > NOISY_REPRODUCE


def test_the_naive_mean_sits_on_c4_times_the_expectation():
    """Level 1's bias factor, still exactly in force one level down.

    With three operators c4 is 0.886, so the mean of s is well below sigma. This
    ties the two levels together arithmetically rather than by assertion, and it
    is why the check above uses a 4-point tolerance rather than a loose one.
    """
    assert NAIVE_MEAN == pytest.approx(
        NOISY_EXPECTED_NAIVE * c4(OPERATORS), rel=0.03)


# ------------------------------- claim 4: the boundary, and its asymmetry
def test_the_correction_goes_negative_often_on_a_noisy_gauge():
    assert 40 < NEGATIVE_PCT < 55


def test_it_almost_never_goes_negative_when_the_operator_term_is_real():
    r = negative_rate(n=600, repeat=SIGMA_REPEAT, reproduce=SIGMA_REPRODUCE)
    assert r["negative_fraction"] < 0.02, (
        "a genuine operator effect should not hit the boundary")


def test_clamping_at_zero_biases_the_estimate_downwards():
    """The second half of the finding, and the part nobody says out loud.

    Reporting a negative variance as zero is a one-sided truncation. So the
    uncorrected number runs high and the corrected one runs low, on the same
    study, and neither is the answer.
    """
    assert CORRECTED_MEAN < NOISY_REPRODUCE
    assert CLAMPED_UNDER_PCT == pytest.approx(20, abs=5)
    assert NAIVE_OVER_PCT > 0 > -CLAMPED_UNDER_PCT


def test_the_unclamped_value_is_available_for_counting():
    """The clamp must be optional, or the negative rate cannot be measured."""
    raw = [reproducibility(study(seed=s, repeat=NOISY_REPEAT,
                                 reproduce=NOISY_REPRODUCE)["readings"],
                           clamp=False)
           for s in range(1, 60)]
    assert any(v < 0 for v in raw), "clamp=False must expose the boundary"
    assert all(reproducibility(study(seed=s, repeat=NOISY_REPEAT,
                                     reproduce=NOISY_REPRODUCE)["readings"]) >= 0
               for s in range(1, 60)), "clamped must never be negative"


def test_the_correction_is_subtracted_not_divided():
    """A sabotage-shaped test.

    Dividing by (parts*trials) instead of subtracting repeat^2/(parts*trials)
    happens to look plausible and gives a number of the right order. It cannot
    reproduce the identity, and it can never go negative - which is exactly why
    the negative rate above is load-bearing.
    """
    reads = NOISY_READS
    naive_var = operator_mean_spread(reads) ** 2
    rep_var = repeatability(reads) ** 2
    expected = naive_var - rep_var / (PARTS * TRIALS)
    got = reproducibility(reads, clamp=False)
    got_var = got ** 2 if got >= 0 else -(got ** 2)
    assert got_var == pytest.approx(expected, rel=1e-12)


# ------------------------------------- claim 5: two degrees of freedom
def test_three_operators_give_two_degrees_of_freedom():
    assert reproducibility_df(3) == 2
    assert REPRODUCE_DF == OPERATORS - 1
    assert REPEAT_DF == PARTS * OPERATORS * (TRIALS - 1) == 60


def test_the_operator_term_is_estimated_thirty_times_worse():
    assert REPRODUCE_ERR_PCT == pytest.approx(50.0, abs=0.1)
    assert REPEAT_ERR_PCT == pytest.approx(9.13, abs=0.05)
    assert REPRODUCE_ERR_PCT / REPEAT_ERR_PCT == pytest.approx(5.48, abs=0.05)


def test_relative_error_needs_a_degree_of_freedom():
    with pytest.raises(ValueError):
        relative_error(0)


def test_the_two_bias_factors_differ_because_the_df_do():
    assert C4_REPRODUCE == pytest.approx(c4(OPERATORS), rel=1e-12)
    assert C4_REPEAT > C4_REPRODUCE
    assert C4_REPRODUCE == pytest.approx(0.8862, abs=5e-5)


# --------------------------------------------------- the study's own shape
def test_the_study_has_the_shape_the_page_describes():
    assert READS.shape == (PARTS, OPERATORS, TRIALS) == (10, 3, 3)


def test_every_reading_is_part_plus_operator_plus_noise():
    s = study()
    residual = (s["readings"] - s["truth"][:, None, None]
                - s["op_effect"][None, :, None])
    assert residual.std(ddof=1) == pytest.approx(SIGMA_REPEAT, rel=0.15)
    assert abs(float(np.mean(residual))) < 0.2 * SIGMA_REPEAT
