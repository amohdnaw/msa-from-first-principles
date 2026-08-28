"""Level 3's claims.

One test here exists because of a specific failure on the SPC build: a sabotage
that inflated a variance component survived twenty-one tests, because the tests
checked sums of squares and percentages and those held by construction. The
numbers the decomposition *ends on* were unguarded.

So `test_the_components_invert_the_expected_mean_squares` is written first and on
purpose. The components are an algebraic inversion of the expected mean squares,
so feeding them back must reproduce those mean squares to floating point. Three
different mis-inversions fail it, and no tolerance-widening makes it pass.
"""
import math

import numpy as np
import pytest

from msalab.anova import (
    ANOVA_DRIFT_PCT, ANOVA_ZERO_BIAS_PCT, AT_WORST, AT_ZERO, BAD_INTERACTION,
    CLEAN, CLEAN_ANOVA, CLEAN_GAP_PCT, CLEAN_XBAR, D2_OPERATORS, D2_TRIALS,
    DIRTY, DIRTY_ANOVA, DIRTY_GAP_PCT, DIRTY_TRUTH, DIRTY_XBAR, F_INTER_CLEAN,
    F_INTER_DIRTY, IDENT_RESIDUAL, INTERACTION_SHARE, OPERATORS, PARTS,
    POOL_ALPHA, POOL_COST_PCT, POOLED_DIRTY, P_INTER_CLEAN, P_INTER_DIRTY,
    SIGMA_OPERATOR, SIGMA_REPEAT, SWEEP, TRIALS, XBAR_DRIFT_PCT, anova,
    average_and_range, compare, d2, rr_from_anova, study,
)


# ------------------------------------------------- the algebraic check, first
def test_the_components_invert_the_expected_mean_squares():
    """The check a percentage test cannot make.

    The components are defined by inverting

        E[MS_part]  = e + t*i + o*t*p
        E[MS_oper]  = e + t*i + parts*t*o
        E[MS_inter] = e + t*i
        E[MS_error] = e

    so substituting them back has to reproduce the mean squares exactly. This is
    algebraic rather than statistical: it holds on any data, at any study size,
    with no tolerance to loosen.
    """
    for interaction in (0.0, 1.9, 4.0):
        reads = study(interaction=interaction)["readings"]
        p, o, t = reads.shape
        a = anova(reads)
        v, ms = a["var_raw"], a["ms"]
        assert ms["repeat"] == pytest.approx(v["repeat"], rel=1e-12)
        assert ms["interaction"] == pytest.approx(
            v["repeat"] + t * v["interaction"], rel=1e-12)
        assert ms["operator"] == pytest.approx(
            v["repeat"] + t * v["interaction"] + p * t * v["operator"], rel=1e-12)
        assert ms["part"] == pytest.approx(
            v["repeat"] + t * v["interaction"] + o * t * v["part"], rel=1e-12)


# --------------------------------- claim 4: the identity is what makes it real
def test_the_sums_of_squares_add_to_the_total():
    for interaction in (0.0, 1.9, 4.0):
        a = anova(study(interaction=interaction)["readings"])
        ss = a["ss"]
        parts = ss["part"] + ss["operator"] + ss["interaction"] + ss["repeat"]
        assert parts == pytest.approx(ss["total"], rel=1e-12)


def test_the_seeded_identity_closes_to_floating_point():
    assert IDENT_RESIDUAL < 1e-8


def test_the_degrees_of_freedom_add_up_too():
    a = anova(study()["readings"])
    df = a["df"]
    assert df["part"] == PARTS - 1
    assert df["operator"] == OPERATORS - 1
    assert df["interaction"] == (PARTS - 1) * (OPERATORS - 1)
    assert df["repeat"] == PARTS * OPERATORS * (TRIALS - 1)
    total = PARTS * OPERATORS * TRIALS - 1
    assert sum(df.values()) == total


# ------------------------------- claim 3: an interaction needs replication
def test_without_replication_there_is_no_error_term_at_all():
    """One trial each and the interaction is unidentifiable, not just imprecise.

    With t = 1 the interaction and the residual occupy the same cells, so there
    is nothing left to test the interaction against. A method that reports an
    interaction from a single-trial study is reporting an artefact.
    """
    reads = study(trials=1)["readings"]
    a = anova(reads)
    assert a["df"]["repeat"] == 0
    assert not math.isfinite(a["f"]["interaction"]) or math.isnan(a["f"]["interaction"])


