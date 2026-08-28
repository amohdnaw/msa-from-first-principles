#!/usr/bin/env python3
"""Turn a level page into a textbook chapter (DESIGN.md §3, 'The level page is a chapter').

Rebuilds <main> from a chapter spec while preserving, byte for byte, the blocks that
already carry verified content: the KaTeX equation, the interactive lab, the SYS note,
every figure, and the next-level link. Nothing is re-typeset or re-rendered here.

Input  is tools/page-sources/<page>, tracked, pre-chapter.
Output is <page> at the repo root, overwritten.

    python3 tools/chapterise.py level-06.html      # one page
    for f in level-01 level-03 level-04 level-06 level-08 level-09; do \
        python3 tools/chapterise.py $f.html; done  # all of them
"""
from __future__ import annotations
import re
import sys
import pathlib

# ---------------------------------------------------------------- CSS injected once
CHAPTER_CSS = """
  /* ---------- chapter grammar (DESIGN.md §3) ----------
     Layout follows the book convention rather than an invented one. Tufte CSS:
     figures are constrained to the main column by default, a *small* figure may
     go in the margin, and anything larger takes the full text block. Margin notes
     sit "as close as possible to the text that references them" - which is done
     with a float at the note's position in the flow, never with grid rows. Grid
     rows put the note in a row of its own and cut an L-shaped hole in the page. */
  :root{ --marg:320px; --marg-gap:48px; }

  /* The page IS the grid. Before this the container was 110rem while the text
     block was 1090px and left-aligned inside it, so the margins came out 149px
     left and 675px right - the dead right column. The page width is now computed
     from the same tokens the grid uses, so it can never drift from it again. */
  .wrap{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg) + 2 * var(--gutter))}
  /* the text block: measure + gutter + margin. Everything aligns to its left edge. */
  .leaf{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  .leaf > div > p,.leaf > div > .eq,.leaf > div > .sys{max-width:var(--measure)}

  .ch-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.16em;
    text-transform:uppercase;color:var(--accent);margin:0 0 18px}

  .toc{border-top:1px solid var(--rule-strong);border-bottom:1px solid var(--rule);
    padding:22px 0 24px;margin:8px 0 0;
    max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  .toc-head{display:flex;gap:18px;align-items:baseline;margin:0 0 14px;flex-wrap:wrap}
  .toc-head .est{margin-left:auto}
  .toc ol{list-style:none;margin:0;padding:0;display:grid;
    grid-template-columns:repeat(auto-fit,minmax(min(300px,100%),1fr));gap:2px 48px}
  .toc li{display:grid;grid-template-columns:44px 1fr;gap:10px;padding:7px 0;
    border-bottom:1px solid rgba(42,49,56,.55)}
  .toc .n{font-family:var(--mono);font-size:13px;color:var(--accent);padding-top:.35em}
  .toc a{color:var(--ink);text-decoration:none;font-size:19px}
  .toc a:hover{color:var(--accent)}
  .toc-chain{font-family:var(--serif);font-size:17px;color:var(--ink-dim);margin:14px 0 0;
    display:flex;flex-wrap:wrap;gap:0 8px;align-items:baseline}
  .toc-chain .sep{color:var(--rule-strong);padding:0 4px}
  .toc .sub{display:block;font-size:15px;color:var(--ink-dim);line-height:1.4}

  /* a heading must clear the sticky nav when jumped to from the contents */
  main section{scroll-margin-top:96px}
  .sec-no{font-family:var(--mono);font-size:13px;font-weight:600;letter-spacing:.14em;
    color:var(--accent);display:block;margin-bottom:10px}
  /* headings balance across lines; body prose gets pretty so no line is left
     carrying a single word (better-typography principle 9) */
  main h2{font-family:var(--serif);font-size:33px;font-weight:600;line-height:1.12;
    color:var(--ink-bright);margin:0 0 14px;max-width:26em;text-wrap:balance}
  .leaf > div > p{text-wrap:pretty}
  .toc .sub,.note em,figcaption .figtext{text-wrap:pretty}
  .lead::first-letter{initial-letter:2;font-weight:600;color:var(--ink-bright);margin-right:.08em}

  /* margin notes: instrument voice, level with the paragraph they annotate.
     Below the margin breakpoint they simply follow the prose at measure width. */
  .note{display:block;font-family:var(--mono);font-size:12.5px;line-height:1.6;
    color:var(--ink-dim);border-left:1px solid var(--rule);padding-left:14px;
    margin:0 0 26px;max-width:var(--measure);text-indent:0}
  .note .k{display:block;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;
    font-size:11px;margin-bottom:5px}
  .note .v{color:var(--ink-bright);font-size:21px;font-variant-numeric:tabular-nums}
  .note em{font-family:var(--serif);font-style:italic;font-size:17px;color:var(--ink);
    line-height:1.45;display:block;font-variant-numeric:oldstyle-nums}
  .note.speak{border-left-color:var(--accent)}
  .note.data .row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;
    align-items:baseline;padding:3px 0;border-bottom:1px solid rgba(42,49,56,.6);min-width:0}
  .note.data .row:last-child{border-bottom:0}
  /* NB: these labels are uppercased, which maps σ to Σ - the summation sign.
     Keep label text ASCII and put Greek in the value. */
  .note.data .rk{color:var(--ink-dim);letter-spacing:.06em;text-transform:uppercase;font-size:11px}
  .note.data .rv{color:var(--ink-bright);font-variant-numeric:tabular-nums;min-width:0;
    overflow-wrap:anywhere}
  .note.data .row.num .rv{font-size:16px;text-align:right;white-space:nowrap}
  /* a sentence is not data: own line, left aligned, in the reading voice */
  .note.data .row.txt{display:block}
  .note.data .row.txt .rv{display:block;font-family:var(--serif);font-size:17px;
    line-height:1.45;margin-top:3px;font-variant-numeric:oldstyle-nums}
  .note.data .rn{flex:1 1 100%;min-width:0;color:var(--ink-dim);font-size:11.5px;
    line-height:1.5;overflow-wrap:anywhere}

  /* A referenced act, collapsed. Closed it is a poster strip; open it is a player
     at the full text-block width. The previous version was a 340px margin card,
     which measured 323x182 on screen - not a player, a thumbnail with controls. */
  .act{border-top:1px solid var(--rule);margin:40px 0 0}
  .act > summary{display:flex;gap:18px;align-items:center;cursor:pointer;
    padding:16px 0;list-style:none}
  .act > summary::-webkit-details-marker{display:none}
  .act > summary::marker{content:""}
  .act > summary:hover .k{color:var(--ink-bright)}
  /* the closed strip has to look like a video, or it reads as a footnote. A poster
     at 280px with a play glyph over it does that; 180px and a word did not. */
  .act .thumb-wrap{position:relative;flex:none;display:block;line-height:0}
  .act .thumb{width:280px;height:auto;display:block;border:1px solid var(--rule)}
  .act .thumb-wrap::after{content:"";position:absolute;left:50%;top:50%;
    transform:translate(-50%,-50%);width:0;height:0;
    border-left:18px solid var(--ink-bright);border-top:11px solid transparent;
    border-bottom:11px solid transparent;filter:drop-shadow(0 0 6px rgba(0,0,0,.6))}
  .act > summary:hover .thumb-wrap::after{border-left-color:var(--accent)}
  .act[open] > summary .thumb-wrap{display:none}
  .act .meta{min-width:0}
  .act .k{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.14em;
    text-transform:uppercase;color:var(--accent);display:block;margin-bottom:5px}
  .act .cap{font-size:17px;line-height:1.45;color:var(--ink-dim);display:block;
    max-width:52ch;text-wrap:pretty}
  .act .cue{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;
    color:var(--ink-dim);margin-left:auto;flex:none;white-space:nowrap}
  .act[open] > summary .cue{color:var(--accent)}
  .act video{display:block;width:100%;height:auto;background:var(--ground);
    margin:0 0 8px;max-width:min(100%,calc(68vh * 16 / 9))}
  @media(max-width:640px){ .act > summary{flex-wrap:wrap} .act .thumb{width:160px} }
  /* a margin figure - Tufte's one case for a figure outside the main flow */
  .note.watch video{display:block;width:100%;height:auto;margin:8px 0;border:1px solid var(--rule)}
  .note.watch:hover .k{color:var(--ink-bright)}

  /* figures take the whole text block and share its left edge */
  figure,.figpair{max-width:calc(var(--measure) + var(--marg-gap) + var(--marg))}
  figure video{max-width:min(100%,calc(68vh * 16 / 9))}

  @media (min-width:1500px){
    :root{ --body:26px; --marg:340px; }
    /* the note floats into the margin at its position in the flow. This is the
       whole trick: no row of its own, so no hole beside it. */
    /* tufte-css's mechanism: a negative right margin pulls the float out of the
       text column so it consumes no horizontal space there. Without it the float
       lives inside the 702px paragraph and shortens every line beside it, which
       destroys the measure the whole design is built on. */
    .note{float:right;clear:right;width:var(--marg);max-width:var(--marg);
      margin:0 calc(-1 * (var(--marg) + var(--marg-gap))) 26px 0;
      position:relative;z-index:1}
    /* a note that must not float (it holds something wide) */
    .note.nofloat{float:none;width:auto;max-width:var(--measure);margin-top:34px}
    .leaf > div::after{content:"";display:block;clear:both}
  }
"""

