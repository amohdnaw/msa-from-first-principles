"""LEVEL 4 act - 'A percentage of what?'

Levels 1 to 3 produced variances. This act turns one into a verdict and shows
that the arithmetic is the easy half.

- Part 1 draws the numerator once and the two denominators beside it, to scale,
  so "against what" is a length rather than a phrase.
- Part 2 tightens the process with a tracker. One ratio gets worse and the other
  does not move, and the gauge never changed.
- Part 3 puts the same gauge in two factories and reads opposite verdicts off
  the same table.
- Part 4 draws ndc against the study ratio and lands both printed gates on it.
  They are different lines.
- Part 5 runs the decision the percentage was standing in for, and moves the
  process without touching the gauge.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level04_scene.py Level04
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level04_scene.py Level04
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
from msalab.against_what import (
    ACCEPT_PCT, A_PART, A_STUDY, A_TOL, A_TOLPCT, B_PART, B_STUDY, B_TOL,
    B_TOLPCT, CENTRED, GAUGE_SIGMA, NDC_MIN, REJECT_PCT, SHIFTED,
    STUDY_PCT_AT_NDC5, TOLERANCE, ndc_from_study_ratio, study_ratio,
    tolerance_ratio, verdict,
)
from msalab.measurement import PART_SIGMA
from msalab.narration import NarratedCameraScene

VERDICT_COLOUR = {"accept": SIGNAL_OK, "conditional": INK_BRIGHT,
                  "reject": SIGNAL_ALARM}


class Level04(NarratedCameraScene):
    def construct(self):
        self.part1_two_denominators()
        self.part2_one_moves_one_does_not()
        self.part3_opposite_verdicts()
        self.part4_ndc_adds_nothing()
        self.part5_what_it_costs()

    # ------------------------------------------------------------- part 1
    def part1_two_denominators(self):
        title = prose("Level 4 · a percentage of what?", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Three levels of arithmetic have produced variances. A "
                      "verdict is not a variance. To get one you divide - and the "
                      "question is what you divide by."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # 0.30 put the study bar's label 1.2 units past the right edge and the
        # frame guard stopped the render before a frame existed
        scale = 0.195
        g6 = 6 * GAUGE_SIGMA
        s6 = 6 * math.hypot(PART_SIGMA, GAUGE_SIGMA)
        rows = [(f"gauge 6σ  {g6:.1f} µm", g6, ACCENT, 1.35),
                (f"study spread  {s6:.1f} µm", s6, DATA_OBSERVED, 0.15),
                (f"tolerance  {TOLERANCE:.0f} µm", TOLERANCE, DATA_TRUTH, -1.05)]

        bars = VGroup()
        for label, width, colour, y in rows:
            bar = Rectangle(width=width * scale, height=0.52,
                            fill_color=colour, fill_opacity=0.62,
                            stroke_color=colour, stroke_width=1.4)
            bar.move_to([-5.4 + width * scale / 2, y, 0])
            tag = within_frame(
                panel_label(label, 20, colour).next_to(bar, RIGHT, buff=0.24),
                f"part 1 bar {label[:12]}")
            bars.add(VGroup(bar, tag))

        with self.say("Here is the gauge, drawn to scale. And here are the two "
                      "things you might compare it to: the spread of the parts you "
                      "measured, and the tolerance on the drawing."):
            for b in bars:
                self.play(FadeIn(b, shift=RIGHT * 0.10), run_time=0.75,
                          rate_func=rf.ease_out_sine)

        read = within_frame(
            panel_label(f"against the study   {study_ratio():5.1f} %\n"
                        f"against the tolerance {tolerance_ratio():5.1f} %",
                        24, INK).move_to(DOWN * 2.75), "part 1 readout")
        with self.say("Same numerator. Two denominators. Two questions - can this "
                      "gauge tell these parts apart, and can it decide whether a "
                      "part conforms. Neither is wrong, and the standard prints "
                      "both without saying which one you are asking."):
            self.play(FadeIn(read, shift=UP * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_one_moves_one_does_not(self):
        title = prose("one of them can see the parts", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0.8, 9.2, 2], y_range=[0, 100, 25],
                    x_length=9.2, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("part-to-part spread, µm", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)
        yl = panel_label("%GRR", 19, INK_DIM)
        yl.next_to(axes.c2p(0.8, 100), RIGHT, buff=0.10).shift(UP * 0.08)

        gates = VGroup()
        for pct, colour, name in [(ACCEPT_PCT, SIGNAL_OK, "accept below 10 %"),
                                  (REJECT_PCT, SIGNAL_ALARM, "reject above 30 %")]:
            ln = DashedLine(axes.c2p(0.8, pct), axes.c2p(9.2, pct),
                            dash_length=0.13, stroke_color=colour, stroke_width=2)
            tg = panel_label(name, 18, colour).next_to(
                axes.c2p(1.4, pct), RIGHT, buff=0.14).shift(UP * 0.24)
            gates.add(ln, tg)

        with self.say("Watch what happens to each of them when the process gets "
                      "better and the gauge does not change at all."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.1, rate_func=rf.ease_in_out_sine)
            self.play(*[Create(g) if isinstance(g, DashedLine) else FadeIn(g)
                        for g in gates], run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # the sweep runs from a sloppy process to a tight one, i.e. right to left
        p = ValueTracker(9.0)
        study_c = always_redraw(lambda: axes.plot(
            lambda x: study_ratio(GAUGE_SIGMA, x),
            x_range=[max(0.85, p.get_value()), 9.0],
            color=DATA_OBSERVED, stroke_width=4))
        tol_c = axes.plot(lambda x: tolerance_ratio(), x_range=[0.85, 9.0],
                          color=DATA_TRUTH, stroke_width=4)
        head = always_redraw(lambda: Dot(
            axes.c2p(p.get_value(), study_ratio(GAUGE_SIGMA, p.get_value())),
            radius=0.075, color=ACCENT))
        read = always_redraw(lambda: panel_label(
            f"parts {p.get_value():4.1f} µm    study "
            f"{study_ratio(GAUGE_SIGMA, p.get_value()):5.1f} %    tolerance "
            f"{tolerance_ratio():5.1f} %", 22, INK)
            .move_to(axes.c2p(6.6, 88.0)))
        self.add(study_c, tol_c, head, read)

        with self.say("The tolerance ratio is a flat line. It does not know the "
                      "parts exist."):
            self.beat(1.2)

        with self.say("The study ratio climbs, and it climbs steeply. Make the "
                      "parts nearly identical and it approaches a hundred percent, "
                      "because a gauge measuring parts that do not differ cannot "
                      "tell them apart. Nothing about the instrument got worse. The "
                      "question got harder."):
            self.play(p.animate.set_value(0.9), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.0)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_opposite_verdicts(self):
        title = prose("the same gauge, two factories", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)
        with self.say("So put one gauge - this gauge, two point zero six microns - "
                      "into two different factories."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        cases = [("A  tight process, generous drawing",
                  f"parts {A_PART:.0f} µm · tolerance {A_TOL:.0f} µm",
                  A_STUDY, A_TOLPCT, 1.25),
                 ("B  sloppy process, tight drawing",
                  f"parts {B_PART:.0f} µm · tolerance {B_TOL:.0f} µm",
                  B_STUDY, B_TOLPCT, -1.55)]

        for head, sub, sp, tp, y in cases:
            block = VGroup(
                panel_label(head, 24, INK_BRIGHT),
                panel_label(sub, 19, INK_DIM),
            ).arrange(DOWN, buff=0.16, aligned_edge=LEFT)
            block.move_to([-5.6 + block.width / 2, y + 0.62, 0])

            sv, tv = verdict(sp), verdict(tp)
            verd = VGroup(
                panel_label(f"against study      {sp:5.1f} %   {sv}", 22,
                            VERDICT_COLOUR[sv]),
                panel_label(f"against tolerance  {tp:5.1f} %   {tv}", 22,
                            VERDICT_COLOUR[tv]),
            ).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            verd.move_to([-5.6 + verd.width / 2, y - 0.52, 0])
            within_frame(verd, f"part 3 verdicts {head[0]}")

            line = ("In the first, the parts barely vary and the drawing is "
                    "generous. The gauge cannot tell the parts apart at all - "
                    "fifty seven percent, reject - and it decides conformance "
                    "comfortably, eight percent, accept."
                    if head.startswith("A") else
                    "In the second, exactly the reverse. It sorts the parts easily "
                    "and it cannot be trusted with the conformance call.")
            with self.say(line):
                self.play(FadeIn(block, shift=RIGHT * 0.10), run_time=0.8,
                          rate_func=rf.ease_out_sine)
                self.play(FadeIn(verd, shift=UP * 0.10), run_time=0.9,
                          rate_func=rf.ease_out_sine)

        with self.say("One gauge. Two rows. Opposite verdicts off the same printed "
                      "table, and neither row is a mistake."):
            self.beat(1.5)

        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_ndc_adds_nothing(self):
        title = prose("and the third number is the first one again", 29, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[4, 70, 10], y_range=[0, 22, 5],
                    x_length=9.0, y_length=4.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.5)
        xl = panel_label("%GRR against study variation", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)
        yl = panel_label("ndc", 19, INK_DIM)
        yl.next_to(axes.c2p(4, 22), RIGHT, buff=0.10).shift(UP * 0.08)

        with self.say("The standard prints a third number beside those two: the "
                      "number of distinct categories. It is supposed to say how "
                      "many groups the gauge can tell apart."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.1, rate_func=rf.ease_in_out_sine)

        curve = axes.plot(lambda x: ndc_from_study_ratio(x), x_range=[4.2, 70],
                          color=DATA_OBSERVED, stroke_width=4)
        with self.say("Plot it against the study ratio and it is a curve. Not a "
                      "cloud - a curve. Given the study ratio, ndc is determined, "
                      "because it is that same ratio with the algebra rearranged. "
                      "It cannot carry information the first number did not "
                      "already have."):
            self.play(Create(curve), run_time=2.4, rate_func=rf.ease_in_out_sine)

        g_ndc = DashedLine(axes.c2p(4, NDC_MIN), axes.c2p(70, NDC_MIN),
                           dash_length=0.13, stroke_color=ACCENT, stroke_width=2)
        v_ndc = Line(axes.c2p(STUDY_PCT_AT_NDC5, 0),
                     axes.c2p(STUDY_PCT_AT_NDC5, 22), stroke_color=ACCENT,
                     stroke_width=2.4)
        v_rej = Line(axes.c2p(REJECT_PCT, 0), axes.c2p(REJECT_PCT, 22),
                     stroke_color=SIGNAL_ALARM, stroke_width=2.4)
        t_ndc = within_frame(
            panel_label(f"ndc reaches {NDC_MIN}\nat {STUDY_PCT_AT_NDC5:.1f} %",
                        19, ACCENT).next_to(axes.c2p(STUDY_PCT_AT_NDC5, 19.5),
                                            LEFT, buff=0.16),
            "part 4 ndc gate")
        t_rej = within_frame(
            panel_label(f"reject above\n{REJECT_PCT:.0f} %", 19, SIGNAL_ALARM)
            .next_to(axes.c2p(REJECT_PCT, 19.5), RIGHT, buff=0.16),
            "part 4 reject gate")

        with self.say("Now put both of the standard's own gates on it. The rule "
                      "says reject above thirty percent. The rule also says ndc "
                      "must reach five."):
            self.play(Create(g_ndc), Create(v_rej), FadeIn(t_rej), run_time=1.2,
                      rate_func=rf.ease_out_sine)
            self.play(Create(v_ndc), FadeIn(t_ndc), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        gap = within_frame(
            panel_label(f"{REJECT_PCT - STUDY_PCT_AT_NDC5:.1f} points apart, "
                        f"printed in the same table", 22, INK_BRIGHT)
            .move_to(axes.c2p(46, 12.0)), "part 4 gap")
        with self.say("Those are not the same line. Ndc reaching five happens at "
                      "twenty seven point one percent, nearly three points tighter "
                      "than the thirty printed beside it. A gauge can satisfy one "
                      "rule and fail the other, in the same table, on the same "
                      "study."):
            self.play(FadeIn(gap, shift=UP * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.1)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_what_it_costs(self):
        title = prose("what the percentage was standing in for", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        half = TOLERANCE / 2
        axes = Axes(x_range=[-26, 26, 10], y_range=[-26, 26, 10],
                    x_length=6.4, y_length=4.4, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55 + LEFT * 2.9)
        xl = panel_label("the part's true size, µm", 18, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.22)
        yl = panel_label("what the gauge read", 18, INK_DIM)
        yl.next_to(axes.c2p(-26, 26), RIGHT, buff=0.10).shift(UP * 0.06)

        with self.say("None of those three numbers is the thing you actually care "
                      "about. A conformance decision compares a reading to a "
                      "limit, so a good part can be rejected and a bad part can be "
                      "shipped."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.2, rate_func=rf.ease_in_out_sine)

        limits = VGroup(
            DashedLine(axes.c2p(-half, -26), axes.c2p(-half, 26),
                       dash_length=0.11, stroke_color=DATA_TRUTH, stroke_width=1.8),
            DashedLine(axes.c2p(half, -26), axes.c2p(half, 26),
                       dash_length=0.11, stroke_color=DATA_TRUTH, stroke_width=1.8),
            Line(axes.c2p(-26, -half), axes.c2p(26, -half),
                 stroke_color=DATA_TRUTH, stroke_width=1.8),
            Line(axes.c2p(-26, half), axes.c2p(26, half),
                 stroke_color=DATA_TRUTH, stroke_width=1.8))
        with self.say("The dashed lines are the truth's limits. The solid lines are "
                      "where the gauge's reading crosses them."):
            self.play(Create(limits), run_time=1.1, rate_func=rf.ease_in_out_sine)

        rng = np.random.default_rng(915)
        n = 520
        truth = rng.normal(0.0, PART_SIGMA, n)
        read = truth + rng.normal(0.0, GAUGE_SIGMA, n)
        good, passed = np.abs(truth) <= half, np.abs(read) <= half
        ok = VGroup(*[Dot(axes.c2p(a, b), radius=0.030, color=INK_DIM,
                          fill_opacity=0.55)
                      for a, b in zip(truth[good == passed], read[good == passed])])
        fa = VGroup(*[Dot(axes.c2p(a, b), radius=0.055, color=SIGNAL_ALARM)
                      for a, b in zip(truth[~good & passed], read[~good & passed])])
        fr = VGroup(*[Dot(axes.c2p(a, b), radius=0.055, color=ACCENT)
                      for a, b in zip(truth[good & ~passed], read[good & ~passed])])

        with self.say("Five hundred parts, measured once each."):
            self.play(FadeIn(ok), run_time=1.2, rate_func=rf.ease_out_sine)

        panel = within_frame(
            VGroup(
                panel_label("centred", 20, INK_DIM),
                panel_label(f"bad parts accepted  "
                            f"{CENTRED['bad_parts_accepted_pct']:5.1f} %", 20,
                            SIGNAL_ALARM),
                panel_label(f"good parts rejected {CENTRED['good_parts_rejected_pct']:5.2f} %",
                            20, ACCENT),
                panel_label(f"scrap               {CENTRED['scrap_rate_pct']:5.2f} %",
                            20, INK),
            ).arrange(DOWN, buff=0.20, aligned_edge=LEFT)
            .move_to(RIGHT * 4.0 + UP * 0.9), "part 5 centred panel")

        with self.say("The salmon points are out of tolerance and were accepted. "
                      "The amber ones were inside and got scrapped. Twenty eight "
                      "percent of the genuinely bad parts pass, on a centred "
                      "process, with this gauge."):
            self.play(FadeIn(fa, scale=1.4), FadeIn(fr, scale=1.4), run_time=1.0,
                      rate_func=rf.ease_out_back)
            self.play(FadeIn(panel, shift=LEFT * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        shifted = within_frame(
            VGroup(
                panel_label("shifted a quarter of tolerance", 20, INK_DIM),
                panel_label(f"bad parts accepted  "
                            f"{SHIFTED['bad_parts_accepted_pct']:5.1f} %", 20,
                            SIGNAL_ALARM),
                panel_label(f"good parts rejected {SHIFTED['good_parts_rejected_pct']:5.2f} %",
                            20, ACCENT),
                panel_label(f"scrap               {SHIFTED['scrap_rate_pct']:5.2f} %",
                            20, INK),
            ).arrange(DOWN, buff=0.20, aligned_edge=LEFT)
            .move_to(RIGHT * 4.0 + DOWN * 1.7), "part 5 shifted panel")

        with self.say("Now move the process off centre without touching the gauge. "
                      "Scrap goes from a tenth of a percent to five and a half. The "
                      "gauge is identical, so every percentage from the first three "
                      "levels is identical, and the risk has moved by a factor of "
                      "forty."):
            self.play(FadeIn(shifted, shift=LEFT * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        closing = prose("a percentage is a proxy. it does not know where you are",
                        29, INK_BRIGHT)
        closing.to_edge(UP, buff=0.38)
        with self.say("So a percentage is a proxy for a risk, and it does not know "
                      "where your process is sitting. Which is the last thing we "
                      "have been assuming without checking: that the gauge is "
                      "merely noisy, and not wrong. Level five asks what happens "
                      "when it reads high."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(closing, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
