"""LEVEL 5 act - 'Precision is not accuracy.'

Four levels of arithmetic, all of it built from variances, all of it with a mean
of zero. This act moves the mean and watches the arithmetic fail to notice.

- Part 1 slides a bias in with a tracker while the %GRR readout stays frozen.
  The number not moving is the whole point, and it is better watched than told.
- Part 2 shows the damage arriving on one side only, which is what distinguishes
  bias from noise on a shop floor.
- Part 3 measures a master until the interval stops containing zero, then prices
  the sample size for smaller biases.
- Part 4 sweeps a linearity slope and the %GRR readout gets *better*.
- Part 5 runs twelve monthly studies of a drifting gauge, each one internally
  fine.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level05_scene.py Level05
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level05_scene.py Level05
"""
from __future__ import annotations

import math

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, Group, Line, MathTex,
    Rectangle, VGroup, Write,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
    ValueTracker,
)

from msalab.act_style import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM,
    RULE, SIGNAL_ALARM, SIGNAL_OK, gauge, micro, panel_label, prose,
    within_frame,
)
from msalab.accuracy import (
    BIAS, BIASED_MISS, CLEAN_MISS, CLEAN_RATIOS, DRIFT, DRIFT_OVER_GAUGE,
    DRIFT_PER_MONTH, DRIFT_TOTAL, GAUGE_SIGMA, GRR_BY_MONTH, LINEARITY,
    MASTER_READS, MONTHS, READS_FOR_BIAS, READS_FOR_HALF, READS_FOR_TENTH,
    bias_interval, misclassification, ratios_with_linearity,
)
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA
from msalab.narration import NarratedCameraScene

TOTAL_SIGMA = math.hypot(PART_SIGMA, GAUGE_SIGMA)
HALF = TOLERANCE / 2


def _pdf(x, mu, sd):
    return np.exp(-((x - mu) ** 2) / (2 * sd ** 2)) / (sd * np.sqrt(2 * np.pi))