def tex(latex: str) -> str:
    """Inline maths, rendered by tools/typeset.mjs.

    EB Garamond has no combining hat and no subscript digits, so a literal
    "sigma-hat" arrives on screen as sigma followed by a stray caret, and a
    subscript falls back mid-word to another font. Anything mathematical inside
    serif prose goes through KaTeX instead of hoping for the glyph.
    """
    return '<span class="tex" data-tex="' + latex + '"></span>'


def take_div(s: str, start: int) -> str:
    """Return the complete <div> beginning at `start`, matching nesting.

    Regex cannot do this: the equation block contains rendered KaTeX, which is
    hundreds of nested divs and spans, so a non-greedy `</div>\\s*</div>` match
    stops in the middle of the formula and leaves the document unbalanced. The
    symptom is later blocks nesting inside the equation - a 2032px "lab".
    """
    depth = 0
    i = start
    while i < len(s):
        if s.startswith("<div", i) and (i + 4 >= len(s) or s[i + 4] in " >\t\n"):
            depth += 1
            i += 4
        elif s.startswith("</div>", i):
            depth -= 1
            i += 6
            if depth == 0:
                return s[start:i]
        else:
            i += 1
    raise ValueError("unbalanced div")


def extract(html: str) -> dict:
    """Pull the blocks that must survive untouched."""
    body = html[html.index("<main"):html.index("</main>")]
    out = {}

    def block(pattern, name, flags=re.S):
        m = re.search(pattern, body, flags)
        if not m:
            sys.exit(f"chapterise: could not find {name}")
        return m.group(0)

    out["eq"] = take_div(body, body.index('<div class="eq">'))
    # not every level has an interactive
    out["lab"] = (take_div(body, body.index('<div class="lab">'))
                  if '<div class="lab">' in body else "")
    out["sys"] = block(r'<aside class="sys">.*?</aside>', "sys note")
    out["next"] = block(r'<a class="next".*?</a>', "next link")

    figs = {}
    for m in re.finditer(r'<figure[^>]*>.*?</figure>', body, re.S):
        f = m.group(0)
        # a figure may hold <img src>, <source src> or a bare <video src>
        src = re.search(r'<(?:img|source|video)[^>]*\bsrc="([^"]+\.(?:png|jpg|mp4|webm))"', f)
        if src:
            figs[src.group(1).split("/")[-1]] = f
    out["figs"] = figs
    return out


def nc(sym: str) -> str:
    """A symbol that must keep its case inside an uppercased label.

    Margin labels are `text-transform: uppercase`, which does not merely restyle
    a variable — it renames it. In SPC `n` is the subgroup size and `N` is the
    lot size, so "at n = 100" rendered "AT N = 100", which is a different
    quantity. Greek is worse: sigma becomes the summation sign.
    """
    return f'<span class="nc">{sym}</span>'


def note(k, v=None, text=None, speak=False, serif=False):
    """A margin note.

    Emitted as a span so it can live *inside* a paragraph: a float only rises to
    the line box where it appears, so a note that is a sibling of the paragraph
    lands at the paragraph's foot instead of level with its reference.
    """
    cls = "note speak" if speak else "note"
    inner = f'<span class="k">{k}</span>'
    if v:
        inner += f'<span class="v">{v}</span>'
    if text:
        inner += f"<em>{text}</em>" if serif else text
    return f'<span class="{cls}">{inner}</span>'


def datanote(*rows, k=None):
    """One margin block carrying several label/value rows.

    Three separate notes on one paragraph stack to 246px of float and stretch the
    section; one block with three rows is shorter and reads as a table.
    """
    out = []
    if k:
        out.append(f'<span class="k">{k}</span>')
    for label, value, *rest in rows:
        tail = f'<span class="rn">{rest[0]}</span>' if rest else ""
        # under ~14 characters it is data and aligns right against its label;
        # longer than that it is a sentence, and right-aligning a sentence is
        # exactly what made the chapter opener unreadable
        kind = "num" if len(str(value)) <= 14 else "txt"
        out.append(f'<span class="row {kind}"><span class="rk">{label}</span>'
                   f'<span class="rv">{value}</span>{tail}</span>')
    return '<span class="note data">' + "".join(out) + "</span>"



# The prose quotes computed constants. Importing them here means the page, the
# act, the figure sheets and the test suite all read one source; a literal typed
# into the prose would be exactly the "asserted number" this repo rejects.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "msa-lab" / "src"))
from msalab.measurement import (  # noqa: E402
    AVERAGE_TABLE, C4_PARTS, C4_SHORTFALL_PCT, EXPECTED_OBSERVED, FLOOR,
    GAUGE_RATIO, GAUGE_SIGMA, INFLATION_TABLE, ONE_PART_RANGE, ONE_PART_READS,
    ONE_PART_SD, OBSERVED_EXACT, OBSERVED_SIM, PARTS, PART_SIGMA,
    RATIO_FOR_10PCT, RATIO_FOR_1PCT, REPEATS, REPEATS_FOR_1PCT,
    REPL_OBSERVED, REPL_WITHIN, SE_OBSERVED_PCT, SE_WITHIN_PCT, WIDENING_PCT,
    WITHIN_DF, WRONG_DIRECTION_PCT,
)

# ---------------------------------------------------------------- chapters
# Each chapter is data: the opener facts, the contents, and a builder that lays
# out its sections. Prose is adapted from that act's own narration — the page is
# the third render of the one script (see DESIGN.md §3).

P = "          "


def para(text, *notes, lead=False):
    """A paragraph, with its margin notes injected after the first sentence.

    The injection point matters: a float only rises to the line box where it
    appears, so a note placed after the paragraph lands at the paragraph's foot.
    """
    cls = ' class="lead"' if lead else ""
    if notes:
        m = re.search(r"(?<=[.?!])\s", text)
        cut = m.end() if m else len(text)
        text = text[:cut] + "".join(notes) + text[cut:]
    return f"{P}<p{cls}>{text}</p>"


