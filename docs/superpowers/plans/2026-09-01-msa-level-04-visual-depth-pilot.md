# MSA Level 4 Visual-Depth Pilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` (recommended) or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn MSA Level 4 into a causal two-act lesson with an optional unseen-data decision, exact denominator/action feedback, local mastery state, field-reference paths, and the site's single contextual MSA platform seam.

**Architecture:** `msalab` remains the numerical source of truth. A small mastery module generates deterministic masked cases, both %GRR ratios, the selected denominator, the AIAG band, and the action; `chapterise.py` embeds that data into the static chapter; page-local JavaScript handles interaction and storage without reimplementing formulas. Manim Act A keeps one gauge fixed while denominators move. A new Act B applies the same gauge in two masked factories. The existing design grammar and neutral conditional band remain unchanged.

**Tech Stack:** Python 3.12, NumPy, pytest, Manim, manim-voiceover/Kokoro/RecorderService, static HTML/CSS/vanilla JavaScript, WebVTT, ffmpeg/ffprobe.

**Outcome contract:** `specs/msa-visual-depth-pilot-contract.md`

**Shared workflow artifacts:** `~/portfolio/diagrams/spc-msa-visual-depth-flow.{mmd,excalidraw,svg,png}` and `~/portfolio/diagrams/spc-msa-visual-depth-implementation.html`

---

## File map

| Responsibility | Path |
|---|---|
| Existing Level 4 formulas and verdict bands | `msa-lab/src/msalab/against_what.py` |
| Deterministic transfer cases and action chain | `msa-lab/src/msalab/level04_mastery.py` (new) |
| Act A: one gauge, moving denominators | `msa-lab/src/msalab/level04_scene.py` |
| Act B: same gauge, two masked factories | `msa-lab/src/msalab/level04_case_scene.py` (new) |
| Computation tests | `msa-lab/tests/test_level04_mastery.py` (new) |
| Static page and progress contract tests | `msa-lab/tests/test_level04_page.py` (new) |
| Existing seam/count tests | `msa-lab/tests/test_page_claims.py` |
| Media and voice gates | `msa-lab/tests/test_level04_media.py` (new), `msa-lab/tests/test_level04_voice.py` (new), existing `msa-lab/tests/test_voice.py`, `msa-lab/build-media.sh` |
| Generated chapter and embedded case JSON | `tools/chapterise.py` |
| Persistent CSS, JavaScript, figures, and transcripts | `tools/page-sources/level-04.html` |
| Served level | `level-04.html` |
| Current sitewide platform link to move | `index.html` |
| Synthetic/final media | `msa-lab/media/videos/level04*_scene/1080p60/`, `posters/level04*.jpg`, `captions/level04*.vtt` |
| Shot approval | `storyboards/msa-level-04-act-a.html`, `storyboards/msa-level-04-act-b.html` (new) |
| Human-use evidence | `docs/evidence/msa-level-04-pilot.html` (new) |

## Invariants

1. Never edit `level-04.html` as the source. Edit `tools/page-sources/level-04.html` and `tools/chapterise.py`, then regenerate.
2. JavaScript never computes %GRR, ndc, bands, actions, or answer keys. It reads Python-generated JSON.
3. `conditional` remains a neutral band. `improve` is a next action, not a pass/fail verdict or a new colour.
4. The site contains exactly one `msa.amohdnaw.xyz` link. Move it from the index navigation into Level 4; never add a second.
5. Reading, transcripts, and derivations remain available without video, JavaScript, storage, or challenge completion.
6. No real company data, company/product/part/person identifiers, new design tokens, account state, or platform sync.

---

### Task 1: Create the isolated implementation branch and prove the baseline

This task changes no product files.

- [ ] **Step 1: Create a worktree**

Invoke `@using-git-worktrees` in `/home/ammar/msa-from-first-principles` and create branch `feat/msa-level-04-visual-depth`.

- [ ] **Step 2: Run the narrow baseline**

```bash
cd msa-lab
PYTHONPATH=src .venv/bin/pytest tests/test_against_what.py tests/test_page_claims.py tests/test_voice.py -q
```