def test_an_interaction_is_a_difference_of_differences():
    """It survives removing the main effects, and nothing else does.

    Subtract each part's mean and each operator's mean and add the grand mean
    back: main effects vanish, the interaction does not. That is the definition,
    and it is why every cell has to be filled.
    """
    s = study(interaction=BAD_INTERACTION)
    reads = s["readings"]
    cell = reads.mean(axis=2)
    resid = (cell - cell.mean(axis=1, keepdims=True)
             - cell.mean(axis=0, keepdims=True) + cell.mean())
    # the residual pattern must track the injected interaction
    injected = s["interaction"]
    inj = (injected - injected.mean(axis=1, keepdims=True)
           - injected.mean(axis=0, keepdims=True) + injected.mean())
    corr = np.corrcoef(resid.ravel(), inj.ravel())[0, 1]
    assert corr > 0.75, f"the residual should be the interaction, r = {corr:.2f}"


# --------------- claim 2: average-and-range has no term for the interaction
def test_the_within_cell_range_cannot_see_the_interaction():
    """Why the omission happens, mechanically.

    The interaction is constant inside a part-operator cell, so a range taken
    inside that cell is blind to it. Repeatability comes out right; the gauge
    total comes out short by the whole interaction term.
    """
    a = average_and_range(study(interaction=0.0)["readings"])
    b = average_and_range(study(interaction=4.0)["readings"])
    assert a["ev"] == pytest.approx(b["ev"], rel=1e-12)


def test_average_and_range_understates_a_gauge_with_an_interaction():
    assert DIRTY_XBAR < DIRTY_ANOVA
    assert DIRTY_XBAR < DIRTY_TRUTH, "it flatters the gauge, it does not inflate it"
    assert DIRTY_GAP_PCT > 25


def test_anova_is_the_one_that_stays_near_the_truth_over_many_studies():
    """The claim belongs to the average, and only to the average.

    Asserting it on the seeded dirty study FAILS: ANOVA overshoots by 19 % there
    while average-and-range undershoots by 10. Averaged over three hundred
    studies per point, ANOVA's mean absolute error is a small fraction of
    average-and-range's. That is the real result and it is the only one the page
    is allowed to make.
    """
    anova_mae = sum(abs(r["anova_err"]) for r in SWEEP) / len(SWEEP)
    xbar_mae = sum(abs(r["xbar_err"]) for r in SWEEP) / len(SWEEP)
    assert anova_mae < xbar_mae / 4, f"{anova_mae:.1f} vs {xbar_mae:.1f}"
    assert INTERACTION_SHARE > 40


def test_on_one_dirty_study_anova_can_be_the_further_of_the_two():
    """Kept deliberately, like Level 1's and Level 2's honesty tests.

    If somebody reseeds until the single study agrees with the conclusion, this
    fails. The conclusion is about a direction over many studies; one study has
    enough noise to reverse the ranking.
    """
    assert abs(DIRTY["anova_err"]) > abs(DIRTY["xbar_err"]), (
        "this seed is chosen so the single study does NOT settle the question")
    assert DIRTY["anova_err"] > 0 > DIRTY["xbar_err"], (
        "and it reverses because ANOVA overshoots while the other undershoots")


def test_the_divergence_is_systematic_and_only_one_method_drifts():
    """The whole comparison, on 300 studies per point rather than one."""
    errs = [row["xbar_err"] for row in SWEEP]
    # average-and-range gets monotonically worse as the interaction grows
    assert errs == sorted(errs, reverse=True), f"not monotone: {errs}"
    assert XBAR_DRIFT_PCT > 8 * ANOVA_DRIFT_PCT
    assert AT_WORST["xbar_err"] < -35


def test_with_no_interaction_neither_method_is_systematically_wrong():
    assert abs(AT_ZERO["anova_err"]) < 10
    assert abs(AT_ZERO["xbar_err"]) < 10


def test_anova_has_its_own_downward_bias_and_it_is_named():
    """Honesty about the method being recommended.

    An operator component on two degrees of freedom, square-rooted, comes out
    low. ANOVA is not unbiased - it is not *systematically* wrong as the
    interaction grows, which is a different and weaker claim.
    """
    assert ANOVA_ZERO_BIAS_PCT < 0
    assert abs(ANOVA_ZERO_BIAS_PCT) > 2


def test_one_clean_study_does_not_show_the_methods_agreeing_exactly():
    """Third time this curriculum has met this trap; kept as a test."""
    assert CLEAN_GAP_PCT > 5, (
        "on one study the two methods differ by more than the page should claim")


# ------------------------------------- d2, derived and then checked in print
@pytest.mark.parametrize("n,published", [
    (2, 1.128), (3, 1.693), (4, 2.059), (5, 2.326), (10, 3.078),
])
def test_d2_reproduces_the_published_constants(n, published):
    """Average-and-range rests on these, so they have to be earned first."""
    assert d2(n) == pytest.approx(published, abs=4e-3)


