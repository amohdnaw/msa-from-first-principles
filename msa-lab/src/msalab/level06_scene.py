"""LEVEL 6 act - 'The gauge that says pass.'

Five levels divided one spread by another. This act takes the number away and
asks whether anything survives.

- Part 1 hires an appraiser who passes every part without looking, and watches
  his percent agreement climb to the base rate while a tracker sweeps his
  colleagues. The number rising is the argument.
- Part 2 sweeps the skew of an agreement table with percent agreement pinned,
  and kappa collapses underneath it.
- Part 3 is the spine: the pass/fail decision sits on top of the Level 5 gauge,
  so a tracker on that gauge's sigma drives kappa, agreement and both error
  rates at once. Nobody chooses a kappa.
- Part 4 follows the disagreement density as the gauge widens, with the camera
  pushed into the limit so the band is visible as a band.
- Part 5 prices a count against a measurement.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level06_scene.py Level06
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level06_scene.py Level06
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, Group, Line, Rectangle,
    VGroup,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
    ValueTracker,
    Transform,
)

from msalab.act_style import (
    ACCENT, DATA_GAUGE, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM, RULE,
    SIGNAL_ALARM, SIGNAL_OK, gauge, micro, panel_label, prose, within_frame,
)
from msalab.attribute import (
    BASE_RATE, BOUND_AT_50, BOUND_AT_300, CROSS, GRAY_BANDS, HALF, KAPPA,
    LAZY, PARTS_FOR_MISS, appraiser_vs_appraiser, cross_table, gray_zone,
    kappa_from_table, _pass_prob,
)
from msalab.accuracy import GAUGE_SIGMA, _phi
from msalab.against_what import TOLERANCE
from msalab.measurement import PART_SIGMA
from msalab.opening import (
    closed_jaws, gauge_jaws, hand_off, part_block, plain, record_strip,
    thing_caption, tick, two_panel, value_label, stamp,
)
from msalab.narration import NarratedCameraScene


class Level06(NarratedCameraScene):
    def construct(self):
        self.part0_opening()
        self.part1_the_appraiser_who_never_looks()
        self.part2_kappa_collapses()
        self.part3_kappa_is_not_free()
        self.part4_the_band()
        self.part5_a_count_is_dear()

    # ------------------------------------------------------------- part 0
    def part0_opening(self):
        """Plain-language opening. specs/act-opening-contract.md, mode B.

        The whole level turns on the reading being gone. So the opening takes it
        away on screen: the strip and its numbers are replaced by a stamp.
        """
        panels = two_panel("the thing", "the record")
        block = part_block()
        cap = thing_caption("one bore, same as ever", block)
        jaws = gauge_jaws(block)
        strip = record_strip(-4.2, 4.2, "how far off it is, in microns")

        rng = np.random.default_rng(606)
        reads = rng.normal(0.0, 1.2, 6)
        dots = VGroup(*[tick(strip["at"](r)) for r in reads])

        with self.say("Six levels of this course have assumed the gauge gives "
                      "you a number. Here is that, one last time."):
            self.play(FadeIn(panels["all"]), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(block), FadeIn(cap), FadeIn(strip["all"]),
                      run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(FadeIn(jaws), run_time=0.4, rate_func=rf.ease_out_sine)
            self.play(Transform(jaws, closed_jaws(block)), run_time=0.8,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(dots, scale=1.6), run_time=0.8,
                      rate_func=rf.ease_out_back)

        gone = within_frame(
            plain("now take the number away.", 27, INK_BRIGHT)
            .move_to([3.2, 1.85, 0]), "opening take-away")
        with self.say("Now take it away. Some gauges do not give you a number at "
                      "all. A thread gauge fits or it does not. Somebody looks "
                      "at a weld and says yes or no."):
            self.play(FadeIn(gone, shift=DOWN * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.play(FadeOut(dots), FadeOut(strip["all"]), run_time=0.9,
                      rate_func=rf.ease_in_sine)

        s1 = stamp("PASS", [3.2, 0.35, 0], SIGNAL_OK)
        with self.say("This is all you get. One word."):
            self.play(FadeIn(s1, scale=1.5), run_time=0.8,
                      rate_func=rf.ease_out_back)

        s2 = stamp("FAIL", [3.2, -0.75, 0], SIGNAL_ALARM)
        with self.say("And when the same person looks at the same part again, "
                      "sometimes you get the other word."):
            self.play(FadeIn(s2, scale=1.5), run_time=0.9,
                      rate_func=rf.ease_out_back)

        verdict = within_frame(
            plain("there is nothing left to subtract.", 28, INK_BRIGHT)
            .move_to([3.2, -1.85, 0]), "opening verdict")
        with self.say("There is nothing left to subtract. No distance between "
                      "two answers, no width, nothing to take an average of. "
                      "And the same three questions still have to be answered."):
            self.play(FadeIn(verdict, shift=DOWN * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        hand_off(self, VGroup(block, cap, jaws), panels)
        self.play(FadeOut(Group(s1, s2, gone, verdict)), run_time=0.6,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 1
    def part1_the_appraiser_who_never_looks(self):
        title = prose("Level 6 · the gauge that says pass", 30, INK_DIM)
        title.to_edge(UP, buff=0.38)
        with self.say("Five levels of arithmetic, all of it one spread divided by "
                      "another. Now the gauge says pass, and nothing else. There "
                      "is no reading to subtract."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        claim = prose("the three questions survive the loss of the number", 27,
                      INK_BRIGHT).move_to(UP * 1.9)
        rows = VGroup(
            panel_label("repeatability    does one appraiser agree with himself",
                        22, INK),
            panel_label("reproducibility  do two appraisers agree with each other",
                        22, INK),
            panel_label("bias             does either agree with the truth",
                        22, INK),
        ).arrange(DOWN, buff=0.30, aligned_edge=LEFT).move_to(DOWN * 0.1)

        with self.say("But the three questions do not go away. Does one appraiser "
                      "agree with himself. Do two agree with each other. Does "
                      "either of them agree with the truth. Only now the answers "
                      "have to be built out of counts."):
            self.play(FadeIn(claim, shift=DOWN * 0.10), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            for r in rows:
                self.play(FadeIn(r, shift=RIGHT * 0.14), run_time=0.5,
                          rate_func=rf.ease_out_sine)

        self.beat(0.8)
        self.play(FadeOut(Group(claim, rows)), run_time=0.55,
                  rate_func=rf.ease_in_sine)

        # the lazy appraiser
        hire = prose("so hire an appraiser who passes everything", 28, INK_BRIGHT)
        hire.move_to(UP * 2.1)
        axes = Axes(x_range=[0, 4.4, 1], y_range=[0, 108, 25],
                    x_length=8.6, y_length=3.6, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.85)
        xl = panel_label("how many colleagues he is compared against", 19,
                         INK_DIM).next_to(axes, DOWN, buff=0.24)

        with self.say("So hire an appraiser who does not look at the parts at all. "
                      "He passes every one."):
            self.play(FadeIn(hire, shift=DOWN * 0.10), Create(axes), FadeIn(xl),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        n = ValueTracker(0.0)
        self_line = always_redraw(lambda: Line(
            axes.c2p(0, 100), axes.c2p(max(0.001, n.get_value()), 100),
            stroke_color=SIGNAL_OK, stroke_width=4))
        truth_line = always_redraw(lambda: Line(
            axes.c2p(0, BASE_RATE * 100),
            axes.c2p(max(0.001, n.get_value()), BASE_RATE * 100),
            stroke_color=DATA_TRUTH, stroke_width=3))
        read = always_redraw(lambda: panel_label(
            f"agrees with himself   {LAZY['self_agreement']*100:6.2f} %\n"
            f"agrees with them      {LAZY['cross_agreement']*100:6.2f} %\n"
            f"agrees with the truth {LAZY['vs_truth']*100:6.2f} %",
            22, INK).move_to(axes.c2p(2.2, 46)))
        self.add(self_line, truth_line, read)

        with self.say("Against himself he is perfect - he never contradicts "
                      "himself, because he never decides anything. Against a "
                      "colleague with the same habit, also perfect. And against "
                      "the truth he scores ninety nine point nine percent, "
                      "because that is how many parts were good."):
            self.play(n.animate.set_value(4.2), run_time=4.2,
                      rate_func=rf.ease_in_out_sine)

        verdict = within_frame(
            VGroup(
                prose("and he missed every bad part that was made", 28,
                      SIGNAL_ALARM),
                panel_label(f"miss rate  {LAZY['miss_rate']*100:.0f} %", 24,
                            SIGNAL_ALARM),
            ).arrange(DOWN, buff=0.22).move_to(axes.c2p(2.2, 16)),
            "part 1 verdict")
        with self.say("And he missed one hundred percent of the bad parts. Percent "
                      "agreement cannot see him. Nothing about the gauge, and "
                      "nothing about him, entered that number - only the base "
                      "rate of the process."):
            self.play(FadeIn(verdict, shift=UP * 0.10), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 2
    def part2_kappa_collapses(self):
        title = prose("kappa removes the chance agreement", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[48, 102, 10], y_range=[0, 108, 25],
                    x_length=8.4, y_length=3.7, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.6 + LEFT * 0.5)
        xl = panel_label("share of the agreement sitting in the 'pass' cell, %",
                         19, INK_DIM).next_to(axes, DOWN, buff=0.24)

        with self.say("The fix is old and well known. Subtract the agreement two "
                      "people would reach by chance, and report only what is left "
                      "over. That is Cohen's kappa, and it sees straight through "
                      "the appraiser who never looks - it cannot even be computed "
                      "for him, because chance explains everything he did."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        obs = 0.90
        shares = np.linspace(0.50, 0.99, 60)
        ks = [kappa_from_table(obs * s, (1 - obs) / 2, (1 - obs) / 2,
                               obs * (1 - s))["kappa"] for s in shares]
        k = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(k.get_value() * (len(shares) - 1)), 0,
                               len(shares) - 1))

        flat = Line(axes.c2p(50, obs * 100), axes.c2p(99, obs * 100),
                    stroke_color=DATA_TRUTH, stroke_width=3)
        flat_tag = within_frame(
            panel_label("percent agreement - pinned at 90 %", 20, DATA_TRUTH)
            .next_to(axes.c2p(74.5, obs * 100), UP, buff=0.14),
            "part 2 pinned tag")
        curve = always_redraw(lambda: VGroup(*[
            Line(axes.c2p(shares[i] * 100, ks[i] * 100),
                 axes.c2p(shares[i + 1] * 100, ks[i + 1] * 100),
                 stroke_color=SIGNAL_ALARM, stroke_width=3.6)
            for i in range(idx())]))
        read = always_redraw(lambda: panel_label(
            f"observed {obs*100:.0f} %     kappa {ks[idx()]:.3f}", 24,
            SIGNAL_ALARM).move_to(axes.c2p(62, 22)))

        with self.say("Now hold the percent agreement still. Ninety percent, "
                      "every table, no exceptions."):
            self.play(Create(flat), FadeIn(flat_tag), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
        self.add(curve, read)

        with self.say("And move only one thing: how lopsided the stream is. As the "
                      "agreement piles into the pass cell, kappa falls from point "
                      "eight to point one. Same percent agreement throughout. The "
                      "trouble is which end a good process lives at - it lives at "
                      "the right-hand end, so being capable depresses kappa all by "
                      "itself."):
            self.play(k.animate.set_value(1.0), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.1)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 3
    def part3_kappa_is_not_free(self):
        title = prose("nobody chooses a kappa", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        with self.say("Which raises the question of where kappa comes from at all. "
                      "And the answer is the whole of this level."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        # x_length 8.2 shifted LEFT 1.2 put the axes' right edge at x=2.9,
        # which is inside the four-line readout block. Measured, not guessed.
        axes = Axes(x_range=[0, 175, 50], y_range=[0, 108, 25],
                    x_length=6.9, y_length=3.6, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.7 + LEFT * 2.3)
        xl = panel_label("the variable gauge underneath, %GRR of tolerance", 19,
                         INK_DIM).next_to(axes, DOWN, buff=0.24)

        with self.say("Behind every go/no-go gauge there is a real dimension and a "
                      "real instrument. The appraiser has no number, but the thing "
                      "in his hand does, and it is the gauge Levels two to five "
                      "built. So sweep that gauge's sigma."):
            self.play(Create(axes), FadeIn(xl), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)

        gs = np.linspace(0.4, 8.7, 55)
        pre = [{"grr": 6.0 * g / TOLERANCE * 100.0,
                "agree": appraiser_vs_appraiser(gauge=float(g))["agreement"],
                "kappa": appraiser_vs_appraiser(gauge=float(g))["kappa"],
                "miss": cross_table(gauge=float(g))["miss_rate"]}
               for g in gs]
        t = ValueTracker(0.0)

        def idx():
            return int(np.clip(round(t.get_value() * (len(gs) - 1)), 0,
                               len(gs) - 1))

        def track(key, colour, width):
            return always_redraw(lambda: VGroup(*[
                Line(axes.c2p(pre[i]["grr"], pre[i][key] * 100),
                     axes.c2p(pre[i + 1]["grr"], pre[i + 1][key] * 100),
                     stroke_color=colour, stroke_width=width)
                for i in range(idx())]))

        agree = track("agree", DATA_TRUTH, 3.0)
        kap = track("kappa", SIGNAL_ALARM, 3.6)
        miss = track("miss", DATA_GAUGE, 2.4)
        read = always_redraw(lambda: panel_label(
            f"%GRR      {pre[idx()]['grr']:6.1f} %\n"
            f"agreement {pre[idx()]['agree']*100:6.2f} %\n"
            f"kappa     {pre[idx()]['kappa']:6.3f}\n"
            f"miss rate {pre[idx()]['miss']*100:6.2f} %", 22, INK)
            .move_to(RIGHT * 4.15 + DOWN * 0.5))
        self.add(agree, kap, miss, read)

        with self.say("Every number an attribute study reports moves, and all of "
                      "them move together, because all of them are functions of "
                      "one sigma. Agreement stays high and comfortable. Kappa "
                      "falls off a cliff. The miss rate climbs. Nobody chose any "
                      "of it."):
            self.play(t.animate.set_value(1.0), run_time=5.2,
                      rate_func=rf.ease_in_out_sine)

        here = 6.0 * GAUGE_SIGMA / TOLERANCE * 100.0
        rule = DashedLine(axes.c2p(here, 0), axes.c2p(here, 104),
                          dash_length=0.13, stroke_color=ACCENT,
                          stroke_width=2.4)
        mine = appraiser_vs_appraiser()
        tag = within_frame(
            panel_label(f"the gauge from Level 5\n"
                        f"agreement {mine['agreement']*100:.2f} %\n"
                        f"kappa {mine['kappa']:.3f}", 21, ACCENT)
            .move_to(axes.c2p(112, 66)), "part 3 accent tag")
        with self.say("And here is where our own gauge sits. Ninety nine and a "
                      "half percent agreement, which reads like a pass. Kappa "
                      "nought point three four, which every published guideline "
                      "calls unacceptable. Those are the same gauge, on the same "
                      "day, measured two ways."):
            self.play(Create(rule), FadeIn(tag), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)

        self.beat(1.2)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 4
    def part4_the_band(self):
        title = prose("so 'appraiser error' is mostly the instrument", 29,
                      INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        axes = Axes(x_range=[-24, 24, 8], y_range=[0, 1.28, 0.5],
                    x_length=9.6, y_length=3.5, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.75)
        xl = panel_label("the part's true size, µm from nominal", 19, INK_DIM)
        xl.next_to(axes, DOWN, buff=0.24)

        with self.say("Which tells you where the disagreements have to be. A part "
                      "far inside the limit is never failed. A part far outside is "
                      "never passed."):
            self.play(FadeIn(title, shift=DOWN * 0.12), Create(axes), FadeIn(xl),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        xs = np.linspace(-24, 24, 481)
        parts = np.array([_phi(float(x), PART_SIGMA) for x in xs])
        parts_curve = axes.plot_line_graph(
            xs, parts / parts.max(), add_vertex_dots=False,
            line_color=INK_DIM, stroke_width=2)["line_graph"]
        limits = VGroup(*[
            Line(axes.c2p(v, 0), axes.c2p(v, 1.16), stroke_color=DATA_TRUTH,
                 stroke_width=2.2) for v in (-HALF, HALF)])
        lim_tag = within_frame(
            panel_label("the go/no-go limits", 19, DATA_TRUTH)
            .next_to(axes.c2p(HALF, 1.16), UP, buff=0.10).shift(LEFT * 0.15),
            "part 4 limit tag")

        with self.say("Here is where the parts are, and here are the limits."):
            self.play(Create(parts_curve), Create(limits), FadeIn(lim_tag),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        g = ValueTracker(0.35)

        def dis_at(gv):
            d = np.array([_phi(float(x), PART_SIGMA)
                          * 2.0 * _pass_prob(float(x), gauge=gv)
                          * (1.0 - _pass_prob(float(x), gauge=gv))
                          for x in xs])
            m = d.max()
            return d / m if m > 0 else d

        dis = always_redraw(lambda: axes.plot_line_graph(
            xs, dis_at(g.get_value()), add_vertex_dots=False,
            line_color=SIGNAL_ALARM, stroke_width=4)["line_graph"])
        read = always_redraw(lambda: (lambda r: within_frame(panel_label(
            f"gauge σ {g.get_value():4.2f} µm\n"
            f"±3σ  band:  {r['parts_in_band_pct']:5.2f} % of production, "
            f"{r['disagreements_in_band_pct']:5.1f} % of the mistakes",
            20, SIGNAL_ALARM).move_to(axes.c2p(0, -0.34)),
            "part 4 band readout"))(
                gray_zone(gauge=g.get_value(), sigmas=3.0)))
        self.add(dis, read)

        with self.say("And here is where the disagreements are - a spike at each "
                      "limit, and nothing anywhere else. Widen the gauge and the "
                      "spikes widen with it. The band belongs to the instrument, "
                      "not to the person holding it."):
            self.play(g.animate.set_value(4.2), run_time=4.4,
                      rate_func=rf.ease_in_out_sine)

        with self.say("Bring it back to our own gauge, and look at the size of it."):
            self.play(g.animate.set_value(GAUGE_SIGMA), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)

        # the readout and the axis label are sized for the wide frame; at 0.44x
        # they are a wall and a clipped word, so both leave before the camera
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(read), FadeOut(xl), run_time=0.45,
                  rate_func=rf.ease_in_sine)
        dis_now = axes.plot_line_graph(
            xs, dis_at(GAUGE_SIGMA), add_vertex_dots=False,
            line_color=SIGNAL_ALARM, stroke_width=4)["line_graph"]
        self.add(dis_now)

        # Restore() left the frame zoomed - part 5's title rendered at 0.44x.
        # Animating back to the captured width and centre is deterministic and
        # does not depend on save_state surviving the updater teardown above.
        home_w = self.camera.frame.width
        home_c = self.camera.frame.get_center()
        with self.say("Six percent of everything this plant makes sits in that "
                      "band, and it produces ninety nine percent of every "
                      "disagreement the study will ever record. Which is why "
                      "retraining the appraiser does so little."):
            self.play(self.camera.frame.animate.scale(0.44)
                      .move_to(axes.c2p(HALF, 0.42)), run_time=2.4,
                      rate_func=rf.ease_in_out_sine)
        self.play(self.camera.frame.animate.set(width=home_w).move_to(home_c),
                  run_time=1.5, rate_func=rf.ease_in_out_sine)

        self.beat(1.0)
        for m in self.mobjects:
            m.clear_updaters()
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

    # ------------------------------------------------------------- part 5
    def part5_a_count_is_dear(self):
        title = prose("and a count costs more than a measurement", 30, INK_BRIGHT)
        title.to_edge(UP, buff=0.38)

        with self.say("One more bill to pay. A count carries less information than "
                      "a measurement, and the arithmetic charges for it."):
            self.play(FadeIn(title, shift=DOWN * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        rows = VGroup(
            panel_label("Level 2 settled a variance with", 22, INK_DIM),
            panel_label("10 parts × 3 operators × 3 trials = 90 readings", 24,
                        SIGNAL_OK),
            panel_label("bounding a 5 % miss rate to ±2 points needs", 22,
                        INK_DIM),
            panel_label(f"{PARTS_FOR_MISS} known-bad parts", 26, SIGNAL_ALARM),
        ).arrange(DOWN, buff=0.34).move_to(UP * 0.85)

        with self.say("Level two settled a whole variance with ninety readings. "
                      "Bounding a five percent miss rate to plus or minus two "
                      "points needs four hundred and fifty seven known-bad parts - "
                      "and a plant that can find four hundred and fifty seven bad "
                      "parts has a different problem."):
            for r in rows:
                self.play(FadeIn(r, shift=UP * 0.10), run_time=0.6,
                          rate_func=rf.ease_out_sine)

        weak = within_frame(
            VGroup(
                prose("and 'we found no escapes' is weak evidence", 27,
                      INK_BRIGHT),
                panel_label(f"zero misses in  50 bad parts still allows "
                            f"{BOUND_AT_50*100:.2f} %", 22, SIGNAL_ALARM),
                panel_label(f"zero misses in 300 bad parts still allows "
                            f"{BOUND_AT_300*100:.2f} %", 22, INK),
            ).arrange(DOWN, buff=0.26).move_to(DOWN * 1.85),
            "part 5 weak evidence")

        with self.say("Which is why the most common result of an attribute study - "
                      "no escapes found - says so much less than it sounds. Zero "
                      "misses in fifty bad parts is still consistent with a miss "
                      "rate near six percent."):
            self.play(FadeIn(weak, shift=UP * 0.10), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        self.beat(1.0)
        self.play(FadeOut(Group(*self.mobjects)), run_time=0.7,
                  rate_func=rf.ease_in_sine)

        closing = VGroup(
            prose("six levels have described one measurement system", 30,
                  INK_BRIGHT),
            panel_label("Level 7 hands it back to the process it was built to "
                        "watch", 22, INK_DIM),
        ).arrange(DOWN, buff=0.36)
        with self.say("So six levels have now described one measurement system, "
                      "from a single reading to a gauge with no reading at all. "
                      "Level seven hands it back to the process it was built to "
                      "watch."):
            self.play(FadeIn(closing, shift=DOWN * 0.10), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        self.beat(1.2)
