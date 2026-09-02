"""Level 4's transfer decisions.

The level's claim is that a verdict is not a property of a gauge. The mastery
bank has to survive that claim rather than restate it, so these tests check the
chain link by link: the job picks the denominator, the denominator picks the
ratio, the ratio lands in an AIAG band, and only then is there an action.

Two rules are load-bearing here and neither is a formatting preference.

`deciding_field` has to be earned. A case may only claim `Decision job` if
answering with the other denominator would have produced a different action, and
it may only claim `AIAG band` if both denominators agree and the action really
does change when the ratio crosses the nearest gate. Without those two
counterfactuals the field is decoration.

`improve` is a next action, not a verdict. `against_what.verdict` still returns
the neutral `conditional` for the same percentage, and the tests hold both
readings of one number at once on purpose.
"""
import json
import re

import pytest

from msalab import against_what
from msalab.against_what import ACCEPT_PCT, GAUGE_SIGMA, REJECT_PCT, verdict
from msalab.level04_mastery import (
    ACTIONS, BAND_LABELS, CASE_SEEDS, DECIDING_FIELDS, DECISION_JOBS,
    DENOMINATORS, PRINTED_DP, action_for_ratio, band_label_for_ratio,
    challenge_bank, challenge_case, denominator_for_job,
)

BANK = challenge_bank()

#: Identifiers that exist in the real world and must never reach a learner.
REAL_IDENTIFIERS = ("ICOS", "BTMMN", "Nikon", "OM-X")


# ---------------------------------------------- the two gates from the plan
def test_job_selects_the_denominator():
    sort_case = challenge_case(CASE_SEEDS[0])
    conformity_case = challenge_case(CASE_SEEDS[1])
    assert sort_case["answer"]["denominator"] == "Study variation"
    assert conformity_case["answer"]["denominator"] == "Tolerance"


def test_actions_follow_the_contract_bands():
    assert action_for_ratio(10.0) == "use"
    assert action_for_ratio(10.01) == "improve"
    assert action_for_ratio(30.0) == "improve"
    assert action_for_ratio(30.01) == "replace"


# --------------------------------------------------- the contract vocabulary
def test_the_learner_visible_words_are_the_contract_words():
    """These strings are the contract, so they are compared literally."""
    assert DENOMINATORS == ("Study variation", "Tolerance")
    assert ACTIONS == ("use", "improve", "replace")
    assert DECIDING_FIELDS == ("Decision job", "Chosen denominator",
                               "Computed %GRR", "AIAG band")
    assert DECISION_JOBS == ("sort process populations",
                             "judge drawing conformance")


def test_the_two_jobs_map_to_the_two_denominators():
    assert denominator_for_job("sort process populations") == "Study variation"
    assert denominator_for_job("judge drawing conformance") == "Tolerance"


def test_an_unknown_job_refuses_to_guess_a_denominator():
    with pytest.raises(ValueError):
        denominator_for_job("check the paperwork")


def test_the_band_labels_are_the_printed_gates():
    assert BAND_LABELS == ("<=10 %", ">10-30 %", ">30 %")
    assert band_label_for_ratio(ACCEPT_PCT) == "<=10 %"
    assert band_label_for_ratio(ACCEPT_PCT + 0.01) == ">10-30 %"
    assert band_label_for_ratio(REJECT_PCT) == ">10-30 %"
    assert band_label_for_ratio(REJECT_PCT + 0.01) == ">30 %"


# ------------------------------------------------------------- the seed bank
def test_the_bank_is_the_twelve_documented_seeds():
    assert CASE_SEEDS == tuple(range(401, 413))
    assert [case["seed"] for case in BANK] == list(CASE_SEEDS)


def test_an_unknown_seed_is_refused_rather_than_improvised():
    with pytest.raises(KeyError):
        challenge_case(999)


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_every_case_is_deterministic(seed):
    """Same seed, same case. No RNG anywhere in this module's chain."""
    assert challenge_case(seed) == challenge_case(seed)


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_every_case_survives_a_json_round_trip(seed):
    case = challenge_case(seed)
    assert json.loads(json.dumps(case)) == case


def test_the_bank_covers_every_case_class():
    """The guard against a future edit quietly dropping a class of case.

    Both jobs, all three actions, and both deciding-field outcomes have to be
    reachable, or the challenge stops teaching one of them.
    """
    assert {c["decision_job"] for c in BANK} == set(DECISION_JOBS)
    assert {c["answer"]["denominator"] for c in BANK} == set(DENOMINATORS)
    assert {c["answer"]["action"] for c in BANK} == set(ACTIONS)
    assert {c["answer"]["deciding_field"] for c in BANK} == {"Decision job",
                                                            "AIAG band"}


