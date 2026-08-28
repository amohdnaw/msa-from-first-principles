# Outcome contract — MSA from first principles

Agreed 2026-08-28 after a twelve-variant gallery and a five-decision interview.
Governs the whole site. A correction from Ammar updates **this file**, not just the
instance it was noticed on.

The parent clause is §2 of `~/portfolio/specs/curriculum-arc-contract.md` ("The MSA
sibling"), which reserved this build and required its own contract first. This is that
contract.

---

## 1. What you will see

Checkable after each level ships, and re-read from this file rather than from memory.

**The look**

1. Open any level page beside the SPC curriculum and they are visibly the **same kind of
   artifact**: the same dark `#0d1114` ground, the same serif prose in a single reading
   column, the same mono labels, the same amber wayfinding, the same hard 0-radius edges.
   Only the wordmark differs — `Ammar Nawawi / MSA` instead of `/ SPC`.
2. Every readout tile whose value has failed its AIAG threshold shows it **on the tile
   itself**, not only in the digits: the tile border takes the alarm colour and its header
   strip takes a wash of it. A passing tile is quiet. This is the one addition to the SPC
   component grammar and it comes from gallery variant 06.
3. A tile in the **conditional** band (%GRR 10–30 %) is **neutral, not a third colour** —
   bright ink on a raised panel, no hue. Nothing on the site uses a traffic light.
4. No page contains a colour that encodes data outside the sampled semantic pair, and
   amber never encodes data anywhere.

**The teaching**

5. Seven level pages exist, 01–07, and the index says **seven** — not twelve. The count is
   derived from the seven movements §2 names, and the index says plainly that MSA is a
   narrower subject that needs seven.
6. Every level page carries a **narrated Manim act** with a poster frame and an opt-in
   caption track, and **an interactive lab** that recomputes in the browser from the same
   formulas the Python library exposes.
7. Open any lab, drag any control, and the readouts move. On the levels where a published
   AIAG or literature value exists, the lab agrees with the Python library **to the
   printed precision**, and a test proves it rather than a screenshot.
8. **No number on any page is asserted.** Every constant is computed at render time from
   `msalab`, every study is generated from a seeded model, and the test suite checks the
   same functions the pages read. Nobody has to trust a quoted figure, including me.
9. Every level ends with a working link to the next, and the chain **walks** end to end on
   the live site: 01 → 02 → … → 07 → index, every hop 200. Resolving is not sufficient —
   the SPC build shipped three links that resolved while walking readers past a level.

**The seam**

10. Level 7 is the handshake back and contains **exactly one** link to the SPC curriculum,
    landing on Level 8 (Capability), on the argument that a Cpk is only as trustworthy as
    the gage that fed it.
11. Sitewide there is **exactly one** outbound link to the SPC curriculum and **exactly
    one** to the MSA platform, and a check counts them.
12. This site **never teaches control limits**, and the SPC site never teaches GR&R. Each
    stops at the boundary rather than summarising the other badly.

**The gates**

13. `pytest` passes, and **every gate has been watched failing** on a deliberately broken
    copy before it is trusted. A gate that has never failed is decoration.
14. The browser sweep passes at **seven widths, 320–2560**: zero horizontal overflow,
    symmetric margins, one left edge per chapter, no Greek under an uppercase transform,
    no LaTeX rendered as literal text, no upscaled image, no broken image, and every lab
    canvas sized to its column.

---

## 2. The picked look

**Gallery of twelve directions, run 2026-08-28. Ammar's pick: variant 02, with variant 06's
panel and status styling grafted in.**

Resolution — and it is smaller than it sounds. Variant 02 *is* the SPC curriculum's system,
and SPC's own `DESIGN.md` records that it was itself picked as "v13 (process control room
HMI) skin on v14 (mathematical textbook) skeleton". So 02+06 reproduces the SPC pick
independently, two months later, from a different variant set. That is a strong signal and
it is why this site **inherits `~/portfolio/DESIGN.md` verbatim** rather than growing a
second design authority.

**Inherited without change:** the palette and its sampled ground, the two-voice rule
(EB Garamond owns prose, headlines, deks, equations, captions; IBM Plex Mono owns labels,
readouts, units, nav, panel headers, figure numbers), the type scale, the spacing scale,
radius 0, the eight-component grammar, the caption policy, the ban list, and the
uppercase-label symbol rule.

**Two named deltas, and only two:**

- **Delta 1 — the stateful readout tile.** SPC's Component 2 colours only the value. Here
  the tile's border takes the semantic colour and its header strip takes a 14 % wash of
  it, so a failing gauge is legible at a glance across a strip of four tiles. Mechanism
  taken from variant 06; **its palette is explicitly rejected** — 06 used Tailwind
  defaults (`#10b981` / `#f59e0b` / `#ef4444`) and its attention hue is amber, which would
  break SPC's load-bearing rule that amber is wayfinding and never encodes data. The wash
  is built from the sampled pair `--signal-ok #65ccaf` and `--signal-alarm #de6a5d`.
- **Delta 2 — the third verdict state.** MSA verdicts are three-way (accept under 10 %,
  conditional 10–30 %, reject over 30 %) where SPC's semantic pair is two colours. No
  third hue is introduced. Conditional renders **neutral** — `--ink-bright` on
  `--panel-high` — because the AIAG conditional band genuinely means "no verdict yet,
  decide on cost and context", and saying that in ink is more honest than a third colour.

Both deltas are written into this site's `DESIGN.md` as an inheritance header plus the two
amendments, so there is one design authority and a short diff, never a fork.

---

## 3. Not in scope