def chapter_01(K):
    return [
        ("s1", "1.1", "One part is a distribution", [
            para("A bore is machined once. It has one size, and that size does not "
                 "change while you look at it. Measure it two hundred times and you "
                 "get two hundred different answers, spread over "
                 f"{ONE_PART_RANGE:.1f}&nbsp;µm.",
                 note("the instance", text="A bench micrometer on machined bores, "
                      "microns from nominal. Simulated, seeded, and reproducible by "
                      "anyone who runs the library."),
                 lead=True),
            para("Nothing about the part accounts for that. The spread belongs to the "
                 "measurement, and the moment you accept that it exists you have "
                 "accepted the sentence this whole curriculum rests on: the gauge is "
                 "a process, so it has a distribution, so it can be studied with the "
                 "same arithmetic as any other process.",
                 datanote(("readings", f"{ONE_PART_READS}"),
                          ("spread of the readings", f"{ONE_PART_SD:.2f} µm"),
                          ("full range seen", f"{ONE_PART_RANGE:.1f} µm"),
                          k="one part, many answers")),
            K["fig"]("Level01.mp4"),
            para("That is the first minute of the act above. It is worth watching the "
                 "readings land rather than reading the number: the histogram builds "
                 "out of nothing while a single bright line marks the one true size "
                 "that never moves."),
        ]),
        ("s2", "1.2", "A reading is two things", [
            para("Every reading is the part plus whatever the measurement process did "
                 "on that occasion. Written down, that is unremarkable. Its "
                 "consequence is not.",
                 note("what is left out", text="Bias — a gauge that reads high on "
                      "everything — is Level 5. Here the error averages to zero, so "
                      "nothing can be blamed on it.")),
            para("If the reading is a sum, the spread of the readings is the spread of "
                 "a sum. And the spread of a sum of two independent things is not the "
                 "sum of their spreads.",
                 note("independent", text="It matters. If the gauge read high on big "
                      "parts the two terms would be correlated and the arithmetic "
                      "below would be wrong.")),
            K["fig"]("l01_1_a_gauge_is_a_process.png"),
        ]),
        ("s3", "1.3", "Variances add, standard deviations do not", [
            para("Independent variation adds in quadrature — the way the sides of a "
                 "right triangle do. The parts are one leg, the gauge is the other, "
                 "and what you observe is the hypotenuse.",
                 lead=True),
            f'{P}<div class="eq"><div class="eq-body" data-tex="\\sigma_{{obs}}^2 = '
            f'\\sigma_{{part}}^2 + \\sigma_{{gauge}}^2"></div>'
            f'<div class="eq-num">(1.1)</div></div>',
            para(f"On this study the parts stand at {PART_SIGMA}&nbsp;µm and the gauge "
                 f"at {GAUGE_SIGMA}&nbsp;µm. Adding them would say "
                 f"{PART_SIGMA + GAUGE_SIGMA:.1f}. The answer is "
                 f"{OBSERVED_EXACT:.2f} — the gauge is "
                 f"{GAUGE_RATIO*100:.0f}&nbsp;% of the part spread and it costs "
                 f"{WIDENING_PCT:.1f}&nbsp;%.",
                 datanote(("gauge as a fraction", f"{GAUGE_RATIO*100:.1f} %"),
                          ("so the spread is wider by", f"{WIDENING_PCT:.2f} %"),
                          ("adding them would claim", f"{PART_SIGMA + GAUGE_SIGMA:.1f} µm"),
                          k="the quadrature price")),
            para("Squaring is what makes measurement error cheap at first and "
                 "expensive later. A small ratio contributes its square, which is "
                 "smaller still; a ratio near one contributes all of itself.",
                 datanote(*[(f"gauge at {r*100:.0f} %", f"{pct:.2f} % wider")
                            for r, pct in INFLATION_TABLE],
                          k="what a gauge costs")),
            para("Read it backwards and it stops being reassuring. To keep the "
                 f"observed spread within one percent of the truth the gauge has to "
                 f"stay under {RATIO_FOR_1PCT*100:.0f}&nbsp;% of the part spread — but "
                 f"a gauge may reach {RATIO_FOR_10PCT*100:.0f}&nbsp;% before the "
                 "histogram is ten percent too wide. Bad gauges hide in that gap.",
                 note("the useful direction", text="Most tables answer “what does this "
                      "gauge cost”. The question an engineer actually has is “how bad "
                      "may it get”, which is the inverse.")),
        ]),
        ("s4", "1.4", "Real, and invisible", [
            para("Here is where this level nearly went wrong. The claim is that the "
                 "observed spread exceeds the part spread. The seeded forty-part study "
                 "in the library reports the opposite.",
                 lead=True),
            para(f"Its observed spread came out at {OBSERVED_SIM:.2f}&nbsp;µm against a "
                 f"true part spread of {PART_SIGMA}. Narrower. The variance law "
                 "forbids that in expectation, and sampling permits it constantly: at "
                 f"forty parts the sampling error of a standard deviation is about "
                 f"{SE_OBSERVED_PCT:.0f}&nbsp;%, and the effect being looked for is "
                 f"{WIDENING_PCT:.1f}&nbsp;%.",
                 datanote(("the effect", f"{WIDENING_PCT:.1f} %"),
                          ("one study's noise", f"{SE_OBSERVED_PCT:.0f} %"),
                          ("studies pointing the wrong way", f"{WRONG_DIRECTION_PCT:.0f} %"),
                          k="signal against noise")),
            K["fig"]("l01_2_what_one_study_can_show.png"),
            para(f"Roughly {WRONG_DIRECTION_PCT:.0f}&nbsp;% of studies report the parts "
                 "as narrower than they are. The reseeding fix was available and it "
                 "would have been a lie about what a study can do, so the study stayed "
                 "and a test now pins it.",
                 note("the gate", text="A test asserts the seeded study contradicts "
                      "the headline. If someone reseeds it to look tidy, that test "
                      "fails.")),
            para("Averaged over four thousand studies the law returns exactly — and "
                 "not quite to sigma. It returns to "
                 + tex(r"c_4\sigma") + ", because the sample standard deviation is a "
                 "biased estimator, low by a factor that depends only on how many "
                 "observations it had.",
                 datanote(("averaged over 4000 studies", f"{REPL_OBSERVED:.4f} µm"),
                          ("what " + nc("s") + " estimates",
                           f"{EXPECTED_OBSERVED:.4f} µm"),
                          ("sigma itself", f"{OBSERVED_EXACT:.4f} µm"),
                          (nc("c4") + f" at {PARTS} parts", f"{C4_PARTS:.5f}"),
                          k="a 0.64 % gap that was not error")),
            para(f"That {C4_SHORTFALL_PCT:.2f}&nbsp;% looked like simulation noise and "
                 "was not. Checking the replication against sigma would have needed a "
                 "tolerance wider than the whole effect this level teaches, so the "
                 "check would have passed while the arithmetic was wrong. Against "
                 + tex(r"c_4\sigma") + " it holds to four figures.",
                 note("earned it first", text="c4 is derived from gamma functions here "
                      "and checked against the printed constants at n = 2, 3, 4, 5, 10 "
                      "and 25 before anything rests on it.")),
            para("So gauge error is never estimated by comparing histograms. It is "
                 "estimated by measuring one part repeatedly, which has "
                 f"{WITHIN_DF} degrees of freedom on the gauge alone and does not "
                 "depend on the part spread at all.",
                 datanote(("within-part estimate", f"{REPL_WITHIN:.4f} µm"),
                          ("its sampling error", f"{SE_WITHIN_PCT:.1f} %"),
                          ("degrees of freedom", f"{WITHIN_DF}"),
                          k="the trustworthy number")),
        ]),
        ("s5", "1.5", "You cannot measure your way out", [
            para("The obvious response to a noisy gauge is to measure every part "
                 "several times and average. It works, and it stops working.",
                 lead=True),
            para("Averaging divides the measurement variance by the number of repeats "
                 "and does nothing whatever to the variation between the parts. So the "
                 f"observed spread falls towards {FLOOR}&nbsp;µm and stops there.",
                 datanote(*[(nc("m") + f" = {m}", f"{sd:.3f} µm", f"+{pct:.2f} %")
                            for m, sd, pct in AVERAGE_TABLE],
                          k="repeats against the floor")),
            para(f"Five repeats reach one percent above the floor. Twenty-five barely "
                 f"improve on five, because the improvement goes as one over m inside "
                 f"a square root. There is no number of repeats that measures the "
                 f"parts away.",
                 note("the floor", text="It is the part-to-part variation. The thing "
                      "you were trying to see in the first place.")),
            K["lab"],
            para("Which leaves the question the next level has to answer. A gauge has "
                 "a size, and a size is only meaningful against something. This level "
                 "has been quietly comparing it to the part spread — but the spread of "
                 "the readings on one part was measured with one operator, on one "
                 "afternoon. Hand the gauge to somebody else and it is not obvious "
                 "that the number stays the same.",
                 note("the seam ahead", text="Repeatability and reproducibility are "
                      "two different questions that the plant calls one word.")),
            K["sys"],
        ]),
    ]