# ------------------------------------------- nothing is typed, everything read
@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_both_ratios_come_from_against_what(seed):
    case = challenge_case(seed)
    assert case["study_ratio"] == round(
        against_what.study_ratio(GAUGE_SIGMA, case["part_sigma"]), PRINTED_DP)
    assert case["tolerance_ratio"] == round(
        against_what.tolerance_ratio(GAUGE_SIGMA, case["tolerance"]),
        PRINTED_DP)


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_both_bands_come_from_the_printed_ratios(seed):
    case = challenge_case(seed)
    assert case["study_band"] == action_for_ratio(case["study_ratio"])
    assert case["tolerance_band"] == action_for_ratio(case["tolerance_ratio"])


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_the_answer_is_the_chain_and_not_a_stored_verdict(seed):
    case = challenge_case(seed)
    answer = case["answer"]
    assert answer["denominator"] == denominator_for_job(case["decision_job"])
    chosen = (case["study_ratio"] if answer["denominator"] == "Study variation"
              else case["tolerance_ratio"])
    assert answer["action"] == action_for_ratio(chosen)
    assert case["feedback"]["Computed %GRR"] == chosen
    assert case["feedback"]["AIAG band"] == band_label_for_ratio(chosen)


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_the_feedback_fields_are_the_four_contract_labels(seed):
    """A wrong answer names a field, so the page must not invent the labels."""
    case = challenge_case(seed)
    assert tuple(case["feedback"]) == DECIDING_FIELDS
    assert case["feedback"]["Decision job"] == case["decision_job"]
    assert case["feedback"]["Chosen denominator"] == (
        case["answer"]["denominator"])


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_the_gauge_is_the_same_instrument_in_every_case(seed):
    """The level's argument dies the moment a case changes the gauge."""
    case = challenge_case(seed)
    assert case["gauge_sigma"] == round(GAUGE_SIGMA, PRINTED_DP + 1)


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_no_printed_ratio_sits_close_enough_to_a_gate_to_be_ambiguous(seed):
    """The learner reads the printed number, so the printed number must decide.

    A ratio landing within half of the last printed digit of a gate would let
    the page and the module disagree about the band while both were right.
    """
    case = challenge_case(seed)
    for pct in (case["study_ratio"], case["tolerance_ratio"]):
        assert abs(pct - ACCEPT_PCT) >= 0.05
        assert abs(pct - REJECT_PCT) >= 0.05


# ------------------------------------------- the deciding field must be earned
@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_a_decision_job_case_proves_the_other_denominator_would_differ(seed):
    """The counterfactual. `Decision job` decided it only if the job mattered."""
    case = challenge_case(seed)
    if case["answer"]["deciding_field"] != "Decision job":
        pytest.skip("this case is decided by the band")
    other = ("Tolerance" if case["answer"]["denominator"] == "Study variation"
             else "Study variation")
    other_pct = (case["study_ratio"] if other == "Study variation"
                 else case["tolerance_ratio"])
    assert action_for_ratio(other_pct) != case["answer"]["action"]
    assert case["study_band"] != case["tolerance_band"]


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_an_aiag_band_case_proves_the_gate_did_the_deciding(seed):
    """Both denominators agree, so only the gate can be doing the work."""
    case = challenge_case(seed)
    if case["answer"]["deciding_field"] != "AIAG band":
        pytest.skip("this case is decided by the job")
    assert case["study_band"] == case["tolerance_band"] == (
        case["answer"]["action"])
    pct = case["feedback"]["Computed %GRR"]
    nearest = min((ACCEPT_PCT, REJECT_PCT), key=lambda gate: abs(pct - gate))
    across = nearest - 0.01 if pct > nearest else nearest + 0.01
    assert action_for_ratio(across) != case["answer"]["action"]


def test_one_case_pair_earns_opposite_extremes_from_one_unchanged_gauge():
    """The level's central claim, reproduced with nothing recalibrated."""
    extremes = [c for c in BANK
                if {c["study_band"], c["tolerance_band"]} == {"use", "replace"}]
    assert extremes, "no case shows use against replace on one gauge"
    assert {c["decision_job"] for c in extremes} == set(DECISION_JOBS)
    assert {c["answer"]["action"] for c in extremes} == {"use", "replace"}
    assert len({c["gauge_sigma"] for c in extremes}) == 1


# ------------------------- an action is not a verdict, and never becomes one
def test_improve_is_an_action_while_conditional_stays_a_neutral_verdict():
    """Two readings of one percentage, and the level needs both.

    `verdict` answers what AIAG's table calls this gauge. `action_for_ratio`
    answers what the plant does next. Collapsing them would turn the middle
    band into a third pass/fail colour, which the contract forbids.
    """
    assert verdict(10.01) == "conditional"
    assert action_for_ratio(10.01) == "improve"
    assert verdict(30.0) == "conditional"
    assert action_for_ratio(30.0) == "improve"


@pytest.mark.parametrize("pct", [0.5, 5.0, 10.0, 10.01, 17.3, 30.0, 30.01, 88.0])
def test_the_action_and_the_verdict_share_the_published_gates(pct):
    """Different words, same two lines. Neither may drift from `against_what`."""
    action, neutral = action_for_ratio(pct), verdict(pct)
    assert (action == "use") == (neutral == "accept")
    assert (action == "replace") == (neutral == "reject")
    assert (action == "improve") == (neutral == "conditional")


# ------------------------------------------------------------------- masking
@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_no_surface_story_carries_a_real_identifier(seed):
    story = challenge_case(seed)["surface_story"]
    for ident in REAL_IDENTIFIERS:
        assert ident.lower() not in story.lower()
    # a tool code is a digit against a letter, and a masked story needs no digit
    assert re.search(r"\d", story) is None


@pytest.mark.parametrize("seed", CASE_SEEDS)
def test_no_surface_story_names_a_person_or_a_place(seed):
    """Capitals only where a sentence starts, so no proper noun can hide."""
    story = challenge_case(seed)["surface_story"]
    sentences = [s.strip() for s in story.split(".") if s.strip()]
    assert sentences, "a case needs a surface story"
    for sentence in sentences:
        words = sentence.split()
        assert words[0][0].isupper()
        assert all(word[0].islower() for word in words[1:] if word[:1].isalpha())