Expected: PASS. Record the exact count in `implementation-notes.html`.

- [ ] **Step 3: Regenerate Level 4 without changing it**

```bash
PYTHONPATH=msa-lab/src msa-lab/.venv/bin/python tools/chapterise.py level-04.html
node tools/typeset.mjs level-04.html
```

Expected: `level-04.html` rebuilds from `tools/page-sources/level-04.html`; the narrow tests still pass.

- [ ] **Step 4: Commit only if regeneration exposed tracked drift**

Do not commit a byte-identical baseline.

---

### Task 2: Lock shot-level storyboards before Manim code

**Files:**
- Create: `storyboards/msa-level-04-act-a.html`
- Create: `storyboards/msa-level-04-act-b.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Write Act A's visual claim**

Use one sentence: \"The gauge does not own a verdict; the denominator chooses the question.\"

- [ ] **Step 2: Build Act A's shot table**

The HTML must name, per shot: persistent object, learner prediction, transformation, surprise, counterexample, formula reveal, camera move, narration line, and exit state. Required sequence:

1. One fixed gauge spread appears first.
2. Study spread and tolerance boundaries move around it.
3. Tightening part spread makes `%GRR_study` worse while `%GRR_tolerance` stays fixed.
4. The same physical gauge survives the whole transformation.

- [ ] **Step 3: Build Act B's shot table**

Use two masked factories and one unchanged gauge. Required sequence:

1. Factory A asks to sort close process populations.
2. Factory B asks to judge conformance against a drawing.
3. Ask for the denominator before any percentage appears.
4. Reveal opposite honest actions from the same gauge.
5. Re-express `%GRR_study` as `ndc` on the same computed curve; land both printed gates on it.
6. End on the chain `Decision job → denominator → computed %GRR → AIAG band → action`.

- [ ] **Step 4: Review visually**

Open both with `review-open`; render with `shot`; read the PNGs. Reject any shot where a label moves without changing the learner's model.

- [ ] **Step 5: Commit**

```bash
git add storyboards/msa-level-04-act-a.html storyboards/msa-level-04-act-b.html implementation-notes.html
git commit -m "design: lock MSA Level 4 storyboards"
```

---

### Task 3: Add the deterministic denominator/action model

**Files:**
- Create: `msa-lab/src/msalab/level04_mastery.py`
- Create: `msa-lab/tests/test_level04_mastery.py`
- Modify: `msa-lab/src/msalab/__init__.py`

- [ ] **Step 1: Write failing tests for the whole decision chain**

```python
from msalab.level04_mastery import CASE_SEEDS, action_for_ratio, challenge_case


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
```

Also test deterministic seeds, all three actions, both denominator labels, both deciding-field outcomes (`Decision job` and `AIAG band`), and no identifiers.

- [ ] **Step 2: Run the tests and watch them fail**

```bash
cd msa-lab
PYTHONPATH=src .venv/bin/pytest tests/test_level04_mastery.py -q
```

Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement the minimal public API**

```python
CASE_SEEDS = tuple(range(401, 413))


def denominator_for_job(job: str) -> str:
    if job == "sort process populations":
        return "Study variation"
    if job == "judge drawing conformance":
        return "Tolerance"
    raise ValueError(f"unknown decision job: {job}")


def action_for_ratio(pct: float) -> str:
    if pct <= ACCEPT_PCT:
        return "use"
    if pct <= REJECT_PCT:
        return "improve"
    return "replace"