def chapter_02(K):
    from msalab.reproducibility import (
        CLAMPED_UNDER_PCT, CORRECTED_MEAN, FIX_RATIO, GAUGE_EXACT,
        HALVE_REPEAT_PCT, HALVE_REPRODUCE_PCT, NAIVE_MEAN, NAIVE_OVER_PCT,
        NEGATIVE_PCT, NOISY_BORROWED_PCT, NOISY_EXPECTED_NAIVE, NOISY_NAIVE,
        NOISY_REPEAT, NOISY_REPRODUCE, OPERATORS, PARTS as RR_PARTS,
        REPEAT_DF, REPEAT_ERR_PCT, REPRODUCE_DF, REPRODUCE_ERR_PCT,
        SIGMA_REPEAT, SIGMA_REPRODUCE, TRIALS,
    )
    rep_share = SIGMA_REPEAT ** 2 / (SIGMA_REPEAT ** 2 + SIGMA_REPRODUCE ** 2) * 100
    return [
        ("s1", "2.1", "Two questions, one word", [
            para("Level 1 finished with a gauge that has a size, measured by reading "
                 "one part over and over. That is one question, and it is not the "
                 "only one. Hand the same part to somebody else.",
                 note("what carried over", text="Same bores, same bench "
                      "micrometer. The part spread is unchanged, so the two levels "
                      "are describing one process."),
                 lead=True),
            para("Repeatability is one operator disagreeing with themselves. "
                 "Reproducibility is operators disagreeing with each other. The "
                 "plant calls the pair one word, and the word hides the fact that "
                 "they are rarely the same size and never have the same fix."),
            K["fig"]("Level02.mp4"),
        ]),
        ("s2", "2.2", "The offset has to persist", [
            para("A difference between two operators on one part is not evidence of "
                 "anything: it could be repeatability wearing a costume. What makes "
                 "reproducibility a separate term is that the offset travels with "
                 "the person across every part they touch.",
                 lead=True),
            K["fig"]("l02_1_two_distances.png"),
            para("Three lines, roughly parallel. Operator A reads low on all ten "
                 "parts, which is a property of A rather than of any part. That is "
                 "the whole justification for giving it its own term - and the "
                 "moment those lines stop being parallel there is a third thing to "
                 "account for, which is Level 3.",
                 datanote(("repeatability", f"{SIGMA_REPEAT} µm"),
                          ("reproducibility", f"{SIGMA_REPRODUCE} µm"),
                          ("the gauge term", f"{GAUGE_EXACT:.2f} µm"),
                          (nc("repeat") + " share of variance", f"{rep_share:.0f} %"),
                          k="the split")),
        ]),
        ("s3", "2.3", "The same law, and the fix that follows from it", [
            para("The two terms combine the way everything in this subject "
                 "combines. Level 1's gauge term was never atomic.", lead=True),
            f'{P}<div class="eq"><div class="eq-body" data-tex="\\sigma_{{gauge}}^2 = '
            f'\\sigma_{{repeat}}^2 + \\sigma_{{reprod}}^2"></div>'
            f'<div class="eq-num">(2.1)</div></div>',
            para("Squaring is again what decides everything. The larger term "
                 "dominates the sum, so improving the smaller one is nearly free of "
                 "consequence. On this gauge reproducibility carries "
                 f"{100 - rep_share:.0f}&nbsp;% of the variance, and the two "
                 "candidate projects are not comparable:",
                 datanote(("halve repeatability", f"{HALVE_REPEAT_PCT:.1f} % better"),
                          ("halve reproducibility", f"{HALVE_REPRODUCE_PCT:.1f} % better"),
                          ("ratio", f"{FIX_RATIO:.1f}x"),
                          k="two projects, same effort")),
            para("Which is why “fix the gauge” is not advice. Recalibrating the "
                 "instrument attacks repeatability; training, a written method and a "
                 "fixture attack reproducibility. Aim the wrong one and the study "
                 "will be repeated in six months with the same answer.",
                 note("and it reverses", text="Nothing here is a fact about "
                      "reproducibility. Make repeatability the larger term and the "
                      "arithmetic recommends the opposite project.")),
        ]),
        ("s4", "2.4", "The operator spread is not the operator effect", [
            para("Now try to measure the split, and the second half turns out to be "
                 "much harder than the first. Repeatability is easy: every "
                 "part-operator cell contributes readings, so it arrives with "
                 f"{REPEAT_DF} degrees of freedom and about "
                 f"{REPEAT_ERR_PCT:.0f}&nbsp;% of error.",
                 lead=True),
            para("Reproducibility looks equally easy - take the spread of the "
                 "operator averages - and it is a trap. Each average is itself made "
                 "of noisy readings, so its spread carries repeatability inside it. "
                 "The quantity that estimator actually targets is not the one you "
                 "wanted:",
                 note("the shape of the error", text="It enters divided by the "
                      "number of readings behind each average, so a bigger study "
                      "borrows less. It never borrows nothing.")),
            f'{P}<div class="eq"><div class="eq-body" data-tex="\\sigma^2_{{\\text{{op '
            f'means}}}} = \\sigma_{{reprod}}^2 + \\frac{{\\sigma_{{repeat}}^2}}'
            f'{{parts \\times trials}}"></div><div class="eq-num">(2.2)</div></div>',
            para(f"On a gauge whose repeatability dominates - {NOISY_REPEAT}&nbsp;µm "
                 f"against {NOISY_REPRODUCE} - that borrowed term is most of the "
                 f"answer. The naive estimator targets "
                 f"{NOISY_EXPECTED_NAIVE:.3f}&nbsp;µm when the truth is "
                 f"{NOISY_REPRODUCE}: it overstates by "
                 f"{(NOISY_EXPECTED_NAIVE/NOISY_REPRODUCE-1)*100:.0f}&nbsp;%, and "
                 f"{NOISY_BORROWED_PCT:.0f}&nbsp;% of what it reports is the "
                 f"instrument rather than the people.",
                 datanote(("the truth", f"{NOISY_REPRODUCE} µm"),
                          ("what the naive estimator targets", f"{NOISY_EXPECTED_NAIVE:.3f} µm"),
                          ("of that, borrowed repeatability", f"{NOISY_BORROWED_PCT:.0f} %"),
                          k="a number about the wrong thing")),
            para(f"One study cannot show you this. With {OPERATORS} operators the "
                 f"estimate has {REPRODUCE_DF} degrees of freedom and about "
                 f"{REPRODUCE_ERR_PCT:.0f}&nbsp;% of error, so the seeded study here "
                 f"reported {NOISY_NAIVE:.3f} - below the truth, in the opposite "
                 f"direction to the bias. Averaged over four thousand studies the "
                 f"bias appears exactly as the algebra says.",
                 datanote(("one study said", f"{NOISY_NAIVE:.3f} µm"),
                          ("4000 studies, uncorrected", f"{NAIVE_MEAN:.3f} µm"),
                          ("against the truth", f"{NAIVE_OVER_PCT:+.0f} %"),
                          k="why one study is not evidence")),
            K["fig"]("l02_2_the_operator_term.png"),
        ]),
        ("s5", "2.5", "Wrong in both directions at once", [
            para("The correction subtracts one estimate from another, and the result "
                 "is not obliged to be a variance. It can come out negative, which "
                 "is not a coding error: it is an estimator meeting a boundary.",
                 lead=True),
            para(f"On that noisy gauge it happens {NEGATIVE_PCT:.0f}&nbsp;% of the "
                 f"time. The convention is to report zero - no operator effect - "
                 f"which reads as a finding and is really a shrug.",
                 note("what zero means here", text="Not “the operators agree”. "
                      "“This study cannot tell.” Those are different sentences and "
                      "only one of them is true.")),
            para("And clamping is not neutral. Truncating one side of a "
                 "distribution moves its mean, so the corrected number runs low "
                 "while the uncorrected one runs high. The same study is wrong in "
                 "both directions, and picking whichever looks reasonable is not a "
                 "method.",
                 datanote(("uncorrected, over 4000 studies", f"{NAIVE_OVER_PCT:+.0f} %"),
                          ("clamped", f"{-CLAMPED_UNDER_PCT:+.0f} %"),
                          ("clamped at zero", f"{NEGATIVE_PCT:.0f} % of studies"),
                          k="the two errors")),
            K["lab"],
            para("So the gauge is split, and the operator half is the half a "
                 "standard study struggles to see. Worse, everything in this level "
                 "assumed the operator offsets are parallel - that A reads low by "
                 "the same amount on every part. Suppose A reads low on the small "
                 "parts and high on the large ones. Nothing here has a term for "
                 "that, and average-and-range never will.",
                 note("the seam ahead", text="An interaction: operators "
                      "disagreeing about particular parts. It needs ANOVA, and it "
                      "is often the reason a gauge fails.")),
            K["sys"],
        ]),
    ]


def chapter_03(K):
    from msalab.anova import (
        AT_WORST, AT_ZERO, ANOVA_DRIFT_PCT, ANOVA_ZERO_BIAS_PCT,
        BAD_INTERACTION, CLEAN_ANOVA, CLEAN_GAP_PCT, CLEAN_XBAR, D2_TRIALS,
        DIRTY, DIRTY_ANOVA, DIRTY_TRUTH, DIRTY_XBAR, F_INTER_CLEAN,
        F_INTER_DIRTY, IDENT_RESIDUAL, INTERACTION_SHARE, OPERATORS,
        PARTS as A_PARTS, POOL_ALPHA, POOL_COST_PCT, P_INTER_CLEAN,
        P_INTER_DIRTY, SWEEP, TRIALS, XBAR_DRIFT_PCT,
    )
    ss = DIRTY["table"]["ss"]
    shares = {k: ss[k] / ss["total"] * 100
              for k in ("part", "operator", "interaction", "repeat")}
    return [
        ("s1", "3.1", "One study, two arithmetics", [
            para(f"{A_PARTS} parts, {OPERATORS} operators, {TRIALS} trials each: "
                 "sixty numbers. Average-and-range reduces them with ranges and a "
                 "table of constants. ANOVA reduces them with sums of squares and "
                 "nothing looked up.",
                 note("the constant, earned", text="Average-and-range needs "
                      + tex("d_2") + f", which is {D2_TRIALS:.4f} for three "
                      "readings. Simulated here, then checked against the printed "
                      "table at five subgroup sizes before anything rests on it."),
                 lead=True),
            para("On a well-behaved study they land close together, and that is the "
                 "honest starting point rather than a concession. The older method "
                 "is not wrong and it is far easier by hand, which is exactly why "
                 "it outlived the arithmetic that replaced it.",
                 datanote(("ANOVA", f"{CLEAN_ANOVA:.2f} µm"),
                          ("average-and-range", f"{CLEAN_XBAR:.2f} µm"),
                          ("gap on this one study", f"{CLEAN_GAP_PCT:.1f} %"),
                          k="no interaction present")),
            K["fig"]("Level03.mp4"),
        ]),
        ("s2", "3.2", "The term that only one of them has", [
            para("Level 2 assumed something without saying so: that each operator's "
                 "offset is the same on every part. Operator A reads low, and reads "
                 "low by the same amount on part one and part ten.",
                 lead=True),
            para("Suppose A reads low on the small parts and high on the large ones. "
                 "That is a real and common failure - a fixture that locates some "
                 "geometries badly, an operator who interpolates a scale differently "
                 "near the ends - and it has a name: the part-by-operator "
                 "interaction.",
                 note("what it is not", text="Not extra repeatability. It is "
                      "perfectly reproducible: measure that part again and the same "
                      "operator makes the same error.")),
            K["fig"]("l03_1_parallel_or_not.png"),
            para("Non-parallel lines <em>are</em> the interaction. Nothing else in "
                 "the study shows it, and it is a difference of differences - which "
                 "is why it needs every operator to see every part, and more than "
                 "one trial. With a single trial the interaction and the repeat "
                 "error occupy the same cells and it is not merely imprecise, it is "
                 "unidentifiable.",
                 datanote(("clean study", f"F {F_INTER_CLEAN:.2f}, p {P_INTER_CLEAN:.3f}"),
                          ("with an interaction", f"F {F_INTER_DIRTY:.2f}, p < 0.001"),
                          ("pool below", f"p > {POOL_ALPHA}"),
                          k="the interaction test")),
        ]),
        ("s3", "3.3", "Four terms, and no remainder", [
            para("What ANOVA gives you that a table of constants cannot is an "
                 "identity. The total variation in all sixty numbers splits into "
                 "exactly four pieces.", lead=True),
            f'{P}<div class="eq"><div class="eq-body" data-tex="SS_{{total}} = '
            f'SS_{{part}} + SS_{{oper}} + SS_{{part \\times oper}} + '
            f'SS_{{repeat}}"></div><div class="eq-num">(3.1)</div></div>',
            para("And nothing is left over - not approximately. On the study with an "
                 "interaction the remainder is "
                 f"{IDENT_RESIDUAL:.1e}, which is floating-point zero. That is what "
                 "makes this a decomposition rather than a convention, and it is the "
                 "statement average-and-range has no way to make.",
                 datanote(("parts", f"{shares['part']:.1f} %"),
                          ("operators", f"{shares['operator']:.1f} %"),
                          ("interaction", f"{shares['interaction']:.1f} %"),
                          ("repeat", f"{shares['repeat']:.1f} %"),
                          k="the total, split")),
            para("The variance components come from inverting the expected mean "
                 "squares, which means a component is a difference of two mean "
                 "squares - so it can come out negative, exactly as Level 2's "
                 "reproducibility could. Three places can hit that boundary here "
                 "instead of one.",
                 note("the check that matters", text="Feeding the components back "
                      "must reproduce the mean squares to floating point. A "
                      "percentage test cannot catch a mis-inversion; that algebraic "
                      "one catches three different ones.")),
        ]),
        ("s4", "3.4", "It does not misplace the interaction", [
            para("So where does the interaction go in the older arithmetic? The "
                 "tempting answer is that it gets folded into repeatability and "
                 "makes the gauge look noisier than it is. That is wrong, and the "
                 "truth is worse.",
                 lead=True),
            para("Repeatability comes from ranges taken <em>inside</em> a "
                 "part-operator cell. The interaction is constant inside that cell, "
                 "so the range is blind to it. Reproducibility comes from the spread "
                 "of the operator averages, and the interaction averages away across "
                 "the parts. There is nowhere for it to enter.",
                 note("mechanically", text="Change the interaction from zero to "
                      "four microns and the repeatability estimate does not move at "
                      "all. A test asserts exactly that.")),
            para("It is omitted. So the gauge comes out <em>smaller</em> than it is - "
                 "the method flatters the instrument, and nobody reading the report "
                 "has any way to tell.",
                 datanote(("the true gauge", f"{DIRTY_TRUTH:.2f} µm"),
                          ("interaction share of it", f"{INTERACTION_SHARE:.0f} %"),
                          ("average-and-range says", f"{DIRTY_XBAR:.2f} µm"),
                          k="a gauge that looks better than it is")),
            K["lab"],
        ]),
        ("s5", "3.5", "Three hundred studies, because one settles nothing", [
            para("On the single seeded study above, ANOVA reports "
                 f"{DIRTY_ANOVA:.2f}&nbsp;µm against a truth of "
                 f"{DIRTY_TRUTH:.2f} - it <em>overshoots</em> by more than "
                 "average-and-range undershoots. One study does not settle which "
                 "method is better, and this is the fourth time this curriculum has "
                 "had to say so.",
                 note("kept on purpose", text="A test asserts the seeded study "
                      "reverses the ranking. Reseeding until it agreed with the "
                      "conclusion would be the dishonest fix."),
                 lead=True),
            K["fig"]("l03_2_what_omitting_it_costs.png"),
            para("Averaged over three hundred studies at each interaction strength "
                 "the picture is unambiguous, and it is a picture about direction "
                 "rather than about size. ANOVA moves "
                 f"{ANOVA_DRIFT_PCT:.1f}&nbsp;% across the whole sweep; "
                 f"average-and-range moves {XBAR_DRIFT_PCT:.1f}&nbsp;%, all of it "
                 "downward.",
                 datanote(*[(f"interaction {r['interaction']:.1f} " + nc("µm"),
                             f"{r['xbar_err']:+.0f} %")
                            for r in SWEEP],
                          k=nc("X\u0304") + "–R error against the truth")),
            para("ANOVA is not unbiased either, and saying so matters. With no "
                 f"interaction at all it sits {ANOVA_ZERO_BIAS_PCT:.1f}&nbsp;% low, "
                 "because an operator component estimated on two degrees of freedom "
                 "and then square-rooted comes out short. It is not "
                 "<em>systematically</em> wrong as the interaction grows, which is a "
                 "weaker and more defensible claim than being right.",
                 note("and the convention", text="AIAG pools the interaction into "
                      f"repeatability when p > {POOL_ALPHA}. Pooling a real one "
                      f"understates the gauge by {POOL_COST_PCT:.1f} % on this "
                      "study - a decision with a price, not a tidy-up.")),
            para("Which brings the question this has been building towards. There "
                 "are four variances now, and a verdict is not a variance. A verdict "
                 "is a percentage, and a percentage needs a denominator. Choosing it "
                 "is not arithmetic - it is a decision about what the gauge is for, "
                 "and the two usual choices disagree with each other on purpose.",
                 note("the seam ahead", text="%GRR against study variation, or "
                      "against tolerance. Same gauge, two verdicts.")),
            K["sys"],
        ]),
    ]


