"""LEVEL 1 act - 'A gauge is a process, and it has variation.'

Written against specs/msa-curriculum-contract.md and the SPC craft contract it
inherits. Five parts, each *deriving* its number by movement rather than typing
it: a tracker sweeps, the geometry follows, and the readout reads whatever the
geometry now says.

What this act has to earn:

- Part 1 shows a part with ONE true size producing a distribution. The spread
  is not asserted, it accumulates as readings land.
- Part 2 decomposes a single reading into truth plus error, with the camera
  moving in, so "the gauge is a process" is a picture rather than a phrase.
- Part 3 derives the quadrature law. The wrong equation is written first and
  then *morphed* into the right one, because the mistake is the interesting
  part: standard deviations look like they should add.
- Part 4 sweeps the gauge ratio and lets the reader watch the cost curve bend -
  cheap at first, brutal later - then reads the inverse off the same curve.
- Part 5 sweeps the number of repeats into the floor it cannot cross.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level01_scene.py Level01
    narrated: SPCLAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level01_scene.py Level01
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
    RULE, SIGNAL_ALARM, gauge, micro, panel_label, prose, within_frame,
)
from msalab.measurement import (
    FLOOR, GAUGE_SIGMA, ONE_PART_READS, ONE_PART_SD, ONE_PART_TRUE, OBSERVED_EXACT,
    PART_SIGMA, RATIO_FOR_10PCT, REPEATS_FOR_1PCT, WIDENING_PCT,
    averaging_floor, inflation, observed_sigma,
)
from msalab.narration import NarratedCameraScene


class Level01(NarratedCameraScene):
    def construct(self):
        self.part1_one_part_is_a_distribution()
        self.part2_a_reading_is_truth_plus_error()
        self.part3_variances_add()
        self.part4_cheap_then_brutal()
        self.part5_the_floor()

    # ------------------------------------------------------------- part 1
    def part1_one_part_is_a_distribution(self):
        title = prose("Level 1 · a gauge is a process", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("This is one bore, machined once. It has exactly one size."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-4.2, 4.2, 1], y_range=[0, 32, 5],
                    x_length=9.4, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.45)
        xl = within_frame(
            panel_label("reading, µm from nominal").next_to(axes, DOWN, buff=0.28),
            "part 1 x-label")

        # the part's one true size: a single bright line, no distribution yet
        truth_line = Line(axes.c2p(ONE_PART_TRUE, 0), axes.c2p(ONE_PART_TRUE, 23),
                          stroke_color=DATA_TRUTH, stroke_width=3)
        truth_tag = within_frame(
            prose("its one true size", 22, DATA_TRUTH)
            .next_to(axes.c2p(ONE_PART_TRUE, 23), UP, buff=0.14),
            "part 1 truth tag")

        with self.say("One size, and nothing has been measured yet."):
            self.play(Create(axes), FadeIn(xl), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(truth_line), FadeIn(truth_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # ---- the readings accumulate into a histogram, live
        rng = np.random.default_rng(21)
        reads = ONE_PART_TRUE + rng.normal(0.0, GAUGE_SIGMA, ONE_PART_READS)
        edges = np.linspace(-4.2, 4.2, 27)
        landed = ValueTracker(0.0)

        def bars():
            k = int(landed.get_value())
            counts, _ = np.histogram(reads[:k], bins=edges)
            g = VGroup()
            for i, c in enumerate(counts):
                if c == 0:
                    continue
                lo, hi = edges[i], edges[i + 1]
                bl = axes.c2p(lo, 0)
                tr = axes.c2p(hi, c)
                g.add(Rectangle(width=tr[0] - bl[0], height=tr[1] - bl[1],
                                fill_color=DATA_GAUGE, fill_opacity=0.55,
                                stroke_color=DATA_GAUGE, stroke_width=1.0)
                      .move_to((bl + tr) / 2))
            return g

        hist = always_redraw(bars)
        self.add(hist)

        # the readout is a function of what has landed, so it cannot disagree
        sd_read = always_redraw(lambda: panel_label(
            f"s  = {np.std(reads[:max(2, int(landed.get_value()))], ddof=1):.2f} µm",
            26, DATA_GAUGE).move_to(axes.c2p(-2.8, 27.5)))
        n_read = always_redraw(lambda: panel_label(
            f"readings = {int(landed.get_value()):>3}", 22, INK_DIM)
            .next_to(sd_read, DOWN, buff=0.16, aligned_edge=LEFT))
        self.add(sd_read, n_read)

        with self.say("Measure it once, and again, and two hundred times. The bore "
                      "has not changed. The readings have a shape, a centre and a "
                      "spread of their own."):
            self.play(landed.animate.set_value(ONE_PART_READS), run_time=4.4,
                      rate_func=rf.ease_in_out_sine)

        span = Line(axes.c2p(reads.min(), 29.4), axes.c2p(reads.max(), 29.4),
                    stroke_color=INK_DIM, stroke_width=1.6)
        span_tag = within_frame(
            panel_label(f"{reads.max() - reads.min():.1f} µm of spread", 20, INK_DIM)
            .next_to(span, UP, buff=0.12), "part 1 span tag")
        with self.say("One true size. Seven microns of spread on the screen. That "
                      "spread belongs to the gauge, not to the part."):
            self.play(Create(span), FadeIn(span_tag), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_a_reading_is_truth_plus_error(self):
        title = prose("every reading is two things", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)
        with self.say("So a reading is never just the part."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        base = Line(LEFT * 5.4, RIGHT * 5.4, stroke_color=RULE, stroke_width=1.5)
        base.shift(DOWN * 0.6)
        zero = base.get_left()

        def x_at(um):
            return zero + RIGHT * (um + 6.0) * (10.8 / 12.0)

        truth_mark = Line(x_at(0.0) + UP * 0.34, x_at(0.0) + DOWN * 0.34,
                          stroke_color=DATA_TRUTH, stroke_width=3)
        truth_lab = within_frame(
            prose("the part", 22, DATA_TRUTH)
            .next_to(truth_mark, UP, buff=0.5), "part 2 truth label")

        err = ValueTracker(0.0)
        reading = always_redraw(lambda: Dot(
            x_at(err.get_value()), radius=0.10, color=DATA_OBSERVED))
        arrow = always_redraw(lambda: Line(
            x_at(0.0), x_at(err.get_value()),
            stroke_color=DATA_OBSERVED, stroke_width=4))
        read_out = always_redraw(lambda: panel_label(
            f"reading = part {err.get_value():+.2f} µm", 24, DATA_OBSERVED)
            .move_to(base.get_center() + DOWN * 1.25))

        with self.say("It is the part, plus whatever the measurement process did "
                      "on that occasion."):
            self.play(Create(base), Create(truth_mark), FadeIn(truth_lab),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.add(arrow, reading, read_out)

        # camera moves in so the error term is the whole screen
        self.camera.frame.save_state()
        rng = np.random.default_rng(7)
        draws = rng.normal(0.0, GAUGE_SIGMA, 7)
        with self.say("Watch the error, not the part. The part is fixed. The error "
                      "is a draw from the gauge's own distribution, and it lands "
                      "somewhere new every time."):
            self.play(self.camera.frame.animate.scale(0.62)
                      .move_to(base.get_center() + DOWN * 0.35),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)
            for d in draws:
                self.play(err.animate.set_value(float(d)), run_time=0.42,
                          rate_func=rf.ease_in_out_sine)

        with self.say("That distribution is the thing this whole subject studies."):
            self.play(Restore(self.camera.frame), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        self.beat(0.8)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_variances_add(self):
        title = prose("so how much wider?", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)
        with self.say("If the reading is the part plus an error, the spread you "
                      "observe must be wider than the spread of the parts. The "
                      "question is by how much."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        # the tempting answer, written first because it is what people expect
        wrong = MathTex(r"\sigma_{obs}", "=", r"\sigma_{part}", "+", r"\sigma_{gauge}",
                        font_size=44, color=INK)
        wrong.move_to(UP * 1.55)
        with self.say("The tempting answer is that the two spreads add."):
            self.play(Write(wrong), run_time=1.2)

        # a right triangle, because that is what the true law is
        o = np.array([-3.4, -1.5, 0.0])
        scale = 0.62
        leg_a = Line(o, o + RIGHT * PART_SIGMA * scale,
                     stroke_color=DATA_TRUTH, stroke_width=5)
        leg_b = Line(leg_a.get_end(), leg_a.get_end() + UP * GAUGE_SIGMA * scale,
                     stroke_color=DATA_GAUGE, stroke_width=5)
        hyp = Line(o, leg_b.get_end(), stroke_color=DATA_OBSERVED, stroke_width=5)
        la = panel_label(f"parts {PART_SIGMA}", 20, DATA_TRUTH).next_to(leg_a, DOWN, buff=0.18)
        lb = panel_label(f"gauge {GAUGE_SIGMA}", 20, DATA_GAUGE).next_to(leg_b, RIGHT, buff=0.16)

        with self.say("It is not. Independent variation adds the way the sides of a "
                      "right triangle do."):
            self.play(Create(leg_a), FadeIn(la), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(Create(leg_b), FadeIn(lb), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(Create(hyp), run_time=1.0, rate_func=rf.ease_in_out_sine)

        right = MathTex(r"\sigma_{obs}^2", "=", r"\sigma_{part}^2", "+",
                        r"\sigma_{gauge}^2", font_size=44, color=INK_BRIGHT)
        right.move_to(wrong)
        with self.say("The variances add. The standard deviations do not."):
            self.play(TransformMatchingTex(wrong, right), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        # the hypotenuse reads its own length
        hyp_read = within_frame(
            panel_label(f"observed = {observed_sigma():.2f} µm", 24, DATA_OBSERVED)
            .next_to(hyp.get_center(), UP + LEFT, buff=0.30), "part 3 hyp readout")
        naive = within_frame(
            panel_label(f"adding them would say {PART_SIGMA + GAUGE_SIGMA:.1f}", 20, INK_DIM)
            .next_to(hyp_read, DOWN, buff=0.18, aligned_edge=LEFT), "part 3 naive")
        with self.say(f"Four point seven and one point four give four point nine, "
                      f"not six point one. The gauge is a quarter of the part "
                      f"spread and it costs {WIDENING_PCT:.1f} percent."):
            self.play(FadeIn(hyp_read), run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(FadeIn(naive), run_time=0.7, rate_func=rf.ease_out_sine)

        self.beat(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_cheap_then_brutal(self):
        title = prose("cheap at first, brutal later", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 1.05, 0.25], y_range=[0, 45, 10],
                    x_length=9.0, y_length=4.1, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55)
        xl = panel_label("gauge spread, as a fraction of the part spread", 20, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.26)
        yl = panel_label("% wider", 20, INK_DIM).next_to(axes.y_axis, UP, buff=0.18)

        with self.say("Sweep the gauge from perfect to as bad as the parts "
                      "themselves, and watch what it costs."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes),
                      FadeIn(xl), FadeIn(yl), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)

        r = ValueTracker(0.0)
        curve = always_redraw(lambda: axes.plot(
            lambda x: (inflation(x) - 1.0) * 100.0,
            x_range=[0, max(1e-4, r.get_value())],
            color=DATA_OBSERVED, stroke_width=4))
        head = always_redraw(lambda: Dot(
            axes.c2p(r.get_value(), (inflation(r.get_value()) - 1.0) * 100.0),
            radius=0.075, color=ACCENT))
        read = always_redraw(lambda: panel_label(
            f"gauge {r.get_value()*100:5.1f} %   ->  "
            f"{(inflation(r.get_value())-1)*100:5.1f} % wider", 24, INK)
            .move_to(axes.c2p(0.30, 38.0)))
        self.add(curve, head, read)

        with self.say("A gauge at a tenth of the part spread costs half a percent. "
                      "At a third it costs four. The curve is almost flat here, "
                      "which is why a mediocre gauge often goes unnoticed."):
            self.play(r.animate.set_value(0.35), run_time=2.6,
                      rate_func=rf.ease_out_sine)

        with self.say("Then it bends. A gauge as noisy as the parts inflates what "
                      "you see by forty one percent."):
            self.play(r.animate.set_value(1.0), run_time=2.8,
                      rate_func=rf.ease_in_sine)

        # read the inverse off the same curve
        mark = DashedLine(axes.c2p(0, 10), axes.c2p(RATIO_FOR_10PCT, 10),
                          dash_length=0.13, stroke_color=ACCENT, stroke_width=2)
        drop = DashedLine(axes.c2p(RATIO_FOR_10PCT, 10), axes.c2p(RATIO_FOR_10PCT, 0),
                          dash_length=0.13, stroke_color=ACCENT, stroke_width=2)
        # One line was long enough to reach x = 0.55, where the curve has already
        # climbed into it. Two short lines in the upper-left stay clear of both
        # the curve and the readout above them.
        inv = within_frame(
            panel_label(f"10 % wider needs\na gauge at {RATIO_FOR_10PCT*100:.0f} %",
                        22, ACCENT).move_to(axes.c2p(0.155, 25.0)),
            "part 4 inverse")
        with self.say("Read it the other way and it is uncomfortable. Your gauge may "
                      "be nearly half the part spread before the histogram is ten "
                      "percent too wide. Small effects hide easily."):
            self.play(Create(mark), Create(drop), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(inv), run_time=0.8, rate_func=rf.ease_out_sine)

        self.beat(1.0)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_the_floor(self):
        title = prose("and you cannot measure your way out", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 26, 5], y_range=[4.66, 4.95, 0.05],
                    x_length=9.0, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("repeats averaged per part", 20, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.26)

        floor = DashedLine(axes.c2p(0, FLOOR), axes.c2p(26, FLOOR),
                           dash_length=0.15, stroke_color=DATA_TRUTH,
                           stroke_width=2)
        # under the line and hard left: at x = 19.5 it sat on its own dashes and
        # on the curve's flat tail at the same time
        floor_tag = within_frame(
            panel_label(f"the parts: {FLOOR} µm", 20, DATA_TRUTH)
            .next_to(axes.c2p(1.6, FLOOR), DOWN, buff=0.20, aligned_edge=LEFT),
            "part 5 floor tag")

        with self.say("The obvious move is to measure each part several times and "
                      "average. It works, and it has a floor."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.1, rate_func=rf.ease_in_out_sine)
            self.play(Create(floor), FadeIn(floor_tag), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        m = ValueTracker(1.0)
        # rounding a continuous x produced a staircase with a vertical cliff at
        # m = 1. The quantity only exists at integers, so the line joins the
        # integer points and nothing is invented between them.
        def steps():
            k = max(1, int(m.get_value()))
            pts = [axes.c2p(i, averaging_floor(i)) for i in range(1, k + 1)]
            if len(pts) < 2:
                return VGroup(Dot(pts[0], radius=0.055, color=DATA_GAUGE))
            g = VGroup(*[Line(a, b, stroke_color=DATA_GAUGE, stroke_width=4)
                         for a, b in zip(pts, pts[1:])])
            g.add(*[Dot(q, radius=0.045, color=DATA_GAUGE) for q in pts])
            return g

        curve = always_redraw(steps)
        head = always_redraw(lambda: Dot(
            axes.c2p(max(1, int(m.get_value())),
                     averaging_floor(max(1, int(m.get_value())))),
            radius=0.075, color=ACCENT))
        read = always_redraw(lambda: panel_label(
            f"m = {max(1, int(m.get_value())):>2}   observed = "
            f"{averaging_floor(max(1, int(m.get_value()))):.3f} µm", 24, INK)
            .move_to(axes.c2p(15.0, 4.905)))
        self.add(curve, head, read)

        with self.say("Averaging divides the measurement variance by the number of "
                      "repeats. It does nothing at all to the variation between "
                      "the parts, so the curve falls towards the part spread and "
                      "stops."):
            self.play(m.animate.set_value(25.0), run_time=4.2,
                      rate_func=rf.ease_out_sine)

        # it took the title's slot: at DOWN * 3.35 it sat on the x-axis label,
        # and a conclusion arriving where the section heading was reads as the
        # heading being answered
        verdict = prose("the gauge is a process, and it has a size", 30, INK_BRIGHT)
        verdict.to_edge(UP, buff=0.38)
        with self.say(f"Five repeats gets you within one percent of the floor and "
                      f"twenty-five barely improves on that. So the honest question "
                      f"is never how good is my gauge. It is how big is it, "
                      f"compared to something. Level two asks whose spread we have "
                      f"actually been measuring."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(verdict, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