def test_d2_is_simulated_and_not_a_lookup_table():
    """Closes a hole a sabotage found: swapping the simulation for the printed
    table passed all twenty-nine tests.

    The numbers would still have been right, and the site's one rule - every
    constant computed, nothing quoted - would have been quietly false. So the
    test asks a question only a simulation can answer: change the seed and the
    answer must change, while staying near the published value.
    """
    a = d2(3, reps=40_000, seed=101)
    b = d2(3, reps=40_000, seed=202)
    assert a != b, "a table ignores the seed; a simulation cannot"
    for v in (a, b):
        assert v == pytest.approx(1.693, abs=0.02)


def test_d2_answers_for_sizes_no_table_prints():
    """And it has to be defined where no printed table goes.

    A lookup with a default returns the same number for 22, 23 and 24, so strict
    monotonicity is the second thing a table cannot fake.
    """
    vals = [d2(n, reps=40_000, seed=5) for n in (22, 23, 24, 40)]
    assert vals == sorted(vals), f"d2 must increase with n: {vals}"
    assert len(set(vals)) == len(vals), "a table with a default repeats itself"
    assert 3.5 < vals[0] < 4.4


def test_d2_needs_a_range_to_take():
    with pytest.raises(ValueError):
        d2(1)


def test_d2_is_used_where_the_page_says_it_is():
    assert D2_TRIALS == pytest.approx(d2(TRIALS), rel=1e-12)
    assert D2_OPERATORS == pytest.approx(d2(OPERATORS), rel=1e-12)
    a = average_and_range(study()["readings"])
    cell_ranges = (study()["readings"].max(axis=2)
                   - study()["readings"].min(axis=2))
    assert a["ev"] == pytest.approx(cell_ranges.mean() / D2_TRIALS, rel=1e-12)


def test_average_and_range_carries_level_twos_correction():
    """Continuity: AV subtracts EV^2/(parts*trials), exactly as Level 2 derived,
    and can therefore hit the same zero boundary."""
    reads = study(operator=0.0, repeat=3.0)["readings"]
    a = average_and_range(reads)
    assert a["av"] == 0.0 or a["av_negative"] or a["av"] < 0.6


# ------------------------------------- claim 5: the test, and what pooling costs
def test_the_interaction_test_is_not_significant_on_a_clean_study():
    assert P_INTER_CLEAN > POOL_ALPHA
    assert F_INTER_CLEAN < 2.0


def test_the_interaction_test_fires_on_a_dirty_study():
    assert P_INTER_DIRTY < 0.01
    assert F_INTER_DIRTY > 5.0


def test_pooling_a_real_interaction_understates_the_gauge():
    assert POOLED_DIRTY["pooled"] is True
    assert POOLED_DIRTY["interaction"] == 0.0
    assert POOLED_DIRTY["gauge"] < DIRTY_ANOVA
    assert POOL_COST_PCT > 5


def test_pooling_conserves_the_sum_of_squares_it_folds():
    """Pooling is not deletion: the interaction SS joins the error SS and the
    degrees of freedom join too. Getting that wrong changes repeatability."""
    a = DIRTY["table"]
    pooled = rr_from_anova(a, pool=True)
    expected = ((a["ss"]["interaction"] + a["ss"]["repeat"])
                / (a["df"]["interaction"] + a["df"]["repeat"]))
    assert pooled["repeat"] == pytest.approx(expected, rel=1e-12)


def test_the_main_effects_are_tested_against_the_interaction():
    """A random-effects model tests both main effects against the interaction.

    Using the error term instead inflates every F, which is a common and quiet
    mistake: it makes an operator effect look significant when it is not.
    """
    a = anova(study(interaction=BAD_INTERACTION)["readings"])
    assert a["f"]["operator"] == pytest.approx(
        a["ms"]["operator"] / a["ms"]["interaction"], rel=1e-12)
    wrong = a["ms"]["operator"] / a["ms"]["repeat"]
    assert wrong > a["f"]["operator"], "the wrong denominator must inflate F"


# ---------------------------------------------- components may go negative
def test_a_component_can_come_out_negative_and_is_reported_as_zero():
    """The same boundary as Level 2, now in three places instead of one."""
    found = False
    for s in range(1, 40):
        a = anova(study(seed=s, operator=0.0, interaction=0.0)["readings"])
        if a["var_raw"]["operator"] < 0 or a["var_raw"]["interaction"] < 0:
            found = True
            assert a["var"]["operator"] >= 0 and a["var"]["interaction"] >= 0
    assert found, "with no operator or interaction effect, some study must hit it"


def test_the_gauge_never_comes_out_negative():
    for s in range(1, 25):
        rr = rr_from_anova(anova(study(seed=s, operator=0.0)["readings"]))
        assert rr["gauge"] >= 0