def chapter_04(K):
    from msalab.against_what import (
        ACCEPT_PCT, A_PART, A_STUDY, A_TOL, A_TOLPCT, B_PART, B_STUDY, B_TOL,
        B_TOLPCT, CAP, CENTRED, GAUGE_SIGMA, NDC, NDC_GATE_GAP, NDC_MIN,
        REJECT_PCT, SHIFTED, STUDY_PCT, STUDY_PCT_AT_NDC5, STUDY_AFTER,
        STUDY_BEFORE, TOLERANCE, TOL_PCT, TIGHTEN_FROM, TIGHTEN_TO, verdict,
    )
    import math as _m
    s6 = 6 * _m.hypot(4.7, GAUGE_SIGMA)
    return [
        ("s1", "4.1", "A verdict is not a variance", [
            para("Three levels of arithmetic have produced variances: a "
                 "repeatability, a reproducibility, an interaction. None of them "
                 "is a decision. To get a decision you divide, and the whole "
                 "difficulty of this level is what you divide by.",
                 lead=True),
            f'{P}<div class="eq"><div class="eq-body" data-tex="\\%GRR_{{study}} = '
            f'\\frac{{\\sigma_{{gauge}}}}{{\\sigma_{{total}}}} \\qquad '
            f'\\%GRR_{{tol}} = \\frac{{6\\sigma_{{gauge}}}}'
            f'{{tolerance}}"></div><div class="eq-num">(4.1)</div></div>',
            para("Same numerator both times. The first asks whether this gauge can "
                 "tell these parts apart. The second asks whether it can decide "
                 "whether a part conforms. Those are different questions, and the "
                 "standard prints both answers side by side without saying which "
                 "one you asked.",
                 datanote(("the gauge, 6" + nc("σ"), f"{6*GAUGE_SIGMA:.1f} µm"),
                          ("the study spread, 6" + nc("σ"), f"{s6:.1f} µm"),
                          ("the tolerance", f"{TOLERANCE:.0f} µm"),
                          ("against study", f"{STUDY_PCT:.1f} %"),
                          ("against tolerance", f"{TOL_PCT:.1f} %"),
                          k="one numerator, two denominators")),
            K["fig"]("Level04.mp4"),
        ]),
        ("s2", "4.2", "Only one of them can see the parts", [
            para("The tolerance came off a drawing. It does not know how much the "
                 "parts vary, so the tolerance ratio cannot move when the process "
                 "changes. The study ratio is almost nothing but that.",
                 lead=True),
            para(f"Improve the process - take the part spread from "
                 f"{TIGHTEN_FROM}&nbsp;µm down to {TIGHTEN_TO} - and the study "
                 f"ratio gets <em>worse</em>, from {STUDY_BEFORE:.1f}&nbsp;% to "
                 f"{STUDY_AFTER:.1f}. Nothing about the instrument changed. A gauge "
                 f"measuring parts that are nearly identical cannot sort them, and "
                 f"as the parts converge the ratio approaches a hundred percent.",
                 datanote(("study ratio before", f"{STUDY_BEFORE:.1f} %"),
                          ("study ratio after", f"{STUDY_AFTER:.1f} %"),
                          ("tolerance ratio", f"{TOL_PCT:.1f} % (unmoved)"),
                          k="tightening the process")),
            para("Which is worth stating plainly, because it is the opposite of an "
                 "intuition: a good process makes a gauge look bad on the study "
                 "ratio. The gauge did not get worse. The question got harder.",
                 note("both are honest", text="If you are sorting parts into bins, "
                      "the study ratio is the one you want. If you are stamping "
                      "conform or not, it is the wrong number entirely.")),
            K["fig"]("l04_1_against_what.png"),
        ]),
        ("s3", "4.3", "The same gauge, opposite verdicts", [
            para(f"So take this gauge - {GAUGE_SIGMA:.2f}&nbsp;µm, unchanged - and "
                 f"put it in two factories.", lead=True),
            para(f"<strong>A.</strong> A well-controlled process on a generous "
                 f"drawing: parts at {A_PART:.0f}&nbsp;µm, tolerance "
                 f"{A_TOL:.0f}. The study ratio is {A_STUDY:.1f}&nbsp;% - "
                 f"{verdict(A_STUDY)} - and the tolerance ratio is "
                 f"{A_TOLPCT:.1f}&nbsp;%, {verdict(A_TOLPCT)}.",
                 datanote(("against study", f"{A_STUDY:.1f} % → {verdict(A_STUDY)}"),
                          ("against tolerance", f"{A_TOLPCT:.1f} % → {verdict(A_TOLPCT)}"),
                          k="factory A")),
            para(f"<strong>B.</strong> A sloppy process on a tight drawing: parts at "
                 f"{B_PART:.0f}&nbsp;µm, tolerance {B_TOL:.0f}. Exactly the "
                 f"reverse - {B_STUDY:.1f}&nbsp;% ({verdict(B_STUDY)}) against "
                 f"{B_TOLPCT:.1f}&nbsp;% ({verdict(B_TOLPCT)}).",
                 datanote(("against study", f"{B_STUDY:.1f} % → {verdict(B_STUDY)}"),
                          ("against tolerance", f"{B_TOLPCT:.1f} % → {verdict(B_TOLPCT)}"),
                          k="factory B")),
            para("One gauge, two rows, opposite verdicts off the same printed "
                 "table - and neither row is a mistake. The shaded region in the "
                 "figure above is the whole set of processes and drawings where "
                 "that happens, and it is not a corner case.",
                 note("so which", text="Whichever matches the decision the gauge is "
                      "there to make. That is a question about the job, and no "
                      "amount of arithmetic answers it.")),
            K["lab"],
        ]),
        ("s4", "4.4", "The third number is the first one rearranged", [
            para("Beside those two the standard prints a third: the number of "
                 "distinct categories, which is supposed to say how many groups the "
                 "gauge can separate.",
                 lead=True),
            para("It is not independent. ndc is "
                 + tex(r"1.41\,\sigma_{part}/\sigma_{gauge}") + ", and the study "
                 "ratio is " + tex(r"\sigma_{gauge}/\sigma_{total}") + ", so one "
                 "determines the other exactly. Plot ndc against the study ratio "
                 "and you get a curve, not a cloud. It cannot carry information "
                 "the first number did not already have, and it cannot rank two "
                 "gauges differently.",
                 datanote((nc("ndc") + " from the components", f"{NDC:.4f}"),
                          (nc("ndc") + " from the study ratio", f"{NDC:.4f}"),
                          ("difference", "0 (algebraic)"),
                          k="two routes, one number")),
            K["fig"]("l04_2_what_the_numbers_are_worth.png"),
            para(f"What it does add is an inconsistency. Requiring ndc to reach "
                 f"{NDC_MIN} is exactly requiring the study ratio to be at or below "
                 f"{STUDY_PCT_AT_NDC5:.1f}&nbsp;% - which is "
                 f"{NDC_GATE_GAP:.1f}&nbsp;points tighter than the "
                 f"{REJECT_PCT:.0f}&nbsp;% printed beside it. A gauge can satisfy "
                 f"one rule and fail the other on the same study.",
                 datanote(("reject above", f"{REJECT_PCT:.0f} %"),
                          (nc("ndc") + f" ≥ {NDC_MIN} means", f"≤ {STUDY_PCT_AT_NDC5:.1f} %"),
                          ("the two gates differ by", f"{NDC_GATE_GAP:.1f} points"),
                          k="two lines, one table")),
            para("And the 1.41 is not a measurement. It is the square root of two, "
                 "rounded to two places - which itself moves the gate by 0.08 of a "
                 "point. Small, and a reminder that a rounded constant sitting "
                 "inside a threshold is not the same object as the number it came "
                 "from.",
                 note("earned, not quoted", text="A test asserts the constant is "
                      "√2 to within 0.005, and another asserts the gate computed "
                      "with the exact root is the more permissive of the two.")),
        ]),
        ("s5", "4.5", "A percentage is a proxy for a risk", [
            para("None of the three numbers is the thing anyone actually cares "
                 "about. A conformance decision compares a <em>reading</em> to a "
                 "limit, so a good part can be scrapped and a bad part can be "
                 "shipped - and how often depends on where the process is sitting.",
                 lead=True),
            para(f"On a centred process with this gauge, "
                 f"{CENTRED['bad_parts_accepted_pct']:.0f}&nbsp;% of the genuinely "
                 f"out-of-tolerance parts pass. That is not the same sentence as "
                 f"the headline rate of {CENTRED['false_accept_pct']:.3f}&nbsp;% of "
                 f"all parts, and the second one is what ships.",
                 datanote(("of the bad parts, accepted", f"{CENTRED['bad_parts_accepted_pct']:.1f} %"),
                          ("of all parts", f"{CENTRED['false_accept_pct']:.3f} %"),
                          ("of the good parts, rejected", f"{CENTRED['good_parts_rejected_pct']:.2f} %"),
                          ("scrap", f"{CENTRED['scrap_rate_pct']:.2f} %"),
                          k="centred")),
            para(f"Now move the process a quarter of the tolerance off centre and "
                 f"touch nothing else. Scrap goes from "
                 f"{CENTRED['scrap_rate_pct']:.2f}&nbsp;% to "
                 f"{SHIFTED['scrap_rate_pct']:.1f}, and good parts rejected from "
                 f"{CENTRED['good_parts_rejected_pct']:.2f} to "
                 f"{SHIFTED['good_parts_rejected_pct']:.2f}. The gauge is "
                 f"identical, so every percentage in this level is identical, and "
                 f"the risk moved by more than an order of magnitude.",
                 datanote(("scrap", f"{CENTRED['scrap_rate_pct']:.2f} % → {SHIFTED['scrap_rate_pct']:.1f} %"),
                          ("good parts rejected", f"{CENTRED['good_parts_rejected_pct']:.2f} % → {SHIFTED['good_parts_rejected_pct']:.2f} %"),
                          ("%GRR", "unchanged"),
                          k="shifted, same gauge")),
            para("So a percentage is a proxy, and it does not know where you are. "
                 "Which exposes the last thing these four levels have assumed "
                 "without checking: that the gauge is merely noisy. Everything so "
                 "far has had a mean of zero. Suppose it reads high.",
                 note("the seam ahead", text="Bias, linearity and stability. A "
                      "gauge can repeat beautifully and be wrong, be right in the "
                      "middle and wrong at the ends, or be right only today.")),
            K["sys"],
        ]),
    ]


