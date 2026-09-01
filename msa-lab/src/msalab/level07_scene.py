"""LEVEL 7 act - 'The handshake back.'

The last act. Six levels built a measurement system; this one hands it to the
person it was built for, and finds that the handover is an identity.

- Part 1 draws the limits a chart earns and the limits it actually gets, with a
  tracker on the gauge pushing them apart.
- Part 2 prices that in detection: the wait to catch a real shift.
- Part 3 is the centrepiece. The definition of %GRR against tolerance is
  rearranged on screen into a ceiling on capability, and the camera goes to the
  point where our own gauge sits on it.
- Part 4 freezes the chart's number and slides the gauge's share of it from
  nothing to most of it - five factories the chart reads as one.
- Part 5 names the seven levels and hands over.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level07_scene.py Level07
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level07_scene.py Level07
"""
from __future__ import annotations

import math

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, Group, Line, MathTex,
    Rectangle, Transform, TransformMatchingTex, VGroup,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
    ValueTracker,
)

from msalab.act_style import (
    ACCENT, DATA_GAUGE, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM, RULE,
    SIGNAL_ALARM, SIGNAL_OK, gauge, micro, panel_label, prose, within_frame,
)
from msalab.handshake import (
    AIAG_GATES, CAP, SAME_CHART, SUBGROUP, arl, capability, chart_limits,
    indistinguishable_pairs, inflation,
)
from msalab.accuracy import GAUGE_SIGMA
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA
from msalab.opening import (
    closed_jaws, gauge_jaws, hand_off, part_block, plain, record_strip,
    thing_caption, tick, two_panel, value_label, span_bar, bar_caption,
)
from msalab.narration import NarratedCameraScene

HALF = TOLERANCE / 2.0


