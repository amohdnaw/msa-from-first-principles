"""LEVEL 3 act - 'The term the older arithmetic has no room for.'

Level 2 ended on an assumption: that each operator's offset is the same on every
part. This act breaks it, on screen, with a tracker.

- Part 1 puts the same sixty numbers through both arithmetics and lets them
  agree, because that agreement is why the older method survived.
- Part 2 sweeps an interaction into existence. The operator lines start parallel
  and cross; the F statistic reads out as they do. Nothing is asserted - the
  reader watches the term appear.
- Part 3 splits the total sum of squares into four and shows the remainder is
  zero, which is what makes the decomposition a fact.
- Part 4 grows the interaction again and shows one method's gauge growing with
  it while the other's does not move.
- Part 5 is the 300-study sweep, and the closing question.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level03_scene.py Level03
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level03_scene.py Level03
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, Group, Line, MathTex,
    Rectangle, Transform, TransformMatchingTex, VGroup, Write,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
    ValueTracker,
)

from msalab.act_style import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    RULE, SIGNAL_ALARM, SIGNAL_OK, gauge, micro, panel_label, prose,
    within_frame,
)
from msalab.anova import (
    BAD_INTERACTION, CLEAN_ANOVA, CLEAN_XBAR, OPERATORS, PARTS, SWEEP, TRIALS,
    anova, average_and_range, rr_from_anova, study,
)
from msalab.opening import (
    closed_jaws, gauge_jaws, hand_off, part_block, plain, record_strip,
    thing_caption, tick, two_panel, value_label,
)
from msalab.narration import NarratedCameraScene

OP_COLOURS = [DATA_GAUGE, DATA_OBSERVED, ACCENT]


def _centred(interaction: float) -> np.ndarray:
    """Operator cell means with each part's own mean removed."""
    cell = study(interaction=interaction)["readings"].mean(axis=2)
    return cell - cell.mean(axis=1, keepdims=True)