def chapter_05(K):
    from msalab.accuracy import (
        APPARENT_INFLATION_PCT, BIAS, BIASED_MISS, BIASED_RATIOS, CLEAN_MISS,
        CLEAN_RATIOS, DRIFT, DRIFT_PCT_TOL, DRIFT_OVER_GAUGE, DRIFT_PER_MONTH,
        DRIFT_TOTAL, GAUGE_SIGMA, GRR_BY_MONTH, LINEARITY, LINEAR_RATIOS,
        MASTER_CI, MASTER_READS, MONTHS, MONTH_MASTER_NOTICES, READS_FOR_BIAS,
        READS_FOR_HALF, READS_FOR_TENTH, REPEAT_SPREAD, SCRAP_MULTIPLE,
        STUDY_IMPROVEMENT,
    )
    return [
        ("s1", "5.1", "Four levels with a mean of zero", [
            para("Everything so far is made of variances. A repeatability, a "
                 "reproducibility, an interaction, and two ratios built out of "
                 "them. Not one of those quantities contains a term that says "
                 "where the readings sit \u2014 only how far apart they are.",
                 lead=True),
            para(f"So take the gauge those levels built, "
                 f"{GAUGE_SIGMA:.4f}&nbsp;\u00b5m, and make it read "
                 f"{BIAS:.0f}&nbsp;\u00b5m high. Everywhere, on every part, all "
                 f"day. Both of Level 4's percentages are unchanged \u2014 not "
                 f"approximately, not to two figures, but to the last decimal the "
                 f"arithmetic carries.",
                 datanote(("against study, centred",
                           f"{CLEAN_RATIOS['study']:.4f} %"),
                          (f"against study, {BIAS:.0f} \u00b5m high",
                           f"{BIASED_RATIOS['study']:.4f} %"),
                          ("against tolerance, centred",
                           f"{CLEAN_RATIOS['tolerance']:.4f} %"),
                          (f"against tolerance, {BIAS:.0f} \u00b5m high",
                           f"{BIASED_RATIOS['tolerance']:.4f} %"),
                          k="the same gauge, moved off centre")),
            para("A standard deviation is computed from the distances between "
                 "readings and their own mean. Shift every reading by the same "
                 "amount and those distances are identical. There is nowhere in "
                 "either formula for a bias to enter, so this is not a weakness "
                 "of the method \u2014 it is what the method is.",
                 note("what R&R is for", text="It answers whether the gauge can "
                      "distinguish. Whether it is correct is a different "
                      "question, and it needs a different instrument.")),
            K["fig"]("Level05.mp4"),
        ]),
        ("s2", "5.2", "The scrap bill is not blind", [
            para("The percentages do not move. The factory does.", lead=True),
            para(f"With the gauge centred, "
                 f"{CLEAN_MISS['good_rejected_pct']:.2f}&nbsp;% of the parts that "
                 f"are genuinely inside tolerance get rejected anyway, and the "
                 f"mistakes split evenly between the two limits \u2014 exactly "
                 f"evenly, because the arithmetic is symmetric. Add the "
                 f"{BIAS:.0f}&nbsp;\u00b5m and that rate goes to "
                 f"{BIASED_MISS['good_rejected_pct']:.2f}&nbsp;%, "
                 f"{SCRAP_MULTIPLE:.1f} times higher, and "
                 f"{BIASED_MISS['rejected_at_upper_pct']:.0f}&nbsp;% of it now "
                 f"happens at one limit.",
                 datanote(("good parts rejected, centred",
                           f"{CLEAN_MISS['good_rejected_pct']:.4f} %"),
                          ("of those, at the upper limit",
                           f"{CLEAN_MISS['rejected_at_upper_pct']:.1f} %"),
                          (f"good parts rejected, {BIAS:.0f} \u00b5m high",
                           f"{BIASED_MISS['good_rejected_pct']:.4f} %"),
                          ("of those, at the upper limit",
                           f"{BIASED_MISS['rejected_at_upper_pct']:.1f} %"),
                          k="what the same bias does to the decision")),
            para("That asymmetry is the useful part, because noise cannot produce "
                 "it. A gauge that is merely imprecise throws away good parts in "
                 "both directions. When the rework bench only ever sees oversize "
                 "parts, the gauge is a better suspect than the process.",
                 note("what an operator sees", text="Not a percentage. A pattern "
                      "in which direction the rejects fall.")),
            K["fig"]("l05_1_precision_is_not_accuracy.png"),
            K["lab"],
        ]),
        ("s3", "5.3", "You cannot find it by measuring again", [
            para("Repeatability is measured by reading the same part twice. Bias "
                 "cannot be, at any sample size, because both readings carry it "
                 "equally. Ten thousand readings of an unknown part give a very "
                 "precise estimate of the spread and no information at all about "
                 "where that spread sits.",
                 lead=True),
            para(f"It takes a reference \u2014 something whose size is already "
                 f"known by better means. Then the question is whether a "
                 f"confidence interval on the mean error contains zero. "
                 f"{MASTER_READS} readings of a master that is truly "
                 f"{BIAS:.0f}&nbsp;\u00b5m out gave a mean error of "
                 f"{MASTER_CI['mean']:+.3f}&nbsp;\u00b5m and an interval of "
                 f"[{MASTER_CI['low']:+.3f}, {MASTER_CI['high']:+.3f}] \u2014 "
                 f"clear of zero, so detected, but only just.",
                 datanote(("readings of the master", f"{MASTER_READS}"),
                          ("mean error", f"{MASTER_CI['mean']:+.3f} \u00b5m"),
                          ("interval half-width",
                           f"{MASTER_CI['half_width']:.3f} \u00b5m"),
                          ("contains zero",
                           "no" if MASTER_CI["detected"] else "yes"),
                          k="one reference study")),
            f'{P}<div class="eq"><div class="eq-body" data-tex="n \\ge '
            f'\\left(\\frac{{(z_{{\\alpha/2}} + z_{{\\beta}})\\,'
            f'\\sigma_{{gauge}}}}{{\\delta}}\\right)^{{2}}">'
            f'</div><div class="eq-num">(5.1)</div></div>',
            para(f"The bias you want to catch sits in the denominator, and it is "
                 f"squared. Catching {BIAS:.0f}&nbsp;\u00b5m takes "
                 f"{READS_FOR_BIAS} readings. Halving that to "
                 f"{BIAS/2:.1f} does not double the work, it roughly quadruples "
                 f"it: {READS_FOR_HALF}. Chasing {BIAS/10:.1f}&nbsp;\u00b5m "
                 f"takes {READS_FOR_TENTH}. Precision gets cheaper with "
                 f"repetition, because averaging divides it by the root of the "
                 f"count. Accuracy does not, because it is not a spread.",
                 note("the asymmetry", text="Level 1 showed averaging buying "
                      "precision at one over root m. Here the same root works "
                      "against you.")),
        ]),
        ("s4", "5.4", "Linearity does not hide \u2014 it flatters", [
            para("The second way to be wrong is to be right in the middle and "
                 "wrong at the ends: a worn anvil, a fixture that does not locate "
                 "the same way across the range, a scale whose gain is off. The "
                 "error is then a fraction of the reading rather than a constant.",
                 lead=True),
            para(f"A slope of {LINEARITY:.2f} means a part ten microns oversize "
                 f"reads {10*LINEARITY:.1f}&nbsp;\u00b5m high. Because the error "
                 f"now grows with the part, it widens the spread of the readings: "
                 f"the apparent part variation rises from "
                 f"{LINEAR_RATIOS['true_part']:.2f}&nbsp;\u00b5m to "
                 f"{LINEAR_RATIOS['apparent_part']:.2f}, up "
                 f"{APPARENT_INFLATION_PCT:.0f}&nbsp;%. That spread is the "
                 f"denominator of the study ratio.",
                 datanote(("slope", f"{LINEARITY:.2f}"),
                          ("true part spread",
                           f"{LINEAR_RATIOS['true_part']:.2f} \u00b5m"),
                          ("apparent part spread",
                           f"{LINEAR_RATIOS['apparent_part']:.2f} \u00b5m"),
                          ("against study, linear",
                           f"{CLEAN_RATIOS['study']:.1f} %"),
                          ("against study, non-linear",
                           f"{LINEAR_RATIOS['study']:.1f} %"),
                          k="the defect that improves the score")),
            para(f"So the ratio <em>improves</em>, by "
                 f"{STUDY_IMPROVEMENT:.1f} points. The instrument's own defect is "
                 f"counted as process variation and the gauge is rewarded for "
                 f"having it. That is worse than a blind spot: a blind spot "
                 f"reports nothing, and this reports good news.",
                 note("why the tolerance ratio is unmoved", text="Its "
                      "denominator came off a drawing, so nothing the gauge does "
                      "can change it. Level 4, section two, in reverse.")),
            K["fig"]("l05_2_worse_than_invisible.png"),
        ]),
        ("s5", "5.5", "And it was right in March", [
            para("The third way to be wrong is to have been right. A gauge "
                 "drifts: a reference surface wears, a temperature compensation "
                 "goes stale, a battery sags. Nothing is wrong on any single day.",
                 lead=True),
            para(f"Run the same study on a master once a month for "
                 f"{MONTHS} months, with the gauge drifting "
                 f"{DRIFT_PER_MONTH}&nbsp;\u00b5m each month. By the end it "
                 f"reads {DRIFT_TOTAL:.2f}&nbsp;\u00b5m high \u2014 "
                 f"{DRIFT_OVER_GAUGE:.1f} times the gauge's own sigma and "
                 f"{DRIFT_PCT_TOL:.0f}&nbsp;% of the whole tolerance. And every "
                 f"study is internally fine: %GRR reads "
                 f"{GRR_BY_MONTH[0]:.4f}&nbsp;% every single month, and the "
                 f"repeatability estimates vary over only "
                 f"{REPEAT_SPREAD:.3f}&nbsp;\u00b5m across the year.",
                 datanote(("drift per month", f"{DRIFT_PER_MONTH} \u00b5m"),
                          ("total drift", f"{DRIFT_TOTAL:.2f} \u00b5m"),
                          ("as a share of tolerance",
                           f"{DRIFT_PCT_TOL:.1f} %"),
                          ("%GRR, every month", f"{GRR_BY_MONTH[0]:.4f} %"),
                          ("months a master read 'no bias'",
                           f"{DRIFT['months_undetected']} of {MONTHS}"),
                          k="a year of correct studies")),
            para(f"The reason is structural rather than statistical: the bias is "
                 f"constant <em>inside</em> one afternoon, so a study run in one "
                 f"afternoon has nothing to see. The drift exists only between "
                 f"studies, which means it is only visible if somebody kept the "
                 f"old ones and plotted them. Even with a master, a single month "
                 f"first notices at month {MONTH_MASTER_NOTICES}, and "
                 f"{DRIFT['months_undetected']} of the {MONTHS} months read as no "
                 f"bias at all.",
                 note("stability is a question about a sequence",
                      text="No single study answers it at any sample size. It "
                      "needs the old studies kept and compared, which is a "
                      "different discipline from this one.")),
            para("Five levels in, the honest summary is that R&amp;R answers one "
                 "question about a measurement system, and it is not the question "
                 "of whether the gauge is right. Which leaves one assumption "
                 "still standing, and it is the largest: that a reading is a "
                 "number at all.",
                 note("the seam ahead", text="Level 6 is the gauge that says "
                      "pass or fail. No variance, no sigma, no ratio \u2014 and "
                      "the same questions still have to be answered.")),
            K["sys"],
        ]),
    ]


