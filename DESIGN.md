# DESIGN.md — MSA from first principles

Frozen 2026-08-28. Governs every page on this site.

## This file is a diff, not a design system

**The design authority is `~/portfolio/DESIGN.md`** — the SPC curriculum's frozen system —
and it is inherited **whole**: palette and sampled ground, the two-voice rule, the type
scale, the spacing scale, radius 0, the eight-component grammar, the caption policy, the
uppercase-label symbol rule, and the ban list. Read that file first. Everything in it
applies here unchanged unless this file amends it below.

There are exactly **two amendments**. If a third is ever needed, that is a signal the two
sites have diverged and the inheritance should be reconsidered rather than patched.

### How that was decided

A twelve-variant gallery was run on 2026-08-28 against one identical specimen page
(Level 3, *Gage R&R by ANOVA* — same words, same numbers, same two figures, same
interactive, twelve visual worlds). Ammar's pick: **variant 02 with variant 06's panel and
status styling.**

Variant 02 *was* the SPC system. Variant 06 was a control-room HMI. And `portfolio/DESIGN.md`
records that the SPC system was itself picked as *"v13 (process control room HMI) skin on
v14 (mathematical textbook) skeleton"* — so the 2026-08-28 pick reproduced the
2026-07 pick independently, from a different variant set, two months apart. Inheriting is
therefore not a shortcut; it is the same answer arrived at twice.

---

## Amendment 1 — the readout tile carries its own state

SPC's Component 2 colours **only the value**. Here the whole tile carries the verdict,
because MSA pages show strips of four tiles against AIAG thresholds and a failing gauge
has to be legible at a glance rather than read digit by digit.

```css
.tile.fail  { border-color: var(--signal-alarm); }
.tile.fail .hd {
  background: rgba(222,106,93,.14);          /* 14% wash of --signal-alarm */
  color: var(--signal-alarm);
  border-bottom-color: var(--signal-alarm);
}
.tile.fail .v { color: var(--signal-alarm); }

.tile.pass  { border-color: var(--signal-ok); }
.tile.pass .hd {
  background: rgba(101,204,175,.14);         /* 14% wash of --signal-ok */
  color: var(--signal-ok);
  border-bottom-color: var(--signal-ok);
}
.tile.pass .v { color: var(--signal-ok); }
```

The **mechanism** comes from gallery variant 06. Its **palette is rejected**, on two
counts, and this matters enough to write down:

1. Variant 06 used `#10b981` / `#f59e0b` / `#ef4444` — Tailwind defaults. The inherited
   semantic pair (`--signal-ok #65ccaf`, `--signal-alarm #de6a5d`) is **sampled from the
   Manim renders**, and `portfolio/DESIGN.md` says do not re-pick these by eye. A UI that
   disagrees with its own figures makes the page contradict itself.
2. Variant 06's attention hue was amber. Amber here is **wayfinding only and never encodes
   data**. Borrowing it for a verdict would break the palette's one job.

Washes are the semantic colours at 14 %, matching the existing `--accent-wash` convention.

## Amendment 2 — the third verdict state is neutral, not a third hue

MSA verdicts are three-way where SPC's semantic pair is two colours:

| %GRR | AIAG verdict | rendered as |
|---|---|---|
| under 10 % | accept | `--signal-ok` tile, per Amendment 1 |
| 10 – 30 % | **conditional** | **neutral** — `--ink-bright` value on `--panel-high`, no hue |
| over 30 % | reject | `--signal-alarm` tile, per Amendment 1 |

No third hue is introduced. The AIAG conditional band genuinely means *"no verdict yet —
decide on cost, criticality and what the gauge is for"*, and neutral ink states that more
honestly than a colour would. It also keeps the site off a traffic light, which is the
cliché this subject invites.

`ndc` follows the same logic: under 5 fails, 5 or more passes, and there is no middle
band, so `ndc` is only ever pass or fail.

---

## What does NOT change, listed because it will be tempting

- **The ground stays `#0d1114`.** It is the exact Manim frame background, so video sits on
  the page with no seam. Going light means re-rendering every act and re-freezing every
  signal colour, and `portfolio/DESIGN.md` closed that option on measured contrast, not
  taste.
- **Two voices, strictly.** EB Garamond owns prose, headlines, deks, equations and figure
  captions. IBM Plex Mono owns labels, readouts, units, nav, panel headers and figure
  numbers. If an element is neither reading nor measuring, it should not exist.
- **Radius 0**, everywhere, with the same single floating-element exception.
- **Amber is wayfinding, never data.** Current nav item, controls, links, level numbers,
  focus rings. Nothing else.
- **Semantic colours never appear outside a data context.** No alarm-red headings, no
  ok-green buttons.
- **Uppercased labels may not contain a symbol whose case carries meaning** — `σ`, `Λ`,
  `d2`, `n` vs `N`. Use the `nc` opt-out. This rule cost the SPC build three separate
  clean-up passes and it will bite harder here, where `σ_repeat`, `σ_reproduce`, `ndc`,
  `d2*` and `K1`/`K2` all appear in labels.

  **Extended 2026-08-28, on measurement, while building Level 1.** The rule as inherited
  named Greek and case-sensitive Latin. It missed a whole class: **the micro sign.** `µ`
  is U+00B5, not Greek mu, so a Greek-range check passes it — but `text-transform:
  uppercase` maps it to **U+039C GREEK CAPITAL MU**, so a units label reading `µm`
  renders `ΜM`. On a site whose every quantity is in microns that is not a cosmetic
  defect. Verified by reading back what the browser rendered rather than by inspecting
  the source. Level 1 also mangled `s`, `c4` and `m` — a sample standard deviation, a
  derived constant and a repeat count, all renamed by a text transform.

  Two consequences, both load-bearing:
  1. **Units belong in the label, not the value.** `<dd>5.839</dd>` under
     `<dt>observed spread <span class="nc">µm</span></dt>`, never `5.839 µm` in the
     value. It follows the two-voice rule, and at tile width it also stops the unit
     wrapping onto its own line.
  2. **A checker for this cannot use a naive word scan.** The article “a” and the
     possessive “’s” both look exactly like a bare single-letter variable, and they
     produced four false positives out of ten hits on the first sweep. Strip `a`, `an`
     and `’s` before testing, or the check trains you to ignore it.

## Identity

The wordmark is `Ammar Nawawi / MSA` in the mono voice — the same primary name and the
same device the siblings use, with `MSA` where SPC has `SPC`. Nothing else distinguishes
the two sites visually, and that is deliberate: they are the same kind of artifact about
different subjects.

## Tuning

Per the knob-tool rule: if any single visual parameter survives **two** counted correction
rounds, stop prompt-iterating — build a throwaway slider panel wired to the live element,
tune in the browser, read the values back, hardcode, delete the panel.

Most likely candidate here: the **14 % wash**, which has to read as state on `--panel`
without competing with the value it sits above.
