"""The gates that read the built Level 4 page rather than the library.

Level 4 is the visual-depth pilot. Everything here is a claim about the page a
reader actually gets, and none of it can be satisfied by the numbers being right
in Python: the chapter can compute a perfect case bank and still ship a form
whose labels drifted, a video that marks itself watched on `play`, or a second
platform link. Those are the failures this file is for.

Two files are read. `level-04.html` is the served page, so every DOM claim is
made against it. `tools/page-sources/level-04.html` holds the persistent CSS and
JavaScript, so the security and no-arithmetic claims are made against the source
the build copies through - asserting them on the output would pass just as well
and would not say where to fix a failure.
"""
import json
import pathlib
import re

from msalab.level04_mastery import (
    ACTIONS, BAND_LABELS, CASE_SEEDS, DECIDING_FIELDS, DENOMINATORS,
    challenge_bank,
)

REPO = pathlib.Path(__file__).resolve().parents[2]
PAGE = REPO / "level-04.html"
SOURCE = REPO / "tools" / "page-sources" / "level-04.html"
NOTES = REPO / "implementation-notes.html"

PLATFORM = "msa.amohdnaw.xyz"
ACT_A = "msa-lab/media/videos/level04_scene/1080p60/Level04.mp4"
ACT_B = "msa-lab/media/videos/level04_case_scene/1080p60/Level04Case.mp4"
ACT_B_CAPTIONS = REPO / "captions" / "level04-case.vtt"


def page():
    return PAGE.read_text()


def source():
    return SOURCE.read_text()


def block(text, opener, closer):
    """The substring from `opener` to its `closer`, opener included.

    Crude on purpose: these are flat blocks with no nesting of the same tag, and
    a real parser would be a dependency this repo does not otherwise carry.
    """
    start = text.index(opener)
    end = text.index(closer, start) + len(closer)
    return text[start:end]


def mastery_script():
    """The page-local mastery IIFE, isolated from the older lab script.

    The lab script legitimately holds the three formulas - that is section 4.4's
    claim rendered as an interactive - so a check that swept the whole file would
    fail on code this task must not touch.
    """
    t = source()
    return block(t, "// ---- mastery loop", "// ---- end mastery loop")


# ----------------------------------------------- claim 1: reading stays open
def test_the_chapter_prose_stays_outside_the_optional_form():
    """Mastery is optional, so no paragraph of the chapter may live inside a
    control the learner has to answer to get past.

    The first assertion is what stops this being a check with nothing to check:
    with no form on the page the loop below would pass on an empty sequence.
    """
    t = page()
    assert '<form id="mastery-form"' in t, "the page has no optional form at all"
    for form in re.findall(r"<form\b.*?</form>", t, re.S):
        assert "<p" not in form, f"a paragraph is trapped inside a form: {form[:120]}"
    assert 'class="lead"' in t, "the chapter lost its opening paragraph"


def test_neither_form_disables_reading_or_the_next_level():
    """A form that can gate anything is a form that will. Nothing on the page may
    be disabled, and the next-level link stays outside every form."""
    t = page()
    forms = list(re.finditer(r"<form\b.*?</form>", t, re.S))
    assert len(forms) == 2, f"expected the prediction and the transfer form, got {len(forms)}"
    inert = re.search(r"<[a-z][^>]*\sdisabled[\s>=]", t)
    assert inert is None, f"an element ships disabled: {inert.group(0) if inert else ''}"
    nxt = t.index('<a class="next"')
    for m in forms:
        assert not (m.start() < nxt < m.end()), "the next-level link is inside a form"


# ---------------------------------------- claim 2: predict before you are told
def test_the_prediction_comes_before_act_a():
    t = page()
    assert 'id="predict"' in t, "the page never asks for a prediction"
    assert t.index('id="predict"') < t.index(ACT_A), (
        "the prediction is asked after Act A has already answered it")


def test_the_prediction_asks_the_contract_question():
    """Contract check 2: whether an unchanged gauge can receive opposite
    verdicts. A prediction about anything else does not prime the act."""
    t = page()
    ask = block(t, '<div class="predict"', "</form>").lower()
    assert "opposite" in ask and "verdict" in ask, (
        "the prediction does not ask about opposite verdicts")
    assert 'value="opposite"' in ask, "no answer records the opposite-verdicts case"


# ----------------------------------------- claim 3: both acts are watchable
def test_both_acts_are_on_the_page_with_a_poster_that_exists():
    t = page()
    srcs = re.findall(r'<source src="([^"]+\.mp4)"', t)
    assert srcs == [ACT_A, ACT_B], f"Level 4 does not carry both acts: {srcs}"
    posters = re.findall(r'<video[^>]*poster="([^"]+)"', t)
    assert len(posters) == 2, f"{len(posters)} posters for 2 acts"
    for p in posters:
        assert (REPO / p).exists(), f"missing poster {p}"