CHAPTERS = {
    "level-01.html": {
        "number": 1, "word": "one",
        "before": "nothing \u2014 this is where the curriculum starts",
        "after": "Level 2 \u2014 repeatability and reproducibility",
        "estimate": "5 sections \u00b7 1 act \u00b7 1 interactive \u00b7 ~8 min read",
        "toc": [("1.1", "s1", "One part is a distribution",
                 "one bore has one size; two hundred readings have a shape"),
                ("1.2", "s2", "A reading is two things",
                 "the part, plus whatever the process did on that occasion"),
                ("1.3", "s3", "Variances add, standard deviations do not",
                 tex(r"\sigma_{obs}^2 = \sigma_{part}^2 + \sigma_{gauge}^2")
                 + " \u2014 cheap at first, brutal later"),
                ("1.4", "s4", "Real, and invisible",
                 "the effect is 4.3 %, one study spans 11 %, and 39 % point the wrong way"),
                ("1.5", "s5", "You cannot measure your way out",
                 "averaging divides the gauge term and never touches the parts")],
        "sections": chapter_01,
    },
    "level-02.html": {
        "number": 2, "word": "two",
        "before": "Level 1 \u2014 measurement as a process",
        "after": "Level 3 \u2014 Gage R&R by ANOVA",
        "estimate": "5 sections \u00b7 1 act \u00b7 1 interactive \u00b7 ~9 min read",
        "toc": [("2.1", "s1", "Two questions, one word",
                 "one operator disagreeing with themselves, or with each other"),
                ("2.2", "s2", "The offset has to persist",
                 "an offset that travels with the person, across every part"),
                ("2.3", "s3", "The same law, and the fix that follows",
                 tex(r"\sigma_{gauge}^2 = \sigma_{repeat}^2 + \sigma_{reprod}^2")
                 + " \u2014 and why one project is worth 3.7 of the other"),
                ("2.4", "s4", "The operator spread is not the operator effect",
                 "the estimator borrows repeatability, and mostly reports it"),
                ("2.5", "s5", "Wrong in both directions at once",
                 "uncorrected too high, clamped too low, 47 % pushed onto zero")],
        "sections": chapter_02,
    },
    "level-03.html": {
        "number": 3, "word": "three",
        "before": "Level 2 \u2014 repeatability and reproducibility",
        "after": "Level 4 \u2014 %GRR, ndc, and against what",
        "estimate": "5 sections \u00b7 1 act \u00b7 1 interactive \u00b7 ~9 min read",
        "toc": [("3.1", "s1", "One study, two arithmetics",
                 "ranges and a table, or sums of squares and nothing looked up"),
                ("3.2", "s2", "The term that only one of them has",
                 "non-parallel lines are the interaction, and it needs replication"),
                ("3.3", "s3", "Four terms, and no remainder",
                 tex(r"SS_{total} = SS_{part} + SS_{oper} + SS_{p \times o} + SS_{rep}")),
                ("3.4", "s4", "It does not misplace the interaction",
                 "it omits it, so the gauge comes out looking better than it is"),
                ("3.5", "s5", "Three hundred studies, because one settles nothing",
                 "43 % too small at the far end, and ANOVA's own bias named")],
        "sections": chapter_03,
    },
    "level-04.html": {
        "number": 4, "word": "four",
        "before": "Level 3 \u2014 Gage R&R by ANOVA",
        "after": "Level 5 \u2014 bias, linearity, stability",
        "estimate": "5 sections \u00b7 1 act \u00b7 1 interactive \u00b7 ~9 min read",
        "toc": [("4.1", "s1", "A verdict is not a variance",
                 "same numerator, two denominators, two questions"),
                ("4.2", "s2", "Only one of them can see the parts",
                 "improve the process and the study ratio gets worse"),
                ("4.3", "s3", "The same gauge, opposite verdicts",
                 "two factories, one instrument, both gates honest"),
                ("4.4", "s4", "The third number is the first one rearranged",
                 tex(r"1.41\,\sigma_{part}/\sigma_{gauge}")
                 + " \u2014 and its gate is 2.9 points tighter"),
                ("4.5", "s5", "A percentage is a proxy for a risk",
                 "shift the process and the risk moves while %GRR does not")],
        "sections": chapter_04,
    },
    "level-05.html": {
        "number": 5, "word": "five",
        "before": "Level 4 \u2014 %GRR, ndc, and against what",
        "after": "Level 6 \u2014 attribute agreement",
        "estimate": "5 sections \u00b7 1 act \u00b7 1 interactive \u00b7 ~9 min read",
        "toc": [("5.1", "s1", "Four levels with a mean of zero",
                 "shift every reading and not one number moves"),
                ("5.2", "s2", "The scrap bill is not blind",
                 "four times the rejections, and 99 % at one limit"),
                ("5.3", "s3", "You cannot find it by measuring again",
                 "it takes a reference, and then it takes 498 readings"),
                ("5.4", "s4", "Linearity does not hide \u2014 it flatters",
                 "the gauge's own defect counted as process variation"),
                ("5.5", "s5", "And it was right in March",
                 "6 \u00b5m of drift while %GRR reads the same every month")],
        "sections": chapter_05,
    },
}


