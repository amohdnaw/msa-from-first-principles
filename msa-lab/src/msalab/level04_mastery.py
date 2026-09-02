"""LEVEL 4 MASTERY - the decision chain, on data the learner has not seen.

Level 4 proves that a percentage is not a property of a gauge. This module is
where that proof has to survive contact with a stranger's factory: one unchanged
gauge, a masked decision job, and a next action the learner has to produce
without being told which denominator to divide by.

The chain has five links and only the first one is a choice:

    Decision job          the plant says what it needs decided
    Chosen denominator     the job fixes it - study variation or tolerance
    Computed %GRR          `against_what` divides, at printed precision
    AIAG band              the published gates place the number
    action                 use, improve, or replace

Everything after the first link is arithmetic and a lookup, so this module never
stores a ratio, a band, or an answer. A case blueprint carries only what a plant
could tell you over the phone: a masked story, the job, the part spread, and the
drawing band. The rest is read from `msalab.against_what` at call time, which is
why the page, the Manim acts, and the tests cannot drift apart - there is one
place to drift from.

`improve` is a next action, not a verdict. `against_what.verdict` keeps returning
the neutral `conditional` for the same percentage, and both readings stay true at
once: the standard declines to bless the gauge, and the plant still has something
to do on Monday.

    PYTHONPATH=src .venv/bin/python -m msalab.level04_mastery
"""
from __future__ import annotations

from msalab.against_what import (
    ACCEPT_PCT, GAUGE_SIGMA, REJECT_PCT, study_ratio, tolerance_ratio,
)

# ------------------------------------------------------- the contract's words
#: The two things a plant can need decided. The only link a person chooses.
DECISION_JOBS = ("sort process populations", "judge drawing conformance")

#: What the job divides by. Same numerator in both, which is the whole point.
DENOMINATORS = ("Study variation", "Tolerance")

#: The plant instruction the chain exists to produce.
ACTIONS = ("use", "improve", "replace")

#: The four fields a wrong answer may be traced to, in chain order. The page and
#: its feedback quote these strings; they are not descriptions of them.
DECIDING_FIELDS = ("Decision job", "Chosen denominator", "Computed %GRR",
                   "AIAG band")

#: The published gates as a learner reads them off the table.
BAND_LABELS = ("<=10 %", ">10-30 %", ">30 %")

#: Decimals the learner sees. The band is taken from the printed number rather
#: than from the full-precision one, so the page can never place a case in one
#: band while this module places it in another.
PRINTED_DP = 1

#: The twelve masked cases. Seeds, not sample sizes: same seed, same case.
CASE_SEEDS = tuple(range(401, 413))


def denominator_for_job(job: str) -> str:
    """What the plant's question forces you to divide by.

    This is the only judgement in the chain, and it is not statistical. A plant
    sorting close populations is asking whether the gauge can tell parts apart,
    which is a question about the parts. A plant judging conformance is asking
    whether the gauge fits inside the drawing, which is a question about the
    drawing and does not care how the parts vary.

    An unrecognised job raises rather than defaulting, because a silent default
    here would hand a learner a real percentage answering a question nobody in
    the case asked.
    """
    if job == DECISION_JOBS[0]:
        return DENOMINATORS[0]
    if job == DECISION_JOBS[1]:
        return DENOMINATORS[1]
    raise ValueError(f"unknown decision job: {job}")


def action_for_ratio(pct: float) -> str:
    """The next action AIAG's two gates imply for one percentage.

    The gates come from `against_what`, unchanged; only the vocabulary differs.
    `verdict` speaks about the gauge and stops at `conditional`. A plant cannot
    act on `conditional`, so the middle band becomes `improve` - work on the
    gauge and re-measure - while staying the same neutral band underneath, with
    no third pass/fail colour anywhere.
    """
    if pct <= ACCEPT_PCT:
        return ACTIONS[0]
    if pct <= REJECT_PCT:
        return ACTIONS[1]
    return ACTIONS[2]


def band_label_for_ratio(pct: float) -> str:
    """Which printed gate range the percentage landed in.

    Feedback has to show the learner the row of the table they were standing on,
    not just the action it produced. The label is the range as the standard
    prints it, so a learner can find it again in the table.
    """
    if pct <= ACCEPT_PCT:
        return BAND_LABELS[0]
    if pct <= REJECT_PCT:
        return BAND_LABELS[1]
    return BAND_LABELS[2]