```

`challenge_case(seed)` reads `study_ratio()`, `tolerance_ratio()`, and the literal gates from `against_what.py`. It returns JSON-safe data:

```python
{
    "seed": 401,
    "surface_story": "Masked factory ...",
    "decision_job": "sort process populations",
    "gauge_sigma": 2.06,
    "part_sigma": 3.0,
    "tolerance": 150.0,
    "study_ratio": 56.6,
    "tolerance_ratio": 8.2,
    "study_band": "replace",
    "tolerance_band": "use",
    "answer": {
        "denominator": "Study variation",
        "action": "replace",
        "deciding_field": "Decision job"
    }
}
```

Ratios, bands, and answers are computed, never typed. Use `Decision job` as the deciding field when the two denominator actions disagree; use `AIAG band` when they agree and the action comes from the shared band. `Chosen denominator` and `Computed %GRR` remain exact feedback labels for those error stages.

- [ ] **Step 4: Prove the neutral-band rule**

Tests must assert `against_what.verdict(10.01) == "conditional"` while `action_for_ratio(10.01) == "improve"`. The first is a neutral verdict; the second is a next action. No colour or pass/fail semantics change.

- [ ] **Step 5: Run the focused tests**

Expected: PASS, after watching a sabotaged denominator mapping and 30% boundary fail.

- [ ] **Step 6: Commit**

```bash
git add msa-lab/src/msalab/level04_mastery.py msa-lab/src/msalab/__init__.py msa-lab/tests/test_level04_mastery.py
git commit -m "feat: compute Level 4 transfer decisions"
```

---

### Task 4: Rebuild Act A from the approved storyboard

**Files:**
- Modify: `msa-lab/src/msalab/level04_scene.py`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Keep the gauge as the persistent object**

Retain `NarratedCameraScene`, `act_style`, and `msalab.against_what`. The gauge spread cannot be destroyed and recreated between denominators or factories.

- [ ] **Step 2: Make denominator movement carry the explanation**

Move the part spread and drawing boundaries around the gauge. Only after the ratios have visible geometric meanings should `%GRR_study` and `%GRR_tolerance` appear.

- [ ] **Step 3: Show the counter-intuitive process improvement**

Tighten the process continuously. The study ratio worsens; the tolerance ratio stays still; the gauge object does not change.


- [ ] **Step 4: Render a silent draft**

```bash
cd msa-lab
PYTHONPATH=src .venv/bin/manim -qh --disable_caching src/msalab/level04_scene.py Level04
```

Expected: render succeeds. Watch muted. Reject if a reviewer cannot state why the same gauge's study verdict changes when part spread tightens.

- [ ] **Step 5: Commit**

```bash
git add msa-lab/src/msalab/level04_scene.py implementation-notes.html
git commit -m "feat: rebuild MSA Level 4 causal act"
```

---

### Task 5: Build the two-factory Act B

**Files:**
- Create: `msa-lab/src/msalab/level04_case_scene.py`
- Modify: `msa-lab/build-media.sh`

- [ ] **Step 1: Create `Level04Case`**

Import two fixed `challenge_case()` seeds that use the same gauge and opposite decision jobs. Show job → denominator → ratio → band → action as one persistent chain.

- [ ] **Step 2: Preserve the same gauge**

Move the gauge object between factory contexts. Do not instantiate a visually identical replacement.

- [ ] **Step 3: Connect `ndc` to `%GRR_study`**

After the two factories establish which denominator answers which question, transform the study-ratio readout into the `ndc` curve. Read `ndc_from_study_ratio()` and `study_ratio_for_ndc()` from `msalab.against_what`; land the 30% and `ndc = 5` gates on that one curve. Do not render a second table or recompute the relationship in the scene.

- [ ] **Step 4: Register the second act**

Add:

```bash
"level04_case_scene:Level04Case:level04-case"
```

to `SCENES` in `msa-lab/build-media.sh`.

- [ ] **Step 5: Render a silent draft**

```bash
cd msa-lab
ONLY=Level04Case ./build-media.sh
```

Expected: `Level04Case.mp4` and `posters/level04-case.jpg` exist; every ratio comes from the generated cases.

- [ ] **Step 6: Commit**

```bash
git add msa-lab/src/msalab/level04_case_scene.py msa-lab/build-media.sh
git commit -m "feat: add MSA Level 4 factory case act"
```

---

### Task 6: Add the optional mastery loop and move the platform seam

**Files:**
- Modify: `tools/chapterise.py`
- Modify: `tools/page-sources/level-04.html`
- Modify: `level-04.html` (generated)
- Modify: `index.html`
- Create: `msa-lab/tests/test_level04_page.py`
- Modify: `msa-lab/tests/test_page_claims.py`

- [ ] **Step 1: Write failing DOM and seam tests**

Assert:

1. Prose remains outside the optional form.
2. Prediction appears before Act A.
3. Both videos have posters and captions.
4. Transfer JSON contains the full Python-generated seed bank.
5. The form exposes exact labels: `Study variation`, `Tolerance`, `use`, `improve`, `replace`, `Decision job`, `Chosen denominator`, `Computed %GRR`, `AIAG band`.
6. Wrong-answer and saved-progress outputs are `aria-live`.
7. The only sitewide `msa.amohdnaw.xyz` hit is in `level-04.html`, after the decision seam.
8. The link is `https://msa.amohdnaw.xyz/app`, `target="_blank"`, `rel="noopener"`.

