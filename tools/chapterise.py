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

    p.write_text(html)
    print(f"{p.name}: chapter {spec['number']} — {len(spec['toc'])} sections, "
          f"{len(keep['figs'])} figures preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