def test_every_caption_track_the_page_declares_exists():
    t = page()
    tracks = re.findall(r'<track[^>]*src="([^"]+\.vtt)"', t)
    assert tracks, "the page declares no captions at all"
    for tr in tracks:
        assert (REPO / tr).exists(), f"missing caption file {tr}"


def test_act_a_has_captions():
    t = page()
    fig = block(t, "<figure>", "</figure>")
    assert ACT_A in fig, "the first figure is not Act A"
    assert "<track" in fig, "Act A ships without captions"


def test_a_rendered_act_b_caption_file_would_have_to_reach_the_page():
    """Act B rendered silently, so it has no cues yet and the page declares no
    track for it. That gap closes when Task 7 voices the act - and the moment the
    file lands on disk this fails until the page references it, so the gap cannot
    become permanent by being forgotten.
    """
    if not ACT_B_CAPTIONS.exists():
        assert "captions/level04-case.vtt" not in page(), (
            "the page promises captions that were never rendered")
        return
    assert "captions/level04-case.vtt" in page(), (
        "Act B has cues on disk that the page never offers")


def test_the_act_b_caption_gap_is_written_down():
    """An undocumented gap is indistinguishable from an oversight."""
    assert "level04-case.vtt" in NOTES.read_text(), (
        "the missing Act B caption track is not recorded in the notes")


# ------------------------------------- claim 4: Python owns the case bank
def transfer_json():
    m = re.search(r'<script type="application/json" id="level04-cases">(.*?)</script>',
                  page(), re.S)
    assert m, "the page carries no transfer data"
    return json.loads(m.group(1))


def test_the_transfer_json_is_the_whole_python_seed_bank():
    data = transfer_json()
    assert [c["seed"] for c in data["cases"]] == list(CASE_SEEDS), (
        "the page ships a different set of seeds than the module generates")
    assert data["cases"] == challenge_bank(), (
        "a case on the page disagrees with msalab.level04_mastery")


def test_the_printed_strings_are_generated_for_every_case():
    """The page renders a ratio as text it was handed, never as a number it
    formatted, so the printed precision the band was taken at cannot drift."""
    data = transfer_json()
    assert [p["seed"] for p in data["printed"]] == list(CASE_SEEDS)
    for case, shown in zip(data["cases"], data["printed"]):
        assert shown["study_ratio"].startswith(f'{case["study_ratio"]:.1f}')
        assert shown["tolerance_ratio"].startswith(f'{case["tolerance_ratio"]:.1f}')
        assert shown["band"] == case["feedback"]["AIAG band"]


def test_the_label_tuples_come_from_the_module():
    data = transfer_json()
    assert data["labels"]["denominators"] == list(DENOMINATORS)
    assert data["labels"]["actions"] == list(ACTIONS)
    assert data["labels"]["deciding_fields"] == list(DECIDING_FIELDS)
    assert data["labels"]["band_labels"] == list(BAND_LABELS)


# --------------------------------- claim 5: the form speaks the contract words
def test_the_form_exposes_the_contract_labels_character_for_character():
    form = block(page(), '<form id="mastery-form"', "</form>")
    for label in DENOMINATORS + ACTIONS + DECIDING_FIELDS:
        assert f'value="{label}"' in form, f"no control answers with {label!r}"
        assert f">{label}<" in form or f"{label}</" in form, (
            f"{label!r} is a value with no visible label")


def test_the_three_questions_are_each_a_named_group():
    form = block(page(), '<form id="mastery-form"', "</form>")
    for name in ("denominator", "action", "deciding_field"):
        assert f'name="{name}"' in form, f"the form never asks for {name}"
    assert form.count("<legend>") == 3, "the three questions are not three groups"


# ------------------------------- claim 6: feedback reaches a screen reader
def test_the_wrong_answer_and_progress_outputs_are_live_regions():
    t = page()
    for el_id in ("mastery-feedback", "mastery-progress"):
        m = re.search(r"<[^>]*id=\"" + el_id + r"\"[^>]*>", t)
        assert m, f"no {el_id} element"
        assert "aria-live" in m.group(0), f"{el_id} is not announced"


# ------------------------- claims 7 and 8: one seam, in one place, done safely
def pages():
    return sorted(REPO.glob("level-[0-9][0-9].html")) + [REPO / "index.html"]