Run and watch the new tests fail.

- [ ] **Step 2: Generate the page data**

In `chapter_04()`, import `challenge_case` and `CASE_SEEDS`, JSON-encode the cases, and emit:

```html
<script type="application/json" id="level04-cases">...</script>
```

No JavaScript formula duplicates.

- [ ] **Step 3: Add the four-stage mastery markup**

1. `Predict`: can an unchanged gauge receive opposite verdicts?
2. Act A and transcript.
3. Act B and transcript.
4. Transfer form: denominator, action, deciding field.

Reading and next-level navigation stay open.

- [ ] **Step 4: Add page-local interaction**

Use `textContent`, `createElement`, and `appendChild`; never use `innerHTML` for generated case content. Store under `msa-fp:mastery:v1`:

```js
{
  "level-04": {
    "prediction": "opposite",
    "watched": {"act-a": true, "act-b": true},
    "passed": true,
    "seed": 405
  }
}
```

Set watched state only on `ended`. Wrap storage in `try/catch`. Storage failure keeps the case usable and reports `Progress was not saved.`

Wrong-answer feedback preserves choices, names the first mismatched contract field, shows both computed ratios and the applicable band, and changes data only after `Retry with new data`.

- [ ] **Step 5: Add the secondary paths**

- `Use this when…`: choose study variation for discrimination and tolerance for conformance.
- `Evidence`: `msalab.level04_mastery`, seed, `test_level04_mastery.py`, both ratios, selected band.
- `Open Variable GR&R study`: `https://msa.amohdnaw.xyz/app`.

- [ ] **Step 6: Move, do not duplicate, the platform link**

Remove the platform link from the index navigation. Add the Level 4 contextual link. Run the existing count test and confirm the total remains exactly one.

- [ ] **Step 7: Regenerate and typeset**

```bash
PYTHONPATH=msa-lab/src msa-lab/.venv/bin/python tools/chapterise.py level-04.html
node tools/typeset.mjs level-04.html
```