# ------------------------------------------------------------- the case bank
#: A blueprint is what a plant could tell you without measuring anything for
#: you: what it makes decisions about, what it needs decided, how much its parts
#: vary, and how much room the drawing gives. No ratio, band, or answer appears
#: here - those are computed, and a typed one would be a second source of truth.
#:
#: The gauge is absent on purpose. Every case runs on `GAUGE_SIGMA`, the
#: instrument Levels 2 and 3 built, because the level's claim is that the
#: instrument did not change.
_BLUEPRINTS: dict[int, dict] = {
    401: {"job": DECISION_JOBS[0], "part": 3.0, "tolerance": 150.0,
          "story": "A masked line splits a bore feature into two close "
                   "process families before assembly. The drawing band is "
                   "generous and nobody downstream reads it."},
    402: {"job": DECISION_JOBS[1], "part": 25.0, "tolerance": 35.0,
          "story": "A masked cell has to pass or fail a shaft diameter "
                   "against a tight drawing band. The upstream process runs "
                   "wide and is not being changed."},
    403: {"job": DECISION_JOBS[0], "part": 30.0, "tolerance": 200.0,
          "story": "A masked plant sorts a wide spread of housings into "
                   "feed lanes. The drawing band around the feature is very "
                   "generous."},
    404: {"job": DECISION_JOBS[1], "part": 30.0, "tolerance": 200.0,
          "story": "A masked plant certifies the same wide spread of housings "
                   "against a very generous drawing band before they ship."},
    405: {"job": DECISION_JOBS[0], "part": 10.0, "tolerance": 60.0,
          "story": "A masked line groups a moderately varied feature into "
                   "families for a rework loop. The drawing band is "
                   "unremarkable."},
    406: {"job": DECISION_JOBS[1], "part": 10.0, "tolerance": 60.0,
          "story": "A masked line judges that same moderately varied feature "
                   "against its drawing band before release."},
    407: {"job": DECISION_JOBS[0], "part": 4.0, "tolerance": 30.0,
          "story": "A masked cell tries to separate a closely held feature "
                   "into two families while the drawing band is also tight."},
    408: {"job": DECISION_JOBS[1], "part": 4.0, "tolerance": 30.0,
          "story": "A masked cell decides conformance on that closely held "
                   "feature against the same tight drawing band."},
    409: {"job": DECISION_JOBS[0], "part": 25.0, "tolerance": 35.0,
          "story": "A masked cell sorts a widely varying shaft diameter into "
                   "process families. The drawing band on it is tight, and no "
                   "conformance call is being made here."},
    410: {"job": DECISION_JOBS[1], "part": 3.0, "tolerance": 150.0,
          "story": "A masked line judges a tightly held bore feature against "
                   "a generous drawing band. Sorting the parts is somebody "
                   "else's problem."},
    411: {"job": DECISION_JOBS[0], "part": 12.0, "tolerance": 140.0,
          "story": "A masked plant separates a fairly varied feature into two "
                   "families for a routing decision. The drawing band is "
                   "roomy."},
    412: {"job": DECISION_JOBS[1], "part": 25.0, "tolerance": 70.0,
          "story": "A masked plant checks a widely varying feature against a "
                   "middling drawing band before it goes to a customer "
                   "process."},
}


def challenge_case(seed: int) -> dict:
    """One transfer case, computed from the seed's blueprint and nothing else.

    The learner gets the story, the job, and the physical setting, then has to
    produce the last three links themselves. Both ratios are returned because
    feedback on a wrong answer has to show the road not taken - that is what
    makes the denominator visible as a choice rather than a step.

    `deciding_field` records which link actually did the work, and it is derived,
    not annotated. When the two denominators imply different actions, the job is
    what decided, so the field is `Decision job` and picking the other
    denominator provably lands elsewhere. When they agree, no choice of
    denominator could have changed the outcome and the gates did the deciding,
    so the field is `AIAG band`. `Chosen denominator` and `Computed %GRR` stay in
    `DECIDING_FIELDS` as the labels feedback uses for the two error stages in
    between.

    The return value is plain JSON types, because the page reads it as data.
    """
    blueprint = _BLUEPRINTS[seed]
    part, tol = blueprint["part"], blueprint["tolerance"]

    study = round(study_ratio(GAUGE_SIGMA, part), PRINTED_DP)
    tolerance_pct = round(tolerance_ratio(GAUGE_SIGMA, tol), PRINTED_DP)
    study_band = action_for_ratio(study)
    tolerance_band = action_for_ratio(tolerance_pct)

    denominator = denominator_for_job(blueprint["job"])
    chosen = study if denominator == DENOMINATORS[0] else tolerance_pct
    deciding = ("Decision job" if study_band != tolerance_band
                else "AIAG band")

    return {
        "seed": seed,
        "surface_story": blueprint["story"],
        "decision_job": blueprint["job"],
        "gauge_sigma": round(GAUGE_SIGMA, PRINTED_DP + 1),
        "part_sigma": part,
        "tolerance": tol,
        "study_ratio": study,
        "tolerance_ratio": tolerance_pct,
        "study_band": study_band,
        "tolerance_band": tolerance_band,
        "answer": {
            "denominator": denominator,
            "action": action_for_ratio(chosen),
            "deciding_field": deciding,
        },
        "feedback": {
            "Decision job": blueprint["job"],
            "Chosen denominator": denominator,
            "Computed %GRR": chosen,
            "AIAG band": band_label_for_ratio(chosen),
        },
    }


def challenge_bank() -> list:
    """Every case, in seed order.

    The bank exists so a test can prove the whole set still covers both jobs,
    all three actions, and both deciding fields. A future edit that drops a case
    class fails there rather than quietly narrowing what the challenge teaches.
    """
    return [challenge_case(seed) for seed in CASE_SEEDS]


def main() -> None:
    print(f"one gauge for all twelve cases: {GAUGE_SIGMA:.4f} um")
    print(f"gates carried from against_what: accept <= {ACCEPT_PCT:.0f} %, "
          f"reject > {REJECT_PCT:.0f} %")
    print()
    header = ("seed", "decision job", "denominator", "%GRR", "band", "action",
              "decided by")
    print("{:<5}{:<26}{:<17}{:>7}{:>11}{:>9}   {}".format(*header))
    for case in challenge_bank():
        answer = case["answer"]
        print("{:<5}{:<26}{:<17}{:>7.1f}{:>11}{:>9}   {}".format(
            case["seed"], case["decision_job"], answer["denominator"],
            case["feedback"]["Computed %GRR"], case["feedback"]["AIAG band"],
            answer["action"], answer["deciding_field"]))
    print()
    print("The gauge never changed. The job did, and the job owns the "
          "denominator.")


if __name__ == "__main__":
    main()