def test_the_one_platform_link_sits_in_level_four_after_the_decision_seam():
    hits = {p.name: p.read_text().count(PLATFORM) for p in pages()}
    assert sum(hits.values()) == 1, f"the platform seam is spent more than once: {hits}"
    assert hits["level-04.html"] == 1, f"the seam is not on Level 4: {hits}"
    t = page()
    assert t.index(PLATFORM) > t.index(ACT_B), "the seam precedes Act B"
    assert t.index(PLATFORM) > t.index('id="mastery-form"'), (
        "the seam precedes the decision it is contextual to")


def test_the_platform_link_opens_the_variable_grr_study_safely():
    m = re.search(r'<a[^>]*href="https://msa\.amohdnaw\.xyz/app"[^>]*>(.*?)</a>',
                  page(), re.S)
    assert m, "the seam does not point at the study app"
    assert 'target="_blank"' in m.group(0) and 'rel="noopener"' in m.group(0)
    assert "Variable GR&amp;R study" in m.group(1), (
        f"the seam does not say what it opens: {m.group(1)!r}")


# ----------------------------------- the secondary paths the contract requires
def test_the_field_answer_and_the_evidence_are_both_reachable():
    t = page()
    use = block(t, 'id="use-this-when"', "</details>")
    assert "discrimination" in use and "conformance" in use, (
        "the field answer does not say which denominator each job takes")
    evidence = block(t, 'id="evidence"', "</details>")
    for token in ("msalab.level04_mastery", "test_level04_mastery.py",
                  "evidence-seed", "evidence-study", "evidence-tolerance",
                  "evidence-band"):
        assert token in evidence, f"the evidence path never names {token}"


# ------------------------------- the page-local script, read as a security gate
def test_the_mastery_script_never_writes_generated_html():
    js = mastery_script()
    for banned in ("innerHTML", "outerHTML", "document.write", "insertAdjacentHTML"):
        assert banned not in js, f"generated case content goes through {banned}"
    for required in ("textContent", "createElement", "appendChild"):
        assert required in js, f"the script never uses {required}"


def test_every_storage_access_is_guarded():
    """A browser in private mode throws on `localStorage`, and an unguarded read
    at module scope takes the whole challenge down with it."""
    js = mastery_script()
    assert js.count("localStorage") >= 2, "the script neither reads nor writes storage"
    for m in re.finditer(r"localStorage", js):
        before = js[:m.start()]
        assert before.count("try {") > before.count("} catch"), (
            "a localStorage access sits outside a try block")
    assert "Progress was not saved." in js, (
        "a storage failure never says progress was not saved")


def test_watched_state_is_set_only_when_a_video_ends():
    js = mastery_script()
    listened = set(re.findall(r'addEventListener\("(\w+)"', js))
    assert "ended" in listened, "no act can ever be marked watched"
    for never in ("play", "playing", "timeupdate", "loadedmetadata", "error",
                  "canplay"):
        assert never not in listened, (
            f"watched state can be reached from {never!r}, which is not watching")


def test_the_mastery_script_never_recomputes_a_ratio_or_a_band():
    """Invariant 2 of the plan. Picking a random case is arithmetic the page may
    do; a percentage, a gate comparison, or a rounding is not."""
    js = mastery_script()
    for banned in ("Math.sqrt(", "Math.hypot(", "Math.pow(", "toFixed(",
                   "parseFloat(", "* 100", "/ 100"):
        assert banned not in js, f"the page recomputes a number with {banned}"


def test_the_stored_progress_shape_is_the_agreed_one():
    js = mastery_script()
    assert '"msa-fp:mastery:v1"' in js, "progress is stored under another key"
    assert '"level-04"' in js, "progress is not namespaced by level"
    for field in ("prediction", "watched", "passed", "seed"):
        assert field in js, f"progress never records {field}"


def test_a_wrong_answer_keeps_the_data_until_the_learner_asks_for_new_data():
    """The contract's failure behaviour: a wrong answer preserves the learner's
    choices and retries with new data only when they ask for it. Swapping the
    case under a wrong answer would hide which link they got wrong."""
    t, js = page(), mastery_script()
    assert 'id="mastery-retry"' in t, "there is no way to ask for new data"
    assert "Retry with new data" in t, "the retry control is not named"
    check = block(js, "// ---- check", "// ---- end check")
    assert "drawCase(" not in check, (
        "checking an answer redraws the case, so the feedback describes data "
        "the learner can no longer see")
    assert "reset()" not in check, "checking an answer clears the learner's choices"
    retry = block(js, "// ---- retry", "// ---- end retry")
    assert "drawCase(" in retry, "the retry control does not draw new data"