- [ ] **Step 8: Run the page and seam tests**

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add tools/chapterise.py tools/page-sources/level-04.html level-04.html index.html msa-lab/tests/test_level04_page.py msa-lab/tests/test_page_claims.py
git commit -m "feat: add MSA Level 4 mastery loop"
```

---

### Task 7: Add media, caption, container, and voice gates

**Files:**
- Modify: `msa-lab/build-media.sh`
- Create: `msa-lab/tests/test_level04_media.py`
- Create: `msa-lab/tests/test_level04_voice.py`
- Modify: `msa-lab/tests/test_page_claims.py`

- [ ] **Step 1: Write failing media tests**

For `Level04.mp4` and `Level04Case.mp4`, assert: 1920×1080, 60 fps, decoded non-empty audio, `moov` before `mdat`, non-empty WebVTT cues, non-empty scored poster, and a build manifest naming scene, service, duration, poster time, and cue count.

- [ ] **Step 2: Make `build-media.sh` emit the manifest**

Write one JSON file beside each final MP4 from measured build values and `${MSALAB_VOICE_SERVICE:-kokoro}`.

- [ ] **Step 3: Add a Level 4-scoped service-aware voice gate**

Create `test_level04_voice.py` and reuse `msalab.voice_check`. Inspect only `level04_scene` and `level04_case_scene`. For manifests marked `kokoro`, require the existing explainer F0 band. For manifests marked `recorder`, require decoded speech and voiced fraction but do not impose Kokoro's F0 band. Any unknown service fails. Leave the existing sitewide `test_voice.py` unchanged so other rendered levels do not need pilot manifests.

- [ ] **Step 4: Prove the media gates fail**

Sabotage one condition at a time: no audio stream, silent decoded audio, cue count, faststart order, frame rate, poster bytes, voice service, and voiced fraction. Restore after each observed failure.

- [ ] **Step 5: Add and exercise the MSA runtime-claim gate**

Add `_act_seconds()` and `test_runtime_claim_matches_the_rendered_acts()` to `test_page_claims.py`, mirroring SPC's `ffprobe`-based gate. The glob must include `level04_case_scene`; the test must compare the actual summed MP4 duration floor with the spelled minute claim in `index.html`. Watch it fail before updating the index claim.

- [ ] **Step 6: Commit**

```bash
git add msa-lab/build-media.sh msa-lab/tests/test_level04_media.py msa-lab/tests/test_level04_voice.py msa-lab/tests/test_page_claims.py index.html
git commit -m "test: gate MSA pilot media"
```

---

### Task 8: Render the synthetic lock candidate

**Files:** Generated media, captions, posters, manifests, and page references.

- [ ] **Step 1: Render Act A with Kokoro**

```bash
cd msa-lab
MSALAB_VOICE=1 MSALAB_VOICE_SERVICE=kokoro ONLY=Level04 ./build-media.sh
```

- [ ] **Step 2: Render Act B with Kokoro**

```bash
MSALAB_VOICE=1 MSALAB_VOICE_SERVICE=kokoro ONLY=Level04Case ./build-media.sh
```

- [ ] **Step 3: Run focused gates**

```bash
PYTHONPATH=src .venv/bin/pytest tests/test_against_what.py tests/test_level04_mastery.py tests/test_level04_page.py tests/test_level04_media.py tests/test_level04_voice.py tests/test_page_claims.py tests/test_voice.py -q
```

Expected: PASS.

- [ ] **Step 4: Commit the synthetic candidate**

Commit only after video, captions, posters, manifests, and page references agree.

---

### Task 9: Verify the real browser experience and failure states

**Files:**
- Create: `docs/evidence/msa-level-04-browser.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Serve and open the real level**

From the MSA worktree root, start the server with:

```text
hub(op="start", name="msa-pilot-http", application="python3",
    args=["-m", "http.server", "8766"], cwd=".",
    ready={"port": 8766, "timeout": 15})
```

Open the live human view with:

```bash
review-open http://127.0.0.1:8766/level-04.html
```

Open the interactive automation tab through `xd://browser`, which is a mounted OMP device in this harness:

```text
write(path="xd://browser",
      content="{\"action\":\"open\",\"name\":\"msa-level-04\",\"url\":\"http://127.0.0.1:8766/level-04.html\"}")
```

- [ ] **Step 2: Exercise the full loop**

Predict → play both acts → choose the wrong denominator → confirm exact field feedback and preserved answers → retry → confirm new seed → pass → reload → confirm progress survives.

- [ ] **Step 3: Verify the Act B `ndc` transformation**

Mute `Level04Case`. Confirm `%GRR_study` transforms into the `ndc` curve and the 30% and `ndc = 5` gates land on that same computed curve. Capture the shared-curve frame in `docs/evidence/msa-level-04-browser.html`. If narration is needed to infer the relationship, fail the storyboard.

- [ ] **Step 4: Exercise the conditional band**

Use a case in `>10–30 %`. Confirm the tile remains neutral, the action reads `improve`, and no pass/fail colour appears.

- [ ] **Step 5: Exercise storage failure**

Force `Storage.prototype.setItem` to throw. Confirm the challenge works and reports that progress was not saved.