class Level05(NarratedCameraScene):
    def construct(self):
        self.part1_the_number_does_not_move()
        self.part2_one_sided()
        self.part3_it_takes_a_master()
        self.part4_linearity_flatters()
        self.part5_stability()

    # ------------------------------------------------------------- part 1
    def part1_the_number_does_not_move(self):
        title = prose("Level 5 · precision is not accuracy", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Four levels of arithmetic, and every number in it was built "
                      "out of variances. Watch what happens when the gauge stops "
                      "being centred."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[-24, 24, 10], y_range=[0, 0.115, 0.05],
                    x_length=9.6, y_length=3.7, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.85)
        xl = panel_label("reading, µm from nominal", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)

        band = Rectangle(width=(axes.c2p(HALF, 0) - axes.c2p(-HALF, 0))[0],
                         height=(axes.c2p(0, 0.115) - axes.c2p(0, 0))[1],
                         fill_color=INK_DIM, fill_opacity=0.10, stroke_width=0)
        band.move_to((axes.c2p(-HALF, 0) + axes.c2p(HALF, 0.115)) / 2)
        edges = VGroup(*[
            Line(axes.c2p(v, 0), axes.c2p(v, 0.104), stroke_color=DATA_TRUTH,
                 stroke_width=2) for v in (-HALF, HALF)])
        band_tag = within_frame(
            panel_label("the tolerance band", 19, DATA_TRUTH)
            .next_to(axes.c2p(0, 0.108), UP, buff=0.10), "part 1 band tag")

        b = ValueTracker(0.0)
        curve = always_redraw(lambda: axes.plot(
            lambda x: _pdf(x, b.get_value(), TOTAL_SIGMA),
            x_range=[-24, 24], color=SIGNAL_ALARM, stroke_width=4))
        ghost = axes.plot(lambda x: _pdf(x, 0.0, TOTAL_SIGMA),
                          x_range=[-24, 24], color=SIGNAL_OK, stroke_width=2.2)

        # the readout is computed from the standard deviations, exactly as the
        # library does it, so it CANNOT respond to the bias
        read = always_redraw(lambda: panel_label(
            f"bias {b.get_value():+5.2f} µm     %GRR study "
            f"{CLEAN_RATIOS['study']:.4f} %     tolerance "
            f"{CLEAN_RATIOS['tolerance']:.4f} %", 22, INK)
            .move_to(axes.c2p(0, 0.146)))

        with self.say("Here is the gauge, centred, inside the tolerance. And here "
                      "are the two percentages Level 4 produced."):
            self.play(Create(axes), FadeIn(xl), FadeIn(band), Create(edges),
                      FadeIn(band_tag), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)
            self.add(ghost, curve, read)

        with self.say("Now slide the whole thing three microns high. The parts have "
                      "not changed, the noise has not changed - only the level. "
                      "Watch the numbers."):
            self.play(b.animate.set_value(BIAS), run_time=4.0,
                      rate_func=rf.ease_in_out_sine)

        frozen = within_frame(
            prose("neither number moved. not to four decimals.", 28, INK_BRIGHT)
            .move_to(axes.c2p(0, -0.030)), "part 1 verdict")
        with self.say("They did not move. Not approximately - not to four decimal "
                      "places, because a standard deviation does not know where "
                      "the readings sit. There is nowhere in either formula for a "
                      "bias to enter."):
            self.play(FadeIn(frozen, shift=UP * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_one_sided(self):
        title = prose("and the damage arrives on one side", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 4.2, 1], y_range=[0, 105, 25],
                    x_length=9.0, y_length=3.9, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("bias, µm", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("share of the rejections, %", 19, INK_DIM)
        yl.next_to(axes.c2p(0, 105), RIGHT, buff=0.10).shift(UP * 0.08)

        with self.say("The percentages are blind, but a shop floor is not - because "
                      "bias does something noise never does."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.2, rate_func=rf.ease_in_out_sine)

        biases = np.linspace(0.0, 4.0, 17)
        pre = [misclassification(bias=float(x))
               for x in biases]
        k = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(k.get_value() * (len(biases) - 1)), 0,
                               len(biases) - 1))

        upper = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(biases[i], pre[i]["rejected_at_upper_pct"]),
                 axes.c2p(biases[i + 1], pre[i + 1]["rejected_at_upper_pct"]),
                 stroke_color=SIGNAL_ALARM, stroke_width=3.6)
            for i in range(idx())]))
        lower = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(biases[i], pre[i]["rejected_at_lower_pct"]),
                 axes.c2p(biases[i + 1], pre[i + 1]["rejected_at_lower_pct"]),
                 stroke_color=DATA_GAUGE, stroke_width=3.6)
            for i in range(idx())]))
        read = always_redraw(lambda: panel_label(
            f"bias {biases[idx()]:4.2f} µm    upper limit "
            f"{pre[idx()]['rejected_at_upper_pct']:5.1f} %    lower "
            f"{pre[idx()]['rejected_at_lower_pct']:5.1f} %", 22, INK)
            .move_to(axes.c2p(2.1, 52.0)))
        self.add(upper, lower, read)

        with self.say("With no bias, half the scrapped parts are too big and half "
                      "are too small. Add a bias and it all goes one way. By three "
                      "microns, ninety nine percent of the rejections are at the "
                      "upper limit - which is something an operator notices in a "
                      "morning, and no variance ratio ever will."):
            self.play(k.animate.set_value(1.0), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_it_takes_a_master(self):
        title = prose("you cannot find it by measuring again", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)
        with self.say("So how do you find it? Not by measuring the part again. "
                      "Repeat a reading a thousand times and you learn the spread "
                      "precisely and learn nothing at all about where it sits."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, MASTER_READS + 1, 2], y_range=[-2.5, 7.5, 2],
                    x_length=8.8, y_length=3.9, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55)
        xl = panel_label("readings of the master", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)
        zero = Line(axes.c2p(0, 0), axes.c2p(MASTER_READS + 1, 0),
                    stroke_color=DATA_TRUTH, stroke_width=2)
        zero_tag = within_frame(
            panel_label("zero error", 18, DATA_TRUTH)
            .next_to(axes.c2p(MASTER_READS + 1, 0), LEFT, buff=0.14)
            .shift(DOWN * 0.28), "part 3 zero tag")

        with self.say("It takes a reference - something whose size you already "
                      "know. Measure that, and the question becomes whether an "
                      "interval on the average error still contains zero."):
            self.play(Create(axes), FadeIn(xl), Create(zero), FadeIn(zero_tag),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        rng = np.random.default_rng(777)
        sample = BIAS + rng.normal(0.0, GAUGE_SIGMA, MASTER_READS)
        marks = VGroup()
        n = ValueTracker(0.0)

        def ci_bar():
            k = max(2, int(n.get_value()))
            ci = bias_interval(sample[:k])
            colour = SIGNAL_ALARM if ci["detected"] else INK_DIM
            x = MASTER_READS + 0.55
            return VGroup(
                Line(axes.c2p(x, ci["low"]), axes.c2p(x, ci["high"]),
                     stroke_color=colour, stroke_width=5),
                Dot(axes.c2p(x, ci["mean"]), radius=0.065, color=colour))

        bar = always_redraw(ci_bar)
        read = always_redraw(lambda: (lambda ci: panel_label(
            f"{max(2, int(n.get_value())):>2} readings   mean {ci['mean']:+5.2f}"
            f"   interval [{ci['low']:+5.2f}, {ci['high']:+5.2f}]   "
            f"{'BIAS FOUND' if ci['detected'] else 'contains zero'}",
            21, SIGNAL_ALARM if ci["detected"] else INK_DIM)
            .move_to(axes.c2p(5.5, 6.6)))(bias_interval(
                sample[:max(2, int(n.get_value()))])))

        with self.say("Take the readings one at a time. The interval starts wide "
                      "enough to swallow zero, and it narrows."):
            self.add(bar, read)
            for k in range(1, MASTER_READS + 1):
                marks.add(Dot(axes.c2p(k, sample[k - 1]), radius=0.06,
                              color=INK_BRIGHT))
                self.play(FadeIn(marks[-1], scale=1.5),
                          n.animate.set_value(k), run_time=0.34,
                          rate_func=rf.ease_out_back)

        panel = within_frame(
            VGroup(
                panel_label("readings needed, 95 % confidence, 90 % power", 19,
                            INK_DIM),
                panel_label(f"to catch {BIAS:.1f} µm      {READS_FOR_BIAS:>4}", 21,
                            SIGNAL_OK),
                panel_label(f"to catch {BIAS/2:.1f} µm      {READS_FOR_HALF:>4}", 21,
                            INK_BRIGHT),
                panel_label(f"to catch {BIAS/10:.1f} µm      {READS_FOR_TENTH:>4}",
                            21, SIGNAL_ALARM),
            ).arrange(DOWN, buff=0.26, aligned_edge=LEFT)
            .move_to(DOWN * 0.2), "part 3 sample size panel")

        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*[m for m in self.mobjects if m is not title])),
                  run_time=0.6, rate_func=rf.ease_in_sine)

        with self.say("Eight readings settle a three micron bias. Halving the bias "
                      "you want to catch does not double the work, it roughly "
                      "quadruples it - and chasing three tenths of a micron takes "
                      "nearly five hundred readings of a master. Accuracy is "
                      "expensive in a way precision is not."):
            self.play(FadeIn(panel, shift=UP * 0.10), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_linearity_flatters(self):
        title = prose("linearity does not hide — it flatters", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[-15, 15, 5], y_range=[-5.5, 5.5, 2],
                    x_length=8.4, y_length=3.7, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.6 + LEFT * 1.6)
        xl = panel_label("the part's true size, µm", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)
        yl = panel_label("the gauge's error", 19, INK_DIM)
        yl.next_to(axes.c2p(-15, 5.5), RIGHT, buff=0.10).shift(UP * 0.06)

        with self.say("The second way to be wrong is to be right in the middle and "
                      "wrong at the ends."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.2, rate_func=rf.ease_in_out_sine)

        s = ValueTracker(0.0)
        line = always_redraw(lambda: axes.plot(
            lambda x: s.get_value() * x, x_range=[-14.5, 14.5],
            color=SIGNAL_ALARM, stroke_width=4))
        flat = DashedLine(axes.c2p(-14.5, 0), axes.c2p(14.5, 0),
                         dash_length=0.13, stroke_color=DATA_TRUTH,
                         stroke_width=2)
        read = always_redraw(lambda: (lambda r: panel_label(
            f"slope {s.get_value():4.2f}\n"
            f"apparent parts {r['apparent_part']:5.2f} µm\n"
            f"true parts     {PART_SIGMA:5.2f} µm\n\n"
            f"%GRR {r['study']:5.1f} %",
            21, ACCENT if s.get_value() > 0.01 else INK_DIM)
            .move_to(RIGHT * 4.30 + UP * 1.35))(
                ratios_with_linearity(slope=max(1e-9, s.get_value()))))

        self.add(flat, line, read)
        with self.say("Turn the slope up. The gauge now reads high on the big parts "
                      "and low on the small ones, which is a real defect with a "
                      "real cause - a worn anvil, a fixture that does not locate "
                      "the same way across the range."):
            self.play(s.animate.set_value(LINEARITY), run_time=3.6,
                      rate_func=rf.ease_in_out_sine)

        verdict = within_frame(
            prose("the gauge's own defect is counted as process variation", 27,
                  INK_BRIGHT).to_edge(UP, buff=0.38), "part 4 verdict")
        with self.say("And look at what happened to the percentage. It got better. "
                      "The gauge's error grows with the size of the part, so it "
                      "widens the spread of the readings - which is the "
                      "denominator. The instrument's own defect is counted as "
                      "process variation and rewarded for it."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(verdict, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_stability(self):
        title = prose("and it was right in March", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[-0.5, MONTHS, 2], y_range=[-2.5, 8.5, 2],
                    x_length=9.2, y_length=3.8, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55)
        xl = panel_label("month", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("measured bias, µm", 19, INK_DIM)
        yl.next_to(axes.c2p(-0.5, 8.5), RIGHT, buff=0.10).shift(UP * 0.06)
        zero = Line(axes.c2p(-0.5, 0), axes.c2p(MONTHS, 0), stroke_color=RULE,
                    stroke_width=1.4)

        with self.say("The third way to be wrong is to have been right. Run the "
                      "same check on a master once a month for a year."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), Create(zero), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        rows = DRIFT["rows"]
        grr = within_frame(
            panel_label(f"%GRR every month: {GRR_BY_MONTH[0]:.4f} %", 22,
                        SIGNAL_OK).move_to(axes.c2p(7.6, -1.85)),
            "part 5 grr readout")
        self.add(grr)

        for r in rows:
            bar = VGroup(
                Line(axes.c2p(r["month"], r["mean"] - r["half_width"]),
                     axes.c2p(r["month"], r["mean"] + r["half_width"]),
                     stroke_color=SIGNAL_OK, stroke_width=3.2),
                Dot(axes.c2p(r["month"], r["mean"]), radius=0.055,
                    color=SIGNAL_OK))
            if r["month"] == 0:
                with self.say("Month one: the interval contains zero, the "
                              "repeatability is what it always was, and the R and "
                              "R number is exactly what it was last time."):
                    self.play(FadeIn(bar, scale=1.3), run_time=0.5,
                              rate_func=rf.ease_out_back)
            else:
                self.play(FadeIn(bar, scale=1.2), run_time=0.22,
                          rate_func=rf.ease_out_back)

        truth = axes.plot(lambda x: DRIFT_PER_MONTH * x, x_range=[0, MONTHS - 1],
                          color=DATA_TRUTH, stroke_width=3)
        truth_tag = within_frame(
            panel_label(f"the real bias: {DRIFT_TOTAL:.1f} µm by the end", 20,
                        DATA_TRUTH).move_to(axes.c2p(3.1, 7.4)),
            "part 5 truth tag")
        with self.say("And here is what the gauge was actually doing. Six microns "
                      "of drift - nearly three times the gauge's own sigma, and a "
                      "fifth of the whole tolerance. Every single study was "
                      "internally correct, because the bias is constant inside one "
                      "afternoon. The drift only exists between studies, and only "
                      "if somebody kept them."):
            self.play(Create(truth), FadeIn(truth_tag), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)

        closing = prose("R&R answers one question about a gauge", 29, INK_BRIGHT)
        closing.to_edge(UP, buff=0.38)
        with self.say("So five levels in, the honest summary is this. R and R "
                      "answers one question about a measurement system, and it is "
                      "not the question of whether the gauge is right. Which leaves "
                      "one more assumption standing: that a reading is a number at "
                      "all. Level six is about the gauge that says pass or fail."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(closing, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