def build_main(spec: dict, keep: dict) -> str:
    """Assemble one chapter from its spec."""
    n = spec["number"]
    figs = keep["figs"]

    def fig(name):
        f = figs.get(name)
        if f is None:
            sys.exit(f"chapterise: figure {name} missing (have: {sorted(figs)})")
        return re.sub(r"<figure[^>]*>", "<figure>", f, count=1)

    def watch(mp4, poster, label, caption):
        """A referenced act that is not this section's subject.

        It was a 340px margin card, which measured 323x182 on screen - an
        unwatchable player for a 1920-wide render, where an axis label is a
        smear. It is now a collapsed player in the text block: a poster strip
        closed, the full text-block width open. Compact by default, watchable on
        demand, and no JavaScript. The media path is lifted from the figure being
        demoted so it cannot drift.
        """
        src = next((s for s in figs.values() if mp4 in s), None)
        if src is None:
            sys.exit(f"chapterise: no figure to demote for {mp4}")
        path = re.search(r'src="([^"]+' + re.escape(mp4) + r')"', src).group(1)
        dur = re.search(r"(\d+:\d\d)", caption)
        return ('      <details class="act">\n'
                '        <summary>\n'
                '          <span class="thumb-wrap">'
                f'<img class="thumb" src="posters/{poster}.jpg" alt="" loading="lazy">'
                '</span>\n'
                '          <span class="meta">'
                f'<span class="k">{label}</span>'
                f'<span class="cap">{caption}</span></span>\n'
                f'          <span class="cue">play{" · " + dur.group(1) if dur else ""}</span>\n'
                '        </summary>\n'
                '        <video controls playsinline preload="none" '
                f'poster="posters/{poster}.jpg">\n'
                f'          <source src="{path}" type="video/mp4">\n'
                f'          <track kind="captions" src="captions/{poster}.vtt" srclang="en" '
                'label="English">\n'
                '        </video>\n'
                '      </details>')

    K = {**keep, "fig": fig, "watch": watch}

    toc_items = "\n".join(
        f'          <li><span class="n">{num}</span><a href="#{anchor}">{title}'
        f'<span class="sub">{sub}</span></a></li>'
        for num, anchor, title, sub in spec["toc"])

    L = []
    A = L.append
    A("  <main>")
    A('    <header class="ch">')
    A('      <div class="leaf">')
    A("        <div>")
    A(f'          <p class="ch-no">Level {n} · chapter {spec["word"]}</p>')
    A('          <h1 class="page-title"></h1>')
    A('          <p class="dek page-dek"></p>')
    A("        </div>")
    A("      </div>")
    A('      <div class="toc">')
    A('        <div class="toc-head"><span class="micro">What this chapter derives</span>'
      f'<span class="micro est">{spec["estimate"]}</span></div>')
    A('        <p class="toc-chain"><span class="micro">after</span> '
      f'{spec["before"].rstrip(".")}<span class="sep">·</span>'
      f'<span class="micro">leads to</span> {spec["after"].rstrip(".")}</p>')
    A("        <ol>")
    A(toc_items)
    A("        </ol>")
    A("      </div>")
    A("    </header>")

    for anchor, num, title, blocks in spec["sections"](K):
        A(f'    <section id="{anchor}">')
        A('      <div class="leaf">')
        A("        <div>")
        A(f'          <span class="sec-no">{num}</span>')
        A(f"          <h2>{title}</h2>")
        for b in blocks:
            A(b)
        A("        </div>")
        A("      </div>")
        A("    </section>")

    A("    " + keep["next"])
    A("  </main>")
    return "\n".join(L)


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    p = pathlib.Path(sys.argv[1])
    spec = CHAPTERS.get(p.name)
    if spec is None:
        sys.exit(f"chapterise: no chapter defined for {p.name} "
                 f"(have: {', '.join(sorted(CHAPTERS))})")

    # The pre-chapter source is tracked in the repo. The transform is not
    # idempotent, so it must never read its own output: regenerating from the
    # generated page would chapterise a chapter. These sources lived in /tmp for
    # one session, which is cleared at boot - a build input that does not survive
    # a reboot is not a build input.
    source = pathlib.Path(__file__).resolve().parent / "page-sources" / p.name
    if not source.exists():
        sys.exit(f"chapterise: no page source at {source}")
    html = source.read_text()

    if ".sec-no" not in html:
        html = html.replace("</style>", CHAPTER_CSS + "</style>", 1)
    html = html.replace("font-family:var(--serif);font-size:21px;",
                        "font-family:var(--serif);font-size:var(--body);")
    if "--body:21px" not in html:
        html = html.replace("    --measure:27em;", "    --body:21px;\n    --measure:27em;", 1)
    # the breakout band predates the chapter grammar; the page width is derived now
    html = re.sub(r"  @media \(min-width:1440px\)\{\n    :root\{ --figure:64rem \}\n"
                  r"    \.wrap\{ max-width:84rem \}\n  \}\n"
                  r"  @media \(min-width:1800px\)\{\n    :root\{ --figure:94rem \}\n"
                  r"    \.wrap\{ max-width:110rem \}\n  \}\n", "", html)

    keep = extract(html)
    new_main = build_main(spec, keep)

    old = html[html.index("<main"):html.index("</main>") + len("</main>")]
    html = html.replace(old, new_main, 1)

    # the standalone opener now duplicates the chapter opener: fold it in
    m = re.search(r'  <header class="opener">.*?</header>\n\n', html, re.S)
    if m:
        block = m.group(0)
        html = html.replace(block, "", 1)
        title = re.search(r"<h1>(.*?)</h1>", block, re.S)
        dek = re.search(r'<p class="dek">(.*?)</p>', block, re.S)
        if title:
            html = html.replace('<h1 class="page-title"></h1>',
                                f"<h1>{title.group(1).strip()}</h1>", 1)
        if dek:
            html = html.replace('<p class="dek page-dek"></p>',
                                f'<p class="dek">{dek.group(1).strip()}</p>', 1)

    # Anything `extract` kept must actually reach the page. chapter_05 was
    # written without K["lab"] and this shipped a level whose interactive was
    # silently dropped - the source still had it, the build still succeeded, and
    # only the browser noticed. A kept block that goes unused is a build error.
    # "eq" is deliberately absent: each chapter spec writes its own equations,
    # so the source's eq block is a template rather than something preserved.
    for name in ("lab", "sys", "next"):
        if keep[name] and keep[name] not in html:
            sys.exit(f"chapterise: {p.name} dropped the {name!r} block that "
                     f"the page source provides - the chapter spec never "
                     f"emitted K[{name!r}]")
    for fname, fig in keep["figs"].items():
        if fname not in html:
            sys.exit(f"chapterise: {p.name} dropped figure {fname} - "
                     f"the chapter spec never emitted it")

    p.write_text(html)
    print(f"{p.name}: chapter {spec['number']} — {len(spec['toc'])} sections, "
          f"{len(keep['figs'])} figures preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