- [ ] **Step 6: Exercise media failure**

Abort each MP4 request. Confirm prose, transcript, and challenge remain usable and the failed act is not marked watched.

- [ ] **Step 7: Verify layouts and reduced motion**

Use `shot` and read all PNGs: light and dark if supported; desktop and mobile; reduced-motion emulation; no overflow; neutral conditional state; no token/radius drift.

- [ ] **Step 8: Record evidence and commit**

The evidence HTML lists exact URLs, viewport sizes, sabotages, states, and screenshots.

---

### Task 10: Run the two-person human gate and lock the pilot

**Files:**
- Create: `docs/evidence/msa-level-04-pilot.html`
- Modify: `implementation-notes.html`

- [ ] **Step 1: Run the novice session**

Without coaching, ask one novice to explain why the unchanged gauge receives opposite honest verdicts and why the denominator changes the question.

- [ ] **Step 2: Run the practitioner session**

Give one practitioner the unseen case. Pass only if they choose the correct denominator and action without being told which %GRR to use.

- [ ] **Step 3: Record facts, not identities**

Store role, task, observed decision, failure point, retry, and pass/fail. No employer, product, part, customer, or employee identifiers.

- [ ] **Step 4: Fix and rerun any failed gate**

If narration supplies the denominator logic that motion did not, return to the storyboard.

- [ ] **Step 5: Commit the locked synthetic pilot**

```bash
git add docs/evidence/msa-level-04-pilot.html implementation-notes.html
git commit -m "test: pass MSA Level 4 human gate"
```

---

### Task 11: Record Ammar's final voice after both pilots lock

**Dependency:** The SPC Level 7 plan must also have passed its browser and human gates.

**Files:** Pilot media, captions, manifests, `msa-lab/tests/test_level04_media.py`, `msa-lab/tests/test_level04_voice.py`.

- [ ] **Step 1: Tighten the final voice expectation**

Require both Level 4 manifests in the Level 4-scoped voice test to say `recorder`. Keep decoded-audio and voiced-fraction checks; do not assert Kokoro's pitch band for human recordings. Leave the existing sitewide Kokoro regression unchanged.

- [ ] **Step 2: Watch the tightened gate fail on Kokoro manifests**

Expected: two explicit `kokoro != recorder` failures.

- [ ] **Step 3: Record Act A**

```bash
cd msa-lab
MSALAB_VOICE=1 MSALAB_VOICE_SERVICE=recorder ONLY=Level04 ./build-media.sh
```

- [ ] **Step 4: Record Act B**

```bash
MSALAB_VOICE=1 MSALAB_VOICE_SERVICE=recorder ONLY=Level04Case ./build-media.sh
```

- [ ] **Step 5: Re-run focused tests and browser playback**

Expected: numerical, page, seam, media, voice, storage, and failure-state checks pass.

- [ ] **Step 6: Commit**

```bash
git add msa-lab/media/videos/level04_scene msa-lab/media/videos/level04_case_scene posters/level04.jpg posters/level04-case.jpg captions/level04.vtt captions/level04-case.vtt msa-lab/tests/test_level04_media.py msa-lab/tests/test_level04_voice.py
git commit -m "feat: lock MSA Level 4 human narration"
```

---

### Task 12: Final MSA checkpoint

- [ ] **Step 1: Run the complete MSA suite**

```bash
cd msa-lab
PYTHONPATH=src .venv/bin/pytest -q
```

Expected: PASS with a non-zero count; compare against baseline plus new tests.

- [ ] **Step 2: Re-run the real level and the link count**

Complete a fresh Level 4 challenge, reload saved state, play both final acts, and confirm the single platform link opens `/app`.

- [ ] **Step 3: Update audit trails**

Update `implementation-notes.html`, `~/agent-ledger/NOW.md`, and `~/agent-ledger/changes.md`; run `brain index` after memory updates.

- [ ] **Step 4: Stop before rollout**

Do not touch another MSA level. Scaling requires both pilot repos to pass the shared gate and a new approved contract.
