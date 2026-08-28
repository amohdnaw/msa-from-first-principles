"""LEVEL 2 act - 'Two questions, one word.'

Level 1 ended on a gauge with a size. This act splits that size, and every
number in it arrives by movement:

- Part 1 names the two distances on one part, by measuring them.
- Part 2 sweeps across the parts to show that the operator offset *persists*,
  which is what makes it a different term rather than more noise. The lines come
  out parallel, and that parallelism is precisely what Level 3 breaks.
- Part 3 morphs Level 1's equation one level down and prices both fixes with a
  tracker, so the reader watches the asymmetry rather than being told it.
- Part 4 shows the operator-mean spread borrowing repeatability, and the
  borrowing shrinking as the study grows.
- Part 5 walks studies until the correction goes negative, and counts.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level02_scene.py Level02
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level02_scene.py Level02
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, Group, Line, MathTex,
    Rectangle, Restore, TransformMatchingTex, VGroup, Write,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
    ValueTracker,
)

from msalab.act_style import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    RULE, SIGNAL_ALARM, SIGNAL_OK, gauge, micro, panel_label, prose,
    within_frame,
)
from msalab.reproducibility import (
    NEGATIVE_PCT, NOISY_REPEAT, NOISY_REPRODUCE, OPERATORS, PARTS,
    REPRODUCE_DF, SIGMA_REPEAT, SIGMA_REPRODUCE, TRIALS, expected_naive,
    fix_value, gauge_sigma, operator_mean_spread, reproducibility, study,
)
from msalab.narration import NarratedCameraScene

OP_COLOURS = [DATA_GAUGE, DATA_OBSERVED, ACCENT]


class Level02(NarratedCameraScene):
    def construct(self):
        self.part1_two_distances()
        self.part2_the_offset_persists()
        self.part3_the_same_law_again()
        self.part4_the_estimator_borrows()
        self.part5_the_boundary()

    # ------------------------------------------------------------- part 1
    def part1_two_distances(self):
        title = prose("Level 2 · two questions, one word", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Level one left us with a gauge that has a size. Ask how it "
                      "was measured and there are two different questions hiding "
                      "in the answer."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-0.6, 2.6, 1], y_range=[-6.0, 2.0, 2],
                    x_length=8.6, y_length=4.3, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.35)
        # A rotated y-label ran 0.4 units off the left edge and the guard caught
        # it before a frame rendered. Horizontal, above the axis, costs nothing.
        yl = within_frame(
            panel_label("reading on one part, µm", 20, INK_DIM)
            .next_to(axes.c2p(-0.6, 2.0), UP, buff=0.14, aligned_edge=LEFT),
            "part 1 y-label")

        s = study()
        cell = s["readings"][3]                    # (operators, trials)
        op_means = cell.mean(axis=1)

        with self.say("Here is one part, and three operators who are each going "
                      "to measure it three times."):
            self.play(Create(axes), FadeIn(yl), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        labels = VGroup()
        for i in range(OPERATORS):
            lab = panel_label(f"operator {chr(65+i)}", 19, OP_COLOURS[i])
            lab.next_to(axes.c2p(i, -6.0), DOWN, buff=0.22)
            labels.add(lab)
        self.play(FadeIn(labels), run_time=0.6, rate_func=rf.ease_out_sine)

        # operator A first, alone: this is repeatability and nothing else
        dots_a = VGroup(*[Dot(axes.c2p(0 + (k - 1) * 0.09, cell[0, k]),
                             radius=0.075, color=OP_COLOURS[0])
                          for k in range(TRIALS)])
        with self.say("Operator A goes first. Three readings of one part, and they "
                      "do not agree. That disagreement is repeatability - one "
                      "person, one part, one gauge, again."):
            for d in dots_a:
                self.play(FadeIn(d, scale=1.5), run_time=0.34,
                          rate_func=rf.ease_out_back)

        rep_span = Line(axes.c2p(-0.32, cell[0].min()),
                        axes.c2p(-0.32, cell[0].max()),
                        stroke_color=DATA_GAUGE, stroke_width=3.5)
        rep_tag = within_frame(
            panel_label(f"repeatability\n{cell[0].max()-cell[0].min():.1f} µm seen",
                        19, DATA_GAUGE)
            .next_to(rep_span, LEFT, buff=0.14), "part 1 repeat tag")
        with self.say("Call it the width of one operator's own answer."):
            self.play(Create(rep_span), FadeIn(rep_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # now B and C: a second, different distance appears
        with self.say("Now hand the same part to two other operators."):
            for i in (1, 2):
                grp = VGroup(*[Dot(axes.c2p(i + (k - 1) * 0.09, cell[i, k]),
                                   radius=0.075, color=OP_COLOURS[i])
                               for k in range(TRIALS)])
                self.play(FadeIn(grp, scale=1.4), run_time=0.55,
                          rate_func=rf.ease_out_back)

        mean_marks = VGroup(*[
            Line(axes.c2p(i - 0.22, op_means[i]), axes.c2p(i + 0.22, op_means[i]),
                 stroke_color=OP_COLOURS[i], stroke_width=4)
            for i in range(OPERATORS)])
        with self.say("Each operator has an average, and the averages are not the "
                      "same. That is a second distance, and it is a different "
                      "thing: reproducibility."):
            self.play(*[Create(m) for m in mean_marks], run_time=1.0,
                      rate_func=rf.ease_in_out_sine)

        rpr_span = Line(axes.c2p(2.42, op_means.min()), axes.c2p(2.42, op_means.max()),
                        stroke_color=INK_BRIGHT, stroke_width=3.5)
        rpr_tag = within_frame(
            panel_label(f"reproducibility\n{op_means.max()-op_means.min():.1f} µm",
                        19, INK_BRIGHT)
            .next_to(rpr_span, RIGHT, buff=0.14), "part 1 reproduce tag")
        with self.say("One word, R and R, covers both. They are not the same size "
                      "and they do not have the same fix."):
            self.play(Create(rpr_span), FadeIn(rpr_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_the_offset_persists(self):
        title = prose("the offset follows the operator, not the part", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        s = study()
        op_means = s["readings"].mean(axis=2)      # (parts, operators)
        lo = float(op_means.min()) - 1.5
        hi = float(op_means.max()) + 1.5

        axes = Axes(x_range=[0.4, PARTS + 0.6, 1], y_range=[lo, hi, 5],
                    x_length=9.6, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("part", 20, INK_DIM).next_to(axes, DOWN, buff=0.24)

        with self.say("Whether that second distance is real depends on one thing: "
                      "does it persist? Measure every part with every operator."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        # each operator's line is drawn as a sweep, so the parallelism is watched
        # rather than presented
        for i in range(OPERATORS):
            pts = [axes.c2p(k + 1, op_means[k, i]) for k in range(PARTS)]
            path = VGroup(*[Line(a, b, stroke_color=OP_COLOURS[i], stroke_width=3.5)
                            for a, b in zip(pts, pts[1:])])
            marks = VGroup(*[Dot(q, radius=0.055, color=OP_COLOURS[i]) for q in pts])
            tag = within_frame(
                panel_label(f"{chr(65+i)}", 20, OP_COLOURS[i])
                .next_to(pts[-1], RIGHT, buff=0.16), f"part 2 tag {i}")
            line = ("Operator A reads low on every part." if i == 0 else
                    "B reads higher." if i == 1 else
                    "C sits close to B. The gaps hold across all ten parts, so "
                    "they belong to the operators.")
            with self.say(line):
                self.play(Create(path), FadeIn(marks), FadeIn(tag),
                          run_time=1.5, rate_func=rf.ease_in_out_sine)

        with self.say("Roughly parallel lines. An offset that travels with the "
                      "person is reproducibility; if these lines crossed each "
                      "other the story would be different, and that is level "
                      "three."):
            self.beat(1.4)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_the_same_law_again(self):
        title = prose("the same law, one level down", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        old = MathTex(r"\sigma_{gauge}^2", font_size=46, color=INK)
        old.move_to(UP * 1.9)
        with self.say("Level one called the whole thing the gauge term."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Write(old), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        new = MathTex(r"\sigma_{gauge}^2", "=", r"\sigma_{repeat}^2", "+",
                      r"\sigma_{reprod}^2", font_size=46, color=INK_BRIGHT)
        new.move_to(old)
        with self.say("It splits the same way everything in this subject splits. "
                      "Variances add."):
            self.play(TransformMatchingTex(old, new), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        # the two fixes, priced by a tracker rather than stated
        axes = Axes(x_range=[0, 1.05, 0.25], y_range=[0, 42, 10],
                    x_length=8.8, y_length=3.4, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 1.55)
        xl = panel_label("how far you improve the term (1 = remove it entirely)",
                         19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("% better gauge", 19, INK_DIM)
        yl.next_to(axes.c2p(0, 42), RIGHT, buff=0.12).shift(UP * 0.10)

        f = ValueTracker(0.0)
        rep_curve = always_redraw(lambda: axes.plot(
            lambda x: fix_value("repeat", factor=1.0 - x),
            x_range=[0, max(1e-4, f.get_value())],
            color=DATA_GAUGE, stroke_width=4))
        rpr_curve = always_redraw(lambda: axes.plot(
            lambda x: fix_value("reproduce", factor=1.0 - x),
            x_range=[0, max(1e-4, f.get_value())],
            color=DATA_OBSERVED, stroke_width=4))
        read = always_redraw(lambda: panel_label(
            f"improve by {f.get_value()*100:3.0f} %   "
            f"repeat {fix_value('repeat', 1-f.get_value()):5.1f} %   "
            f"reprod {fix_value('reproduce', 1-f.get_value()):5.1f} %",
            22, INK).move_to(axes.c2p(0.52, 37.0)))

        with self.say("Now improve one of them and watch what the gauge does."):
            self.play(Create(axes), FadeIn(xl), FadeIn(yl), run_time=0.9,
                      rate_func=rf.ease_in_out_sine)
            self.add(rep_curve, rpr_curve, read)

        with self.say("Halve the repeatability and the gauge improves by nine "
                      "percent. Halve the reproducibility instead and it improves "
                      "by thirty five. Same effort, nearly four times the return, "
                      "and the only thing that decided it was which term was "
                      "bigger to begin with."):
            self.play(f.animate.set_value(1.0), run_time=4.6,
                      rate_func=rf.ease_in_out_sine)

        # inside the plot it sat on the repeatability curve; the title's slot is
        # empty by then and a conclusion arriving there reads as the answer
        verdict = within_frame(
            prose("fix the gauge is not advice until you know which half", 29,
                  INK_BRIGHT).to_edge(UP, buff=0.38), "part 3 verdict")
        with self.say("Which is why telling somebody to fix the gauge is not "
                      "advice."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(verdict, shift=DOWN * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.0)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_the_estimator_borrows(self):
        title = prose("the operator spread is not the operator effect", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 62, 15], y_range=[0.3, 1.45, 0.3],
                    x_length=9.4, y_length=4.1, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("readings behind each operator average (parts x trials)",
                         19, INK_DIM).next_to(axes, DOWN, buff=0.24)

        with self.say("There is a trap in measuring the operator term. Each "
                      "operator's average is itself made of noisy readings, so the "
                      "spread of those averages carries repeatability inside it."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)

        truth = DashedLine(axes.c2p(0, NOISY_REPRODUCE),
                           axes.c2p(62, NOISY_REPRODUCE),
                           dash_length=0.14, stroke_color=DATA_TRUTH,
                           stroke_width=2)
        truth_tag = within_frame(
            panel_label(f"the real operator term: {NOISY_REPRODUCE} µm", 19, DATA_TRUTH)
            .next_to(axes.c2p(30, NOISY_REPRODUCE), DOWN, buff=0.16),
            "part 4 truth tag")
        with self.say("On a gauge whose repeatability is large, this matters a "
                      "lot. The real operator term here is four tenths of a "
                      "micron."):
            self.play(Create(truth), FadeIn(truth_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        n = ValueTracker(6.0)
        curve = always_redraw(lambda: axes.plot(
            lambda x: expected_naive(NOISY_REPEAT, NOISY_REPRODUCE,
                                     parts=max(2, int(x)), trials=1),
            x_range=[6, max(6.1, n.get_value())],
            color=SIGNAL_ALARM, stroke_width=4))
        head = always_redraw(lambda: Dot(
            axes.c2p(n.get_value(),
                     expected_naive(NOISY_REPEAT, NOISY_REPRODUCE,
                                    parts=max(2, int(n.get_value())), trials=1)),
            radius=0.075, color=ACCENT))
        read = always_redraw(lambda: panel_label(
            f"{int(n.get_value()):>2} readings   operator spread reads "
            f"{expected_naive(NOISY_REPEAT, NOISY_REPRODUCE, parts=max(2, int(n.get_value())), trials=1):.3f}",
            22, INK).move_to(axes.c2p(22, 1.38)))
        self.add(curve, head, read)

        with self.say("With only a handful of readings behind each average, the "
                      "spread of the averages is nearly double the truth. Almost "
                      "all of what it is reporting is the instrument, not the "
                      "people."):
            self.play(n.animate.set_value(30.0), run_time=3.0,
                      rate_func=rf.ease_out_sine)

        with self.say("Grow the study and the borrowed part shrinks, because it "
                      "enters divided by the number of readings. It never quite "
                      "vanishes."):
            self.play(n.animate.set_value(60.0), run_time=2.4,
                      rate_func=rf.ease_in_out_sine)

        eq = within_frame(
            MathTex(r"\sigma^2_{\text{operator means}}", "=",
                    r"\sigma_{reprod}^2", "+",
                    r"\frac{\sigma_{repeat}^2}{parts \times trials}",
                    font_size=34, color=INK_BRIGHT)
            .move_to(axes.c2p(38, 1.12)), "part 4 equation")
        with self.say("So the honest estimate subtracts the borrowed term. That "
                      "subtraction is not a refinement. On this gauge two thirds "
                      "of the naive number was never about the operators at all."):
            self.play(Write(eq), run_time=1.6)

        self.beat(1.0)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_the_boundary(self):
        title = prose("and then it goes negative", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        raws = []
        for k in range(1, 25):
            reads = study(seed=500 + k, repeat=NOISY_REPEAT,
                          reproduce=NOISY_REPRODUCE)["readings"]
            raws.append(reproducibility(reads, clamp=False))
        # the axis is fitted to the data rather than guessed: clamping the drawn
        # value to a floor stacked every negative study on one line and they all
        # looked like the same result
        floor = min(raws) - 0.08
        axes = Axes(x_range=[0, 24, 6], y_range=[floor, 1.15, 0.4],
                    x_length=9.4, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("studies, one after another", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)
        zero = Line(axes.c2p(0, 0), axes.c2p(24, 0), stroke_color=INK_DIM,
                    stroke_width=1.6)
        truth = DashedLine(axes.c2p(0, NOISY_REPRODUCE),
                           axes.c2p(24, NOISY_REPRODUCE), dash_length=0.14,
                           stroke_color=DATA_TRUTH, stroke_width=2)

        with self.say("Subtracting one estimate from another has a consequence. "
                      "The answer is not guaranteed to be a variance."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      Create(zero), Create(truth), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)

        neg = 0
        marks = VGroup()
        counter = always_redraw(lambda: panel_label(
            f"clamped to zero: {neg} of {len(marks)}", 22, ACCENT)
            .move_to(axes.c2p(17.0, 1.02)))
        self.add(counter)

        with self.say("Run study after study on that same noisy gauge. Every time "
                      "the subtraction lands below zero, the result is reported as "
                      "zero - no operator effect at all."):
            for k, v in enumerate(raws, start=1):
                colour = SIGNAL_ALARM if v < 0 else SIGNAL_OK
                d = Dot(axes.c2p(k, v),
                        radius=0.065, color=colour)
                marks.add(d)
                if v < 0:
                    neg += 1
                self.play(FadeIn(d, scale=1.6), run_time=0.13,
                          rate_func=rf.ease_out_back)

        with self.say(f"On this gauge it happens about {NEGATIVE_PCT:.0f} percent "
                      f"of the time. And because zero is a floor and not a "
                      f"correction, the reported number now runs low - the "
                      f"uncorrected one ran high. The same study is wrong in both "
                      f"directions."):
            self.beat(1.6)

        for m in self.mobjects:
            m.clear_updaters()
        closing = prose("two operators' worth of evidence, and one word for two things",
                        28, INK_BRIGHT)
        closing.to_edge(UP, buff=0.38)
        with self.say(f"Three operators give {REPRODUCE_DF} degrees of freedom on "
                      f"the operator term, which is about fifty percent of error. "
                      f"So we have split the gauge, and we still cannot see "
                      f"whether the operators disagree about particular parts. "
                      f"That is the next level."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(closing, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