- **No control-limit teaching.** No control charts, no Shewhart, no capability indices
  taught here beyond the single Level 7 sentence that hands them back. §2 boundary rule.
- **No second MSA link.** The live MSA *platform* is a tool this site points at once. Its
  app, its auth, its registry and its report layouts are untouched by this work.
- **No twelve levels.** The spine is seven and the index says so.
- **No real company data.** No `.xls` study from `html-dashboard`, no tool IDs
  (ICOS-K01, BTMMN03, Nikon OM-X), no PIC names, anonymised or otherwise.
- **No sampling plans, no AQL, no reliability, no Weibull, no measurement-uncertainty GUM
  treatment.** Named here because each is plausibly "MSA-adjacent" and each would be a
  different subject.
- **No shared repo with the SPC curriculum and no shared repo with the platform.** Own
  repo, own Pages site, own history.
- **No custom subdomain on day one.** It ships on `amohdnaw.github.io/msa-from-first-principles`
  and a subdomain gets pointed at it whenever Ammar wants one.
- **No hand-recorded human voice.** Same synthetic narration path as SPC, same one-line
  swap available later.

## 4. Defaults taken

Approving this contract confirms these. Each was decided rather than asked, and each is
reversible.

1. **The seam is retargeted so the two curricula link to each other.** SPC Level 11
   currently points at the MSA *platform*; on this build it points at **this curriculum**
   instead, and the platform link moves to where it belongs — inside the MSA curriculum.
   Reason: §2 allows exactly one link each way "at the seam", and with three artifacts the
   coherent reading is curriculum ↔ curriculum, with the platform referenced from its own
   subject. Cost: one paragraph edit to the shipped `level-11.html`.
2. **The return link lands on SPC Level 8, not Level 11.** §2 says so explicitly, and
   Capability is the level whose number a bad gauge invalidates.
3. **msa.amohdnaw.xyz currently contains zero links back to the SPC curriculum**, so the
   contracted return half of the seam has never existed. This build creates it. Found by
   measurement on 2026-08-28, not from the contract text.
4. **Conditional is neutral** rather than a third hue — see Delta 2.
5. **The narrated acts are rendered at 1080p60 with the same `build-media.sh` pipeline**,
   posters scored by frame content rather than taken at a fixed timestamp, captions
   provided but never `default`.
6. **`msalab` is a new Python package, not an import of `spclab`.** The two share method,
   not code, and a shared library would couple two sites that must be able to move
   independently. Where a formula genuinely already exists in `spclab` (the normal CDF,
   the incomplete beta), it is re-derived and its own test checks it against the published
   table — the same rule SPC used when it found `_betainc` recursing.
7. **Level count is derived, not matched.** If a movement turns out to carry two levels'
   worth of content the count changes and §2 plus this file are amended — the count is not
   defended for symmetry.

---

## 5. The spine

Seven levels, one per movement of §2, the last being the handshake.

| # | Level | The one question it answers | Media |
|---|---|---|---|
| 1 | Measurement as a process | A gauge is not a window onto the truth; it is a process with variation, and it has its own distribution. What is the observed spread actually made of? | act + lab |
| 2 | Repeatability and reproducibility | The same operator twice, versus two operators once — two different questions that the plant calls one word. Which one is your problem? | act + lab |
| 3 | Gage R&R by ANOVA | Average-and-range gets an answer; ANOVA gets the same answer plus the term average-and-range cannot see. Why does the interaction change the corrective action? | act + lab |
| 4 | %GRR, ndc, and against what | A percentage of *what*? %study and %tolerance answer different questions and disagree on purpose. When does a gauge that passed one fail the other? | act + lab |
| 5 | Bias, linearity, stability | Precision is not accuracy. A gauge can repeat beautifully and be wrong, be right in the middle and wrong at the ends, or be right today and wrong in June. | act + lab |
| 6 | Attribute agreement | When the measurement is a judgement — pass/fail, cosmetic grade — percent agreement flatters and kappa does not. What does chance agreement cost you? | act + lab |
| 7 | The handshake back | A Cpk is only as trustworthy as the gage that fed it. What does an unfit gauge do to a capability number, arithmetically? | act + lab |

Each level ends by raising the question the next one answers. That chain is the structure;
nothing else is.

## 6. Machinery — inherited, not rebuilt

From `~/portfolio`, adapted rather than reinvented:

- `tools/chapterise.py` (1836 lines) — the page generator: chapter specs to built HTML.
- `tools/typeset.mjs` — the KaTeX pass plus `--check` idempotence gate.
- `DESIGN.md` — inherited verbatim with the §2 inheritance header and two deltas.
- `spc-lab/src/spclab/narration.py` — `NarratedScene` / `NarratedCameraScene`, the
  narration-drives-pacing base classes, and the one-script-two-renders contract.
- `spc-lab/build-media.sh` — render, caption, poster-score, in one command.
- `spc-lab/tests/test_page_claims.py` — the runtime/claim gates that made the SPC index
  self-checking, including the lesson that a claim written from the same misunderstanding
  as the code cannot catch the code.
- `fonts/` — the four self-hosted woff2 files and `install-fonts.py`, so Manim renders
  byte-identical outlines to what the browser gets.

New here: `msalab` (the Python library and its tests) and `specs/` (this file).

## 7. Verification

After each level: checks 1–14 are re-read **from this file, not from memory**, and run
against the built page at 1080p60 and across 320–2560. Gates are watched failing on a
sabotaged copy before they are trusted. A correction updates this contract.

Build order: one level at a time, each shipped and verified before the next starts, so a
wrong shape costs one level rather than seven.