class Level07(NarratedCameraScene):
    def construct(self):
        self.part0_opening()
        self.part1_the_limits_contain_it()
        self.part2_the_detection_bill()
        self.part3_the_identity()
        self.part4_what_the_chart_cannot_see()
        self.part5_the_arc_closes()

    # ------------------------------------------------------------- part 0
    def part0_opening(self):
        """Plain-language opening. specs/act-opening-contract.md, mode B.

        The last opening. Two widths go in and one comes out, because that sum
        is the only thing the person watching the process ever receives.
        """
        panels = two_panel("the two things", "what gets handed over")
        b1 = part_block(centre=LEFT * 4.4 + UP * 0.9, w=1.7, h=0.6)
        b2 = part_block(centre=LEFT * 4.4 + DOWN * 0.6, w=1.7, h=0.6)
        c1 = thing_caption("the parts, really differing", b1)
        c2 = thing_caption("the gauge, wobbling", b2)

        with self.say("Two separate things have been going on for six levels. "
                      "The parts really do differ from each other. And the gauge "
                      "wobbles on top of that."):
            self.play(FadeIn(panels["all"]), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(b1), FadeIn(c1), run_time=0.6,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(b2), FadeIn(c2), run_time=0.6,
                      rate_func=rf.ease_out_sine)

        pb = span_bar(2.9, 1.45, DATA_TRUTH)
        pl = bar_caption("the parts", pb)
        gb = span_bar(1.4, 0.35, ACCENT)
        gl = bar_caption("the gauge", gb)
        with self.say("Here they are as two widths, and this whole course has "
                      "been about telling them apart."):
            self.play(FadeIn(pb), FadeIn(pl), run_time=0.7,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(gb), FadeIn(gl), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        sb = span_bar(3.22, -1.0, SIGNAL_ALARM)
        sl = bar_caption("what the person watching gets", sb)
        with self.say("But nobody on the floor receives two widths. They receive "
                      "readings, and a reading has both in it. One width, with "
                      "no seam in it anywhere."):
            self.play(FadeIn(sb, shift=RIGHT * 0.14), FadeIn(sl), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        verdict = within_frame(
            plain("they only ever get the sum.", 30, INK_BRIGHT)
            .move_to([2.9, -2.15, 0]), "opening verdict")
        with self.say("They only ever get the sum. This level is about what that "
                      "costs them, and about the one number that turns out to "
                      "join the two halves of this subject exactly."):
            self.play(FadeIn(verdict, shift=DOWN * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        hand_off(self, VGroup(b1, b2, c1, c2), panels)
        self.play(FadeOut(Group(pb, pl, gb, gl, sb, sl, verdict)),
                  run_time=0.6, rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 1
    def part1_the_limits_contain_it(self):
        title = prose("Level 7 · the handshake back", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Six levels have described a measurement system. Not one of "
                      "them said what it is for. A gauge exists because somebody "
                      "is watching a process."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        axes = Axes(x_range=[0, 26, 5], y_range=[-15, 11, 5],
                    x_length=9.4, y_length=4.2, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.6)
        xl = panel_label("subgroup", 19, INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("subgroup mean, µm from nominal", 19, INK_DIM)
        yl.next_to(axes.c2p(0, 11), RIGHT, buff=0.10).shift(UP * 0.06)
        centre = Line(axes.c2p(0, 0), axes.c2p(26, 0), stroke_color=RULE,
                      stroke_width=1.4)

        with self.say("So start with what they are drawing. Subgroup means, and a "
                      "pair of limits at three standard errors."):
            self.play(Create(axes), FadeIn(xl), FadeIn(yl), Create(centre),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        g = ValueTracker(0.0)

        def half_width(gv):
            return 3.0 * math.hypot(PART_SIGMA, gv) / math.sqrt(SUBGROUP)

        true_lines = VGroup(*[
            DashedLine(axes.c2p(0, s * half_width(0.0)),
                       axes.c2p(26, s * half_width(0.0)),
                       dash_length=0.14, stroke_color=DATA_TRUTH,
                       stroke_width=2.0) for s in (1, -1)])
        obs_lines = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(0, s * half_width(g.get_value())),
                 axes.c2p(26, s * half_width(g.get_value())),
                 stroke_color=SIGNAL_ALARM, stroke_width=3.0)
            for s in (1, -1)]))
        read = always_redraw(lambda: within_frame(panel_label(
            f"gauge σ {g.get_value():4.2f} µm     "
            f"limits ±{half_width(g.get_value()):5.3f} µm\n"
            f"{(half_width(g.get_value()) / half_width(0.0) - 1) * 100:5.2f} % "
            f"wider than the process", 21, SIGNAL_ALARM)
            .move_to(axes.c2p(13, -12.2)), "part 1 readout"))

        with self.say("These are the limits the process itself has earned - "
                      "computed from the parts, if you could see the parts."):
            self.play(Create(true_lines), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)
        self.add(obs_lines, read)

        with self.say("But nobody sees parts. They see readings. And Level one "
                      "settled what a reading is: the part plus the gauge, with "
                      "the variances adding. So bring the gauge in."):
            self.play(g.animate.set_value(GAUGE_SIGMA), run_time=3.4,
                      rate_func=rf.ease_in_out_sine)

        gap_tag = within_frame(
            panel_label(f"{half_width(0.0):.3f}  →  "
                        f"{half_width(GAUGE_SIGMA):.3f} µm", 20, INK_BRIGHT)
            .move_to(axes.c2p(20.5, 8.2)), "part 1 gap tag")
        home_w = self.camera.frame.width
        home_c = self.camera.frame.get_center()
        with self.say("Nine percent is half a micron on this chart, which is why "
                      "nobody has ever noticed it. Look closely at one limit."):
            self.play(FadeIn(gap_tag), run_time=0.6,
                      rate_func=rf.ease_out_sine)
            self.play(self.camera.frame.animate.set(width=home_w * 0.30)
                      .move_to(axes.c2p(20.5, half_width(GAUGE_SIGMA) - 0.28)),
                      run_time=2.4, rate_func=rf.ease_in_out_sine)
        self.play(self.camera.frame.animate.set(width=home_w).move_to(home_c),
                  run_time=1.5, rate_func=rf.ease_in_out_sine)

        # the gap tag has done its work in the zoom; at the wide frame it sits
        # where the verdict has to go, and beside the y-axis label
        self.play(FadeOut(gap_tag), run_time=0.4, rate_func=rf.ease_in_sine)
        verdict = within_frame(
            prose("the chart is wider than the process, and was never told", 28,
                  INK_BRIGHT).move_to(axes.c2p(13, 3.4)),
            "part 1 verdict")
        with self.say("Every chart in every plant is drawn around a spread that "
                      "includes its own instrument, and nothing on the chart says "
                      "so."):
            self.play(FadeIn(verdict, shift=DOWN * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_the_detection_bill(self):
        title = prose("and it is paid for in waiting", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0.3, 2.1, 0.3], y_range=[0, 62, 20],
                    x_length=8.6, y_length=3.8, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.55 + LEFT * 0.9)
        xl = panel_label("size of a real process shift, part sigmas", 19,
                         INK_DIM).next_to(axes, DOWN, buff=0.24)
        yl = panel_label("subgroups until it is caught", 19, INK_DIM)
        yl.next_to(axes.c2p(0.3, 62), RIGHT, buff=0.10).shift(UP * 0.06)

        with self.say("A wider limit is a later signal. Here is how long a chart "
                      "waits before it notices that something real has moved."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      FadeIn(yl), run_time=1.3, rate_func=rf.ease_in_out_sine)

        xs = np.linspace(0.30, 2.10, 90)
        pre = [arl(float(s)) for s in xs]
        k = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(k.get_value() * (len(xs) - 1)), 0,
                               len(xs) - 1))

        def track(key, colour, width):
            return always_redraw(lambda: VGroup(*[
                Line(axes.c2p(xs[i], pre[i][key]),
                     axes.c2p(xs[i + 1], pre[i + 1][key]),
                     stroke_color=colour, stroke_width=width)
                for i in range(idx())]))

        perfect = track("arl_if_gauge_were_perfect", DATA_TRUTH, 2.6)
        charted = track("arl_as_charted", SIGNAL_ALARM, 3.6)
        read = always_redraw(lambda: panel_label(
            f"shift {xs[idx()]:4.2f} σ\n"
            f"if perfect  {pre[idx()]['arl_if_gauge_were_perfect']:6.1f}\n"
            f"as charted  {pre[idx()]['arl_as_charted']:6.1f}\n"
            f"longer by   {(pre[idx()]['penalty_ratio'] - 1) * 100:5.1f} %",
            21, INK).move_to(RIGHT * 4.55 + UP * 0.9))
        self.add(perfect, charted, read)

        with self.say("A three sigma shift is caught immediately whatever the "
                      "gauge does, and a very small one is missed either way. The "
                      "bill lands in between - which is exactly the range a chart "
                      "is run to cover. Around one sigma the wait is thirty "
                      "percent longer than it needed to be."):
            self.play(k.animate.set_value(1.0), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_the_identity(self):
        title = prose("and then the two curricula turn out to be one", 29,
                      INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        with self.say("Which brings the last thing, and it is the reason this "
                      "level exists. Level four defined a percentage: the gauge's "
                      "spread against the tolerance."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        defn = MathTex(r"\%GRR_{tol}", "=", r"\frac{6\sigma_{gauge}}{T}",
                       font_size=54, color=INK)
        defn.move_to(UP * 0.55)
        with self.say("There it is, unchanged."):
            self.play(FadeIn(defn, shift=UP * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        step = MathTex(r"\frac{T}{6\sigma_{gauge}}", "=",
                       r"\frac{100}{\%GRR_{tol}}",
                       font_size=54, color=INK_BRIGHT)
        step.move_to(UP * 0.55)
        with self.say("Turn it upside down. Nothing has been assumed and nothing "
                      "estimated - this is the same statement written the other "
                      "way round."):
            self.play(TransformMatchingTex(defn, step), run_time=1.8,
                      rate_func=rf.ease_in_out_sine)

        with self.say("And the left hand side is a capability index. Half a "
                      "tolerance over three standard deviations, with the gauge's "
                      "standard deviation in place of the process's - which is "
                      "what you get when the process is perfect and only the "
                      "instrument is left."):
            self.beat(0.4)

        final = MathTex(r"Cpk_{max}", "=", r"\frac{T}{6\sigma_{gauge}}", "=",
                        r"\frac{100}{\%GRR_{tol}}",
                        font_size=54, color=ACCENT)
        final.move_to(UP * 0.55)
        self.play(TransformMatchingTex(step, final), run_time=1.6,
                  rate_func=rf.ease_in_out_sine)

        gates = VGroup(*[
            panel_label(f"%GRR_tol {g:4.0f} %   ->   Cpk can never exceed "
                        f"{100.0/g:6.3f}", 24,
                        SIGNAL_OK if g <= 10 else INK if g <= 20
                        else SIGNAL_ALARM)
            for g in AIAG_GATES]).arrange(DOWN, buff=0.24,
                                          aligned_edge=LEFT).move_to(DOWN * 1.55)
        with self.say("Which means every published gauge gate is a capability "
                      "ceiling that nobody prints beside it. Ten percent allows a "
                      "Cpk of ten. Twenty allows five. Thirty - the line above "
                      "which a gauge is rejected - allows three point three."):
            for row in gates:
                self.play(FadeIn(row, shift=RIGHT * 0.14), run_time=0.6,
                          rate_func=rf.ease_out_sine)

        self.beat(0.8)
        self.play(FadeOut(gates), run_time=0.6, rate_func=rf.ease_in_sine)

        # the hyperbola, and our own gauge on it
        axes = Axes(x_range=[0, 120, 20], y_range=[0, 11.5, 2],
                    x_length=8.8, y_length=3.5, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 1.45)
        xl = panel_label("%GRR against tolerance", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.22)
        curve = axes.plot(lambda x: 100.0 / x, x_range=[9.0, 120.0],
                          color=SIGNAL_ALARM, stroke_width=4)

        with self.say("One curve, and it joins the two subjects at every point "
                      "along it."):
            self.play(final.animate.scale(0.62).to_edge(UP, buff=1.05),
                      FadeOut(title), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)
            self.play(Create(axes), FadeIn(xl), Create(curve), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)

        here = CAP["grr_tolerance_pct"]
        dot = Dot(axes.c2p(here, CAP["ceiling"]), radius=0.075, color=ACCENT)
        tag = within_frame(
            panel_label(f"our gauge  {here:.1f} %\nCpk ≤ {CAP['ceiling']:.2f}",
                        22, ACCENT).move_to(axes.c2p(here + 34, 4.6)),
            "part 3 our gauge tag")

        with self.say("And here is where the gauge these six levels built comes "
                      "out. Forty one percent of tolerance, so this plant cannot "
                      "report a Cpk above two point four three - not with a better "
                      "process, not with more parts, not ever, until the "
                      "instrument changes."):
            self.play(FadeIn(dot, scale=1.8), FadeIn(tag), run_time=1.2,
                      rate_func=rf.ease_out_back)

        home_w = self.camera.frame.width
        home_c = self.camera.frame.get_center()
        with self.say("An M S A verdict was a capability verdict the whole time."):
            self.play(self.camera.frame.animate.set(width=home_w * 0.45)
                      .move_to(axes.c2p(here + 10, CAP["ceiling"])),
                      run_time=2.2, rate_func=rf.ease_in_out_sine)
        self.play(self.camera.frame.animate.set(width=home_w).move_to(home_c),
                  run_time=1.4, rate_func=rf.ease_in_out_sine)

        self.beat(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_what_the_chart_cannot_see(self):
        title = prose("what the chart cannot take back out", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[0, 26, 5], y_range=[0, 1.35, 1],
                    x_length=9.2, y_length=2.0, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 2.05)
        xl = panel_label("within-subgroup variance, µm²", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)

        with self.say("One last thing the chart is not able to do. The spread it "
                      "estimates inside a subgroup is made of two things: the "
                      "parts differing from each other, and the gauge failing to "
                      "repeat."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        total = SAME_CHART[0]["within_estimate"] ** 2
        f = ValueTracker(0.0)

        def split(frac):
            rep2 = frac * total
            part2 = total - rep2
            return part2, rep2

        def bar_for(x0, x1, colour):
            lo, hi = axes.c2p(x0, 0.30), axes.c2p(x1, 0.95)
            w = max(0.001, hi[0] - lo[0])
            r = Rectangle(width=w, height=hi[1] - lo[1], fill_color=colour,
                          fill_opacity=0.85, stroke_width=0)
            r.move_to((lo + hi) / 2)
            return r

        bars = always_redraw(lambda: (lambda ps: VGroup(
            bar_for(0.0, ps[0], INK_DIM),
            bar_for(ps[0], total, SIGNAL_ALARM),
        ))(split(f.get_value())))
        edge = Line(axes.c2p(total, 0.18), axes.c2p(total, 1.10),
                    stroke_color=DATA_TRUTH, stroke_width=3)
        edge_tag = within_frame(
            panel_label("what the chart estimates", 20, DATA_TRUTH)
            .next_to(axes.c2p(total, 1.10), UP, buff=0.10),
            "part 4 edge tag")
        read = always_redraw(lambda: (lambda ps: within_frame(panel_label(
            f"the gauge is {f.get_value()*100:3.0f} % of this variance\n"
            f"what the chart sees  {math.sqrt(total):6.4f} µm\n"
            f"true Cpk underneath  "
            f"{(TOLERANCE/2)/(3*math.sqrt(max(1e-9, ps[0]))):5.3f}",
            21, INK).move_to(axes.c2p(13, 2.45)),
            "part 4 readout"))(split(f.get_value())))

        self.add(bars, edge, read)
        with self.say("Here is that spread, all of it parts."):
            self.play(FadeIn(edge_tag), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        with self.say("Now hand some of it to the gauge. Watch the number the "
                      "chart reports. It does not move - it cannot, because the "
                      "chart only ever saw the total. And underneath, the true "
                      "capability of the process runs from one point oh four to "
                      "two point three three."):
            self.play(f.animate.set_value(0.80), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        verdict = within_frame(
            prose("five factories, one chart, and no arithmetic that separates "
                  "them", 27, INK_BRIGHT).to_edge(UP, buff=0.38),
            "part 4 verdict")
        with self.say("A capable process with a poor gauge and a poor process with "
                      "a perfect one look identical from here. No amount of "
                      "charting separates them, which is why a gauge study is a "
                      "separate study - and why this site exists beside the other "
                      "one."):
            self.play(FadeOut(title, shift=UP * 0.12),
                      FadeIn(verdict, shift=DOWN * 0.12), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_the_arc_closes(self):
        rows = [
            ("01", "a gauge is a process, and it has variation"),
            ("02", "two questions, one word"),
            ("03", "the term the older arithmetic has no room for"),
            ("04", "a percentage of what?"),
            ("05", "precision is not accuracy"),
            ("06", "the gauge that says pass"),
            ("07", "the handshake back"),
        ]
        items = VGroup(*[
            VGroup(panel_label(n, 24, ACCENT),
                   prose(text, 26, INK)).arrange(RIGHT, buff=0.42)
            for n, text in rows
        ]).arrange(DOWN, buff=0.28, aligned_edge=LEFT).move_to(UP * 0.15)

        with self.say("Seven levels. A gauge is a process and it has variation. "
                      "Two questions hiding in one word. The term average and "
                      "range cannot see. A percentage, and what it is a percentage "
                      "of. Precision is not accuracy. The gauge that says pass. "
                      "And the handshake back."):
            for row in items:
                self.play(FadeIn(row, shift=RIGHT * 0.16), run_time=0.55,
                          rate_func=rf.ease_out_sine)

        self.beat(0.9)
        self.play(FadeOut(items), run_time=0.6, rate_func=rf.ease_in_sine)

        closing = VGroup(
            prose("every number here was computed at render time", 29, INK_DIM),
            prose("and the chart is on the other site", 32, INK_BRIGHT),
        ).arrange(DOWN, buff=0.44)
        with self.say("Every number in these seven levels was computed when the "
                      "page was built, by the same library the tests read. None of "
                      "it is asserted. And the chart that consumes all of it is on "
                      "the other site, where it belongs."):
            self.play(FadeIn(closing, shift=DOWN * 0.10), run_time=1.3,
                      rate_func=rf.ease_out_sine)

        self.beat(1.4)
