# Outcome contract — a plain-language opening for every act

Agreed 2026-08-30, after Ammar watched all seven acts end to end. His note:

> The animation is okay for someone who knows a lot of the technical terms. Maybe need a
> more in depth visuals with more simple terms then only after that ties in with the
> current visuals we have now.

Read as: **simpler words, deeper visuals.** Show the physical thing concretely and at
length before an axis with a Greek letter on it ever appears.

Governs `msa-lab/src/msalab/level0*_scene.py` and a new `msalab/opening.py`.
`DESIGN.md`, `act_style.py` and `specs/msa-curriculum-contract.md` are unchanged and
still binding.

---

## 1. What you will see

Verifiable literally, in order, after the build. Level 1 first; the rest only after it
has been watched.

1. Open `level-01.html` and play the act. The **first thing on screen is two labelled
   panels** — `THE THING` on the left, `THE RECORD` on the right — not an axis.
2. Within the first twenty seconds, **two gauge jaws close onto a rectangle** in the left
   panel and **one number crosses to the right panel**.
3. The same part is measured again with nothing touched, and **the second number lands
   somewhere else** on the right.
4. **No Greek letter, no σ, no "repeatability", no "variance" and no "distribution"
   appears on screen** at any point before check 6.
5. The right panel fills with a crowd of different answers while the left panel is
   captioned as unchanged.
6. The opening lands on the sentence **"the part never moved. the numbers did."**, then
   the **left panel fades** and the right panel is already composed as the existing
   part 1 figure — so the join is a fade, not a cut.
7. **Act 1 runtime grows from 2:54 to between 3:40 and 4:30.**
8. The five existing parts of act 1 are **unchanged in script**: `git diff` shows no edit
   inside `part1_` … `part5_` narration strings.
9. `msalab.voice_check` still reports Level 1 **in the 100–130 Hz band**.
10. `pytest` green and the browser sweep clean at 8 pages × 8 widths, as now.

## 2. The picked direction

**Direction C, with Direction A's frames 2–3 grafted in.**

`diagrams/act-opening-mock-pick.png` — the three-direction storyboard, of which C is the
bottom strip. C supplies the two-panel composition and the fade handoff; A supplies the
jaws-closing-on-the-part moment, which lives inside C's left panel.

Why the graft rather than A alone: Levels 4, 6 and 7 have nothing physical to draw — a
percentage, a pass stamp, a variance sum — so a bench elevation would collapse into C on
those anyway. The graft gives **one recipe that holds for all seven levels**.

Per level, the left panel and the sentence it lands on:

| Level | Left panel shows | Lands on |
|---|---|---|
| 1 | one rectangle measured twice, two different ticks | the part never moved. the numbers did |
| 2 | same part: one person twice, then two people | two words for two different disagreements |
| 3 | one person's offset differs part to part | the disagreement isn't the same on every part |
| 4 | the gauge's spread held against parts, then against the drawing | a percentage of what? |
| 5 | ticks tight together, whole scale shifted | tight, and wrong |
| 6 | the tick replaced by a PASS stamp | no number left to measure |
| 7 | part spread and gauge spread stacked into one bar | the chart gets the sum |

## 3. Not in scope

- **No change to the five existing parts** of any act: not the visuals, not the script,
  not the pacing.
- **No narration rewrite outside the opening.** Jargon inside the existing parts stays.
- **No new figure sheets** and no change to the twelve that exist.
- **No page copy, lab, or chapter-spec changes.** The pages are untouched.
- **No illustration or clip art.** Schematic shapes built from Manim primitives only —
  rectangles, lines, arcs, ticks — inside `DESIGN.md`'s ban list.
- **No palette, type, or voice change.** Same tokens, same two fonts, same Kokoro
  `am_michael` at 100–130 Hz.
- **No index runtime claim edit until all seven are done**, so the page never overstates.

## 4. Defaults taken

Approving this contract confirms these; none were asked as separate questions.

- **All seven acts**, but **Level 1 ships and is watched before 2–7 begin.** One coherent
  act per checkpoint — no layer-only phases.
- **Total runtime moves from 27:32 to roughly 36–40 minutes.** The index claim is updated
  once, at the end, from a measurement.
- **The opening is narration-paced like everything else** — `with self.say(...)` drives it,
  so the silent and voiced cuts stay in sync and nothing needs re-tuning twice.
- **Openings share one module**, `msalab/opening.py`, so a correction to the visual
  grammar is one edit rather than seven.
- **Each act re-renders in full**, audio included, because inserting a part changes every
  downstream timestamp. Captions and posters regenerate from `build-media.sh`.

## 5. Verification

After each act, checks 1–10 are re-read **from this file, not from memory**, and the act
is watched end to end at 1080p60 before it is called done. A correction from Ammar
updates this contract, not just the instance.

---

## 6. Decisions taken while building

| When | What was decided | Why | Evidence | Result |
|---|---|---|---|---|
| 08-30 | Direction C + A's jaws graft | A alone collapses to C on levels 4, 6, 7 | §2 above | agreed |
| 08-30 | Value labels moved above the strip | 0.46 below the dot put them 0.16 from the strip caption | `opening.py` `value_label` | collision gone |
| 08-30 | Part block enlarged 1.5x0.72 to 2.0x0.95, plain caption added | the left panel was mostly air, and the ask was deeper visuals not emptier ones | `opening.py` `PART_W`, `thing_caption` | reads as a thing |
| 08-30 | Jaw foot ends at the block face, not a fixed reach | a fixed 0.42 reach drew a line across the part; it read as a bracket with the part inside it | `opening.py` `gauge_jaws` | reads as a clamp |
| 08-30 | Open state widened 0.62 -> 1.30 | at 0.62 against a 2.0 block, open and closed were indistinguishable, so the closing animation did nothing | frames at 16.2-18.4s | travel visible |
| 08-30 | Postponed-term guard raises, does not warn | a warning in a render log is a warning nobody reads | `opening.py` `plain` | 28 gates, 4 watched failing |
| 08-30 | AST parse, not regex, for the on-screen scan | the regex spanned newlines and matched `GAUGE_SIGMA` in code, failing a passing build | `tests/test_opening.py` | vacuity assert caught it |