class Level03(NarratedCameraScene):
    def construct(self):
        self.part0_opening()
        self.part1_two_arithmetics()
        self.part2_the_term_appears()
        self.part3_nothing_left_over()
        self.part4_where_it_goes()
        self.part5_the_sweep()

    # ------------------------------------------------------------- part 0
    def part0_opening(self):
        """Plain-language opening. specs/act-opening-contract.md, mode B.

        Level 2 ended on an assumption nobody states: that a person who reads
        high, reads high on everything. This opening breaks it with two parts and
        three people, before any arithmetic is named.
        """
        panels = two_panel("the things", "the record")
        b1 = part_block(centre=LEFT * 4.5 + UP * 1.15)
        b2 = part_block(centre=LEFT * 4.5 + DOWN * 1.35)
        c1 = thing_caption("a small bore", b1)
        c2 = thing_caption("a big bore", b2)

        with self.say("Two bores this time, one small and one large, and three "
                      "people who will each measure both."):
            self.play(FadeIn(panels["all"]), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(b1), FadeIn(c1), run_time=0.6,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(b2), FadeIn(c2), run_time=0.6,
                      rate_func=rf.ease_out_sine)

        # the record: three rows of two readings, one row per person
        who = ("first person", "second person", "third person")
        colours = (SIGNAL_OK, INK, SIGNAL_ALARM)
        small = (0.4, 1.5, 2.6)
        big = (2.5, 1.4, 0.5)          # the order reverses: that IS the level
        rows = VGroup()
        marks = []
        for i, (name, col) in enumerate(zip(who, colours)):
            y = 1.35 - i * 0.95
            lab = within_frame(plain(name, 19, col).move_to([1.15, y, 0]),
                               f"opening row {i} label")
            line = Line([2.6, y, 0], [6.3, y, 0], stroke_color=RULE,
                        stroke_width=1.2)
            rows.add(lab, line)
            marks.append((y, col, small[i], big[i], line))

        with self.say("One row each, and a line to put their numbers on."):
            self.play(FadeIn(rows), run_time=0.9, rate_func=rf.ease_out_sine)

        def at(line, v):
            lo, hi = line.get_start()[0], line.get_end()[0]
            return [lo + (v / 3.0) * (hi - lo), line.get_center()[1], 0]

        d_small = VGroup(*[Dot(at(ln, s), radius=0.07, color=col)
                           for (y, col, s, bg, ln) in marks])
        with self.say("Here is the small bore. The first person reads it low, "
                      "the third reads it high, and the second sits between "
                      "them. So far this is exactly Level two."):
            self.play(FadeIn(d_small, scale=1.7), run_time=1.0,
                      rate_func=rf.ease_out_back)

        d_big = VGroup(*[Dot(at(ln, bg), radius=0.07, color=col).set_opacity(0.55)
                         for (y, col, s, bg, ln) in marks])
        with self.say("Now the large bore, with the same three people. And the "
                      "order has turned over. The one who read low now reads "
                      "high."):
            self.play(FadeIn(d_big, scale=1.7), run_time=1.1,
                      rate_func=rf.ease_out_back)

        verdict = within_frame(
            plain("the disagreement changes with the part.", 26,
                  INK_BRIGHT).move_to([2.9, -1.85, 0]), "opening verdict")
        with self.say("So the disagreement between people is not one number. It "
                      "depends on which part they are holding, and that is a "
                      "third thing neither of the first two levels has a name "
                      "for."):
            self.play(FadeIn(verdict, shift=DOWN * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        hand_off(self, VGroup(b1, b2, c1, c2), panels)
        self.play(FadeOut(Group(rows, d_small, d_big, verdict)), run_time=0.6,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 1
    def part1_two_arithmetics(self):
        title = prose("Level 3 · two arithmetics, sixty numbers", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Ten parts, three operators, three trials each. Sixty "
                      "numbers, and two completely different ways to reduce them."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        left = within_frame(
            VGroup(
                panel_label("average-and-range", 24, DATA_OBSERVED),
                panel_label("ranges inside each cell", 19, INK_DIM),
                panel_label("a table of constants", 19, INK_DIM),
                panel_label("three terms", 19, INK_DIM),
            ).arrange(DOWN, buff=0.24, aligned_edge=LEFT).move_to(LEFT * 3.4 + UP * 0.6),
            "part 1 left column")
        right = within_frame(
            VGroup(
                panel_label("ANOVA", 24, SIGNAL_OK),
                panel_label("sums of squares", 19, INK_DIM),
                panel_label("no constants at all", 19, INK_DIM),
                panel_label("four terms", 19, INK_DIM),
            ).arrange(DOWN, buff=0.24, aligned_edge=LEFT).move_to(RIGHT * 1.9 + UP * 0.6),
            "part 1 right column")

        with self.say("One reduces them with ranges and a printed table. The other "
                      "with sums of squares and nothing looked up."):
            self.play(FadeIn(left, shift=RIGHT * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(right, shift=LEFT * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        ansl = within_frame(
            panel_label(f"{CLEAN_XBAR:.2f} µm", 34, DATA_OBSERVED)
            .next_to(left, DOWN, buff=0.7), "part 1 left answer")
        ansr = within_frame(
            panel_label(f"{CLEAN_ANOVA:.2f} µm", 34, SIGNAL_OK)
            .next_to(right, DOWN, buff=0.7), "part 1 right answer")
        with self.say("On a well-behaved study they land in the same place. Which "
                      "is exactly why the older method survived in the plants for "
                      "decades - it is not wrong, and it is much easier by hand."):
            self.play(FadeIn(ansl), FadeIn(ansr), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_the_term_appears(self):
        title = prose("now let the operators disagree about particular parts",
                      29, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        lim = 7.2
        band = 2.6      # reserved for the readout: the teal line reaches -6.2
        axes = Axes(x_range=[0.4, PARTS + 0.6, 1], y_range=[-lim - band, lim, 3],
                    x_length=9.4, y_length=4.2, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.45)
        xl = panel_label("part", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        zero = Line(axes.c2p(0.4, 0), axes.c2p(PARTS + 0.6, 0),
                    stroke_color=RULE, stroke_width=1.4)

        with self.say("Here are the three operators again, with each part's own "
                      "average taken out, so what is left is the operator pattern."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      Create(zero), run_time=1.2, rate_func=rf.ease_in_out_sine)

        # pre-compute the endpoints so the tracker interpolates a real study at
        # each strength rather than a drawn approximation
        strengths = np.linspace(0.0, BAD_INTERACTION, 26)
        frames = [_centred(float(g)) for g in strengths]
        tables = [anova(study(interaction=float(g))["readings"]) for g in strengths]
        k = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(k.get_value() * (len(strengths) - 1)),
                               0, len(strengths) - 1))

        def lines():
            c = frames[idx()]
            g = VGroup()
            for i in range(OPERATORS):
                pts = [axes.c2p(j + 1, np.clip(c[j, i], -lim, lim))
                       for j in range(PARTS)]
                g.add(VGroup(*[Line(a, b, stroke_color=OP_COLOURS[i],
                                    stroke_width=3.2)
                               for a, b in zip(pts, pts[1:])]))
                g.add(*[Dot(q, radius=0.05, color=OP_COLOURS[i]) for q in pts])
            return g

        curves = always_redraw(lines)
        read = always_redraw(lambda: panel_label(
            f"interaction {strengths[idx()]:.2f} µm    F = "
            f"{tables[idx()]['f']['interaction']:5.2f}    p = "
            f"{tables[idx()]['p']['interaction']:.3f}", 22,
            SIGNAL_OK if tables[idx()]["p"]["interaction"] > 0.25 else SIGNAL_ALARM)
            .move_to(axes.c2p(5.5, -lim - band * 0.55)))
        self.add(curves, read)

        with self.say("With no interaction the lines are parallel. Each operator "
                      "has an offset and keeps it."):
            self.beat(1.4)

        with self.say("Now turn the interaction up. The offsets stop being "
                      "constant: an operator who reads low on one part reads high "
                      "on another, and the lines cross. That crossing is the whole "
                      "of it. There is nothing else in the study that shows it, and "
                      "the F test goes with it."):
            self.play(k.animate.set_value(1.0), run_time=5.4,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_nothing_left_over(self):
        title = prose("four terms, and no remainder", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        a = anova(study(interaction=BAD_INTERACTION)["readings"])
        ss = a["ss"]
        terms = [("parts", ss["part"], INK_BRIGHT),
                 ("operators", ss["operator"], DATA_OBSERVED),
                 ("interaction", ss["interaction"], ACCENT),
                 ("repeat", ss["repeat"], DATA_GAUGE)]

        total_w = 11.2
        bar = Rectangle(width=total_w, height=0.62, stroke_color=INK_DIM,
                        stroke_width=1.6, fill_opacity=0)
        bar.move_to(UP * 1.4)
        tag = within_frame(
            panel_label(f"total sum of squares  {ss['total']:.1f}", 22, INK)
            .next_to(bar, UP, buff=0.22), "part 3 total tag")

        with self.say("The other thing ANOVA gives you is an identity. Take the "
                      "total variation in all sixty numbers."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(bar), FadeIn(tag),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        x = bar.get_left()[0]
        segs = VGroup()
        labs = VGroup()
        for name, v, colour in terms:
            w = total_w * v / ss["total"]
            seg = Rectangle(width=w, height=0.62, fill_color=colour,
                            fill_opacity=0.62, stroke_color=colour,
                            stroke_width=1.2)
            seg.move_to([x + w / 2, bar.get_center()[1], 0])
            # the three small segments are narrower than their own labels, so
            # the labels alternate depth instead of overlapping each other
            lab = panel_label(f"{name}  {v / ss['total'] * 100:.1f} %", 18, colour)
            lab.next_to(seg, DOWN, buff=0.30 + 0.46 * (len(segs) % 2))
            segs.add(seg)
            labs.add(lab)
            x += w

        with self.say("It splits into exactly four pieces: the parts differing from "
                      "each other, the operators differing from each other, the "
                      "interaction between them, and the repeat error."):
            for seg, lab in zip(segs, labs):
                self.play(FadeIn(seg, shift=RIGHT * 0.08), FadeIn(lab),
                          run_time=0.62, rate_func=rf.ease_out_sine)

        resid = abs(ss["total"] - (ss["part"] + ss["operator"]
                                   + ss["interaction"] + ss["repeat"]))
        eq = within_frame(
            panel_label(f"remainder  {resid:.2e}", 24, SIGNAL_OK)
            .move_to(DOWN * 2.4), "part 3 remainder")
        with self.say("And nothing is left over. Not approximately - the remainder "
                      "is zero to floating point. That identity is what makes this "
                      "a decomposition rather than a convention, and average-and-"
                      "range has no such statement to make."):
            self.play(FadeIn(eq, shift=UP * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_where_it_goes(self):
        title = prose("where does the interaction go?", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        with self.say("So if the older method has no term for it, where does the "
                      "interaction end up? The answer is that it does not end up "
                      "anywhere."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        strengths = np.linspace(0.0, 3.4, 22)
        pre = []
        for g in strengths:
            reads = study(interaction=float(g))["readings"]
            pre.append((rr_from_anova(anova(reads))["gauge"],
                        average_and_range(reads)["gauge"],
                        float(np.sqrt(1.0 + 1.8 ** 2 + g ** 2))))
        k = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(k.get_value() * (len(strengths) - 1)),
                               0, len(strengths) - 1))

        axes = Axes(x_range=[0, 3.6, 1], y_range=[0, 5.0, 1],
                    x_length=8.6, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55)
        xl = panel_label("interaction, µm", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("gauge, µm", 19, INK_DIM)
        yl.next_to(axes.c2p(0, 5.0), RIGHT, buff=0.10).shift(UP * 0.08)

        truth_c = always_redraw(lambda: axes.plot(
            lambda x: np.sqrt(1.0 + 1.8 ** 2 + x ** 2),
            x_range=[0, max(1e-3, strengths[idx()])],
            color=DATA_TRUTH, stroke_width=3))
        anova_c = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(strengths[i], pre[i][0]),
                 axes.c2p(strengths[i + 1], pre[i + 1][0]),
                 stroke_color=SIGNAL_OK, stroke_width=3.5)
            for i in range(idx())]))
        xbar_c = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(strengths[i], pre[i][1]),
                 axes.c2p(strengths[i + 1], pre[i + 1][1]),
                 stroke_color=SIGNAL_ALARM, stroke_width=3.5)
            for i in range(idx())]))
        read = always_redraw(lambda: panel_label(
            f"truth {pre[idx()][2]:.2f}   ANOVA {pre[idx()][0]:.2f}   "
            f"X-bar-R {pre[idx()][1]:.2f}", 22, INK)
            .move_to(axes.c2p(1.8, 4.55)))

        self.play(Create(axes), FadeIn(xl), FadeIn(yl), run_time=0.9,
                  rate_func=rf.ease_in_out_sine)
        self.add(truth_c, anova_c, xbar_c, read)

        with self.say("The white line is the truth, and it climbs as the "
                      "interaction grows. ANOVA follows it. The older method does "
                      "not move, because there is no term in its arithmetic for "
                      "the thing that is changing."):
            self.play(k.animate.set_value(1.0), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        verdict = within_frame(
            prose("it does not misplace the interaction — it omits it", 28,
                  INK_BRIGHT).to_edge(UP, buff=0.38), "part 4 verdict")
        with self.say("Which means the gauge comes out looking better than it is. "
                      "Not noisier. Better. That is the failure mode nobody warns "
                      "you about."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(verdict, shift=DOWN * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_the_sweep(self):
        title = prose("three hundred studies at each point", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 3.6, 1], y_range=[-48, 10, 10],
                    x_length=8.8, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("interaction, µm", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("error against the true gauge, %", 19, INK_DIM)
        yl.next_to(axes.c2p(0, 10), RIGHT, buff=0.10).shift(UP * 0.08)
        zero = DashedLine(axes.c2p(0, 0), axes.c2p(3.6, 0), dash_length=0.14,
                          stroke_color=DATA_TRUTH, stroke_width=2)

        with self.say("One study cannot settle this - on the study we just watched, "
                      "ANOVA actually overshot. So here is the comparison done "
                      "properly: three hundred studies at each interaction "
                      "strength."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), Create(zero), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        xs = [r["interaction"] for r in SWEEP]
        for key, colour, name in [("anova_err", SIGNAL_OK, "ANOVA"),
                                  ("xbar_err", SIGNAL_ALARM, "average-and-range")]:
            pts = [axes.c2p(x, r[key]) for x, r in zip(xs, SWEEP)]
            path = VGroup(*[Line(a, b, stroke_color=colour, stroke_width=3.5)
                            for a, b in zip(pts, pts[1:])])
            marks = VGroup(*[Dot(q, radius=0.06, color=colour) for q in pts])
            tag = within_frame(
                panel_label(name, 20, colour).next_to(pts[-1], UP, buff=0.18),
                f"part 5 tag {name}")
            line = ("ANOVA stays within a few percent of the truth the whole way."
                    if name == "ANOVA" else
                    "Average-and-range walks away from it, and by the time the "
                    "interaction matches the operator term it is reporting a gauge "
                    "forty three percent too small.")
            with self.say(line):
                self.play(Create(path), FadeIn(marks), FadeIn(tag), run_time=1.8,
                          rate_func=rf.ease_in_out_sine)

        closing = prose("four numbers now. so which do you divide, and by what?",
                        29, INK_BRIGHT)
        closing.to_edge(UP, buff=0.38)
        with self.say("So the decomposition has four terms and one of them is "
                      "invisible to the older arithmetic. Which leaves the question "
                      "this has been building to. We have variances. A verdict "
                      "needs a percentage, and a percentage needs a denominator. "
                      "That is level four."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(closing, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
