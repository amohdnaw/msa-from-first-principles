"""LEVEL 4, act A - 'the gauge does not own a verdict'.

Built against `storyboards/msa-level-04-act-a.html`, shot for shot. The act has
one job: show that the denominator chooses the question, so that a reviewer
watching with the sound off can say why one unchanged gauge earns opposite
readings.

The rule the whole act is built on: **one amber band, created once, never
resized.** It is made in shot 01 out of repeated readings and it is still the
same Mobject at the end of shot 08. Everything that moves is a denominator - the
study spread grows and contracts behind it, the drawing boundaries sweep past
it - and no camera move is allowed to change the band's size on screen, which is
why shot 01 is framed for the widest length the act will ever draw.

    01  one width, no verdict            the band is made out of readings
    02  commit before dividing           the prediction pins; two empty slots open
    03  the parts arrive                 the study spread grows from behind it
    04  the drawing arrives              boundaries drop in and sweep across
    05  same numerator, two questions    the first two symbols of the act
    06  improve the process, ruin it     one readout climbs, the other holds
    07  the flip point                   the gate crossings are part spreads
    08  the same gauge, after all of it  back to shot 01, plus two denominators

The number of distinct categories does not appear anywhere in this act. It
re-expresses a ratio the learner has not yet used to decide anything, so it
belongs to act B, after a decision job exists to be re-expressed.

Every length and every printed number comes from `msalab.against_what` at render
time. Nothing here is typed twice.

    silent:   PYTHONPATH=src .venv/bin/manim -qh src/msalab/level04_scene.py Level04
    narrated: MSALAB_VOICE=1 PYTHONPATH=src .venv/bin/manim -qh src/msalab/level04_scene.py Level04
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Create, DashedLine, Dot, FadeIn, FadeOut, LaggedStart, Line, MathTex,
    Rectangle, ReplacementTransform, Transform, VGroup, ValueTracker,
    always_redraw, rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
)

from msalab.act_style import (
    ACCENT, DATA_OBSERVED, DATA_TRUTH, EDGE_MARGIN, FRAME_RIGHT, INK,
    INK_BRIGHT, INK_DIM, RULE, RULE_STRONG, micro, panel_label, prose,
    within_frame,
)
from msalab.against_what import (
    ACCEPT_PCT, BAND, GAUGE_SIGMA, REJECT_PCT, STUDY_PCT, TIGHTEN_FROM,
    TIGHTEN_TO, TOLERANCE, TOL_PCT, study_ratio, tolerance_ratio,
)
from msalab.measurement import PART_SIGMA, SEED, observed_sigma
from msalab.narration import NarratedCameraScene
from msalab.opening import (
    bar_caption, hand_off, part_block, plain, span_bar, thing_caption,
    two_panel,
)

# ------------------------------------------------------------------- geometry
#: The widest and tightest drawing the shot 04 sweep visits. Both are lengths
#: composed from `against_what` rather than staging numbers: the tight end puts
#: the boundaries exactly on the gauge band's own edges, and the wide end is
#: that same gauge width added to the drawing this level actually has.
SWEEP_TIGHT = 6.0 * GAUGE_SIGMA
SWEEP_WIDE = TOLERANCE + 6.0 * GAUGE_SIGMA

#: Shot 01 is framed for the widest length the act will ever draw, so the amber
#: band never has to be resized and no shot needs a pull-back. Scene units per
#: micron, fixed for the whole act.
_ROOM = FRAME_RIGHT - EDGE_MARGIN - 0.42
SCALE = _ROOM / (SWEEP_WIDE / 2.0)

GAUGE_W = 6.0 * GAUGE_SIGMA * SCALE
BAND_H = 0.56
STUDY_H = 1.16

RAIL_Y = 0.0
STUDY_Y = 1.35
TOL_Y = -1.35
CAP_STUDY_Y = 2.06
CAP_TOL_Y = -2.06
BOUND_TOP, BOUND_BOT = 1.70, -1.70

#: Where the pinned prediction lives, from shot 02 to shot 08.
PIN = [-4.30, 3.00, 0]
#: Where the gauge band parks while shot 07 owns the frame with an axis.
PARK = [4.30, 2.95, 0]

#: The opening compares the same three lengths, so it uses their true
#: proportions on the record strip's own span rather than drawn-by-eye bars.
OPEN_LEFT, OPEN_RIGHT = 0.55, 6.40
OPEN_SCALE = (OPEN_RIGHT - OPEN_LEFT) / (6.0 * observed_sigma(PART_SIGMA,
                                                              GAUGE_SIGMA))


def _measure(half: float, y: float, colour: str, sw: float = 2.2) -> VGroup:
    """A length with both of its ends marked. A denominator, drawn to scale."""
    return VGroup(
        Line([-half, y, 0], [half, y, 0], stroke_color=colour, stroke_width=sw),
        Line([-half, y - 0.15, 0], [-half, y + 0.15, 0], stroke_color=colour,
             stroke_width=sw),
        Line([half, y - 0.15, 0], [half, y + 0.15, 0], stroke_color=colour,
             stroke_width=sw),
    )


def _study_span(part: float) -> float:
    """Six sigma of what the study observed, in scene units."""
    return 6.0 * observed_sigma(part, GAUGE_SIGMA) * SCALE


def _study_shape(part: float) -> VGroup:
    """The study spread: a band behind the gauge band, and its measured length.

    At `part = 0` this is exactly the gauge band's own width, which is why shot
    03 can grow it out from behind the amber band with no cut and no rebuild.
    """
    w = _study_span(part)
    return VGroup(
        Rectangle(width=w, height=STUDY_H, fill_color=DATA_OBSERVED,
                  fill_opacity=0.18, stroke_color=DATA_OBSERVED,
                  stroke_width=1.8).move_to([0.0, RAIL_Y, 0]),
        _measure(w / 2.0, STUDY_Y, DATA_OBSERVED),
    )


def _drawing_shape(gap: float) -> VGroup:
    """The drawing: two hard boundaries and the length between them."""
    hx = gap * SCALE / 2.0
    return VGroup(
        Line([-hx, BOUND_BOT, 0], [-hx, BOUND_TOP, 0], stroke_color=DATA_TRUTH,
             stroke_width=2.6),
        Line([hx, BOUND_BOT, 0], [hx, BOUND_TOP, 0], stroke_color=DATA_TRUTH,
             stroke_width=2.6),
        _measure(hx, TOL_Y, DATA_TRUTH),
    )


def _empty_slot(y: float) -> DashedLine:
    """A denominator slot with nothing in it yet."""
    return DashedLine([-_ROOM, y, 0], [_ROOM, y, 0], dash_length=0.11,
                      stroke_color=RULE, stroke_width=1.6)


def _edge_ghost() -> VGroup:
    """Where the band's edges stood in shot 01, marked so the eye can check.

    An outline traced over the band is invisible precisely because the band
    never moves, which makes the check unwatchable. Two dashed verticals at the
    shot 01 edges, taller than the band, stay legible against every denominator
    that passes behind them - and the band landing exactly between them is a
    thing a muted viewer can see.
    """
    hx = GAUGE_W / 2.0
    return VGroup(*[
        DashedLine([x, RAIL_Y - 0.84, 0], [x, RAIL_Y + 0.84, 0],
                   dash_length=0.09, stroke_color=ACCENT,
                   stroke_width=2.0).set_stroke(opacity=0.75)
        for x in (-hx, hx)])


class Level04(NarratedCameraScene):
    def construct(self):
        self.part0_opening()
        self.shot01_one_width()
        self.shot02_commit_before_dividing()
        self.shot03_the_parts_arrive()
        self.shot04_the_drawing_arrives()
        self.shot05_same_numerator()
        self.shot06_improve_the_process()
        self.shot07_the_flip_point()
        self.shot08_the_same_gauge()

    # ------------------------------------------------------------- helpers
    def _freeze(self, *mobs):
        """Stop updaters before anything is faded, so nothing redraws itself
        back into the frame halfway through its own exit."""
        for m in mobs:
            m.clear_updaters()

    def _home(self):
        return self.camera.frame.width, self.camera.frame.get_center()

    # ------------------------------------------------------------- part 0
    def part0_opening(self):
        """Plain-language opening. specs/act-opening-contract.md, mode B.

        This level's record holds widths rather than positions, and the three
        widths are the three the act then argues about, drawn at their true
        proportions so the opening cannot promise a ratio the act disproves.
        """
        panels = two_panel("the thing", "the record")
        block = part_block()
        cap = thing_caption("the gauge from the last three levels", block)

        with self.say("Three levels have measured how much this gauge wobbles. "
                      "Here it is, as a width."):
            self.play(FadeIn(panels["all"]), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(block), FadeIn(cap), run_time=0.7,
                      rate_func=rf.ease_out_sine)

        g = span_bar(6.0 * GAUGE_SIGMA * OPEN_SCALE, 1.20, ACCENT,
                     left=OPEN_LEFT)
        gl = bar_caption("how much the gauge wobbles", g)
        with self.say("That is the whole of what the first three levels "
                      "produced. One width."):
            self.play(FadeIn(g, shift=RIGHT * 0.14), FadeIn(gl), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        p_bar = span_bar(6.0 * observed_sigma(PART_SIGMA, GAUGE_SIGMA)
                         * OPEN_SCALE, -0.05, DATA_OBSERVED, left=OPEN_LEFT)
        pl = bar_caption("how much the parts differ", p_bar)
        with self.say("Now: a width on its own means nothing. It has to be held "
                      "against something. Here is one candidate, how much the "
                      "parts differ from each other."):
            self.play(FadeIn(p_bar, shift=RIGHT * 0.14), FadeIn(pl),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        t_bar = span_bar(TOLERANCE * OPEN_SCALE, -1.30, DATA_TRUTH,
                         left=OPEN_LEFT)
        tl = bar_caption("what the drawing allows", t_bar)
        with self.say("And here is another, completely unrelated to the first: "
                      "how much room the drawing gives you."):
            self.play(FadeIn(t_bar, shift=RIGHT * 0.14), FadeIn(tl),
                      run_time=1.0, rate_func=rf.ease_out_sine)

        question = within_frame(
            plain("a percentage of which one?", 30, INK_BRIGHT)
            .move_to([3.0, -2.45, 0]), "opening question")
        with self.say("The gauge fits inside both of them, and it fits by "
                      "different amounts. So when somebody hands you a "
                      "percentage, the only question that matters is which of "
                      "these two they divided by."):
            self.play(FadeIn(question, shift=DOWN * 0.10), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        self.beat(0.9)
        hand_off(self, VGroup(block, cap), panels)
        self.play(FadeOut(VGroup(g, gl, p_bar, pl, t_bar, tl, question)),
                  run_time=0.6, rate_func=rf.ease_in_sine)

    # -------------------------------------------------------------- shot 01
    def shot01_one_width(self):
        """One width, no verdict. The persistent band is created here."""
        self.title = prose("Level 4 · a percentage of what?", 26, INK_DIM)
        self.title.to_edge(UP, buff=0.34)

        rail = Line([-GAUGE_W / 2 - 1.15, RAIL_Y, 0],
                    [GAUGE_W / 2 + 1.15, RAIL_Y, 0],
                    stroke_color=RULE_STRONG, stroke_width=1.6)
        rail_cap = within_frame(
            panel_label("one part, measured again and again", 20, INK_DIM)
            .move_to([0.0, RAIL_Y - 0.95, 0]), "shot 01 rail caption")

        with self.say("One part, and the gauge the last three levels measured. "
                      "Nothing is touched between readings."):
            self.play(FadeIn(self.title, shift=DOWN * 0.12), Create(rail),
                      FadeIn(rail_cap), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        rng = np.random.default_rng(SEED)
        dots = VGroup(*[Dot([v * SCALE, RAIL_Y, 0], radius=0.072, color=ACCENT)
                        for v in rng.normal(0.0, GAUGE_SIGMA, 13)])
        dots.set_opacity(0.0)
        self.add(dots)
        with self.say("Every reading lands somewhere slightly different, and "
                      "the scatter they make has a width of its own."):
            self.play(LaggedStart(*[d.animate.set_opacity(1.0) for d in dots],
                                  lag_ratio=0.16), run_time=2.2,
                      rate_func=rf.ease_out_sine)

        self.band = Rectangle(width=GAUGE_W, height=BAND_H, fill_color=ACCENT,
                              fill_opacity=0.85, stroke_color=ACCENT,
                              stroke_width=0).move_to([0.0, RAIL_Y, 0])
        self.band_tag = within_frame(
            panel_label(f"gauge 6σ   {6.0 * GAUGE_SIGMA:.1f} µm", 21, ACCENT)
            .move_to([0.0, RAIL_Y - 0.95, 0]), "shot 01 band tag")

        with self.say("Three levels of work produced one width. There is no "
                      "verdict inside it."):
            self.play(ReplacementTransform(dots, self.band),
                      FadeOut(rail), Transform(rail_cap, self.band_tag),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
        # rail_cap now *is* the tag on screen; swap in the real object so the
        # later shots can move the tag along with the band
        self.remove(rail_cap)
        self.add(self.band_tag)
        self.beat(0.8)

    # -------------------------------------------------------------- shot 02
    def shot02_commit_before_dividing(self):
        """The prediction gate. Two empty slots, no number in either."""
        self.prediction = within_frame(
            VGroup(
                micro("predict", 17, ACCENT),
                prose("can the same gauge be\nright to keep and\n"
                      "right to replace?", 21, INK_BRIGHT),
            ).arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(PIN),
            "shot 02 prediction")

        with self.say("Answer now, before any arithmetic: can the same gauge be "
                      "right to keep and right to replace?"):
            self.play(FadeOut(self.title, shift=UP * 0.10),
                      FadeIn(self.prediction, shift=DOWN * 0.10), run_time=1.1,
                      rate_func=rf.ease_out_sine)
            self.beat(1.4)

        self.slot_study = _empty_slot(STUDY_Y)
        self.slot_tol = _empty_slot(TOL_Y)
        self.cap_study = within_frame(
            panel_label("denominator ?", 21, INK_DIM)
            .move_to([0.0, CAP_STUDY_Y, 0]), "shot 02 upper slot label")
        self.cap_tol = within_frame(
            panel_label("denominator ?", 21, INK_DIM)
            .move_to([0.0, CAP_TOL_Y, 0]), "shot 02 lower slot label")

        with self.say("Whatever happens next, the top of the fraction is "
                      "already fixed. You cannot edit it. The only thing left "
                      "to choose is the length that goes underneath."):
            self.play(Create(self.slot_study), Create(self.slot_tol),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(self.cap_study, shift=DOWN * 0.08),
                      FadeIn(self.cap_tol, shift=UP * 0.08), run_time=0.8,
                      rate_func=rf.ease_out_sine)
        self.beat(0.7)

    # -------------------------------------------------------------- shot 03
    def shot03_the_parts_arrive(self):
        """The study spread grows out from behind the band. The band holds."""
        self.part_t = ValueTracker(0.0)
        self.study = always_redraw(
            lambda: _study_shape(self.part_t.get_value()))
        self.add(self.study)
        self.bring_to_front(self.band, self.band_tag)

        name_study = within_frame(
            prose("how much these parts differ", 23, DATA_OBSERVED)
            .move_to([0.0, CAP_STUDY_Y, 0]), "shot 03 study name")

        with self.say("Here is one thing you could hold the gauge against: how "
                      "much these parts differ from each other. Watch the amber "
                      "band while it arrives."):
            self.play(self.part_t.animate.set_value(PART_SIGMA),
                      Transform(self.cap_study, name_study),
                      run_time=3.0, rate_func=rf.ease_in_out_sine)

        with self.say("The band did not move and it did not widen. The change "
                      "came from behind it, and the share of that length the "
                      "amber band covers has already changed."):
            self.beat(1.6)

    # -------------------------------------------------------------- shot 04
    def shot04_the_drawing_arrives(self):
        """The drawing boundaries drop in, then travel. Nothing answers."""
        drop = _drawing_shape(TOLERANCE)
        name_tol = within_frame(
            prose("what the drawing allows", 23, DATA_TRUTH)
            .move_to([0.0, CAP_TOL_Y, 0]), "shot 04 drawing name")

        with self.say("Here is the other one. This length came off a drawing. "
                      "Nobody measured a part to get it."):
            self.play(FadeIn(drop, shift=DOWN * 0.9),
                      Transform(self.cap_tol, name_tol), run_time=1.3,
                      rate_func=rf.ease_out_sine)

        self.tol_t = ValueTracker(TOLERANCE)
        self.drawing = always_redraw(
            lambda: _drawing_shape(self.tol_t.get_value()))
        self.remove(drop)
        self.add(self.drawing)
        self.bring_to_front(self.band, self.band_tag)

        with self.say("A drawing can be redrawn. Watch everything else in the "
                      "frame while it is."):
            self.play(self.tol_t.animate.set_value(SWEEP_WIDE), run_time=1.8,
                      rate_func=rf.ease_in_out_sine)
            self.play(self.tol_t.animate.set_value(SWEEP_TIGHT), run_time=2.6,
                      rate_func=rf.ease_in_out_sine)

        with self.say("The boundaries crossed the whole study spread in both "
                      "directions, and no part, no reading and no band "
                      "answered. So these two lengths cannot be measuring the "
                      "same question."):
            self.play(self.tol_t.animate.set_value(TOLERANCE), run_time=1.8,
                      rate_func=rf.ease_in_out_sine)
            self.beat(1.0)

    # -------------------------------------------------------------- shot 05
    def shot05_same_numerator(self):
        """The first two symbols of the act, after both lengths exist."""
        self.copy_study = self.band.copy()
        self.copy_tol = self.band.copy()
        self.add(self.copy_study, self.copy_tol)
        on_study = self.band.copy().stretch_to_fit_height(0.20)
        on_study.move_to([0.0, STUDY_Y, 0])
        on_tol = self.band.copy().stretch_to_fit_height(0.20)
        on_tol.move_to([0.0, TOL_Y, 0])

        with self.say("One numerator, two denominators. The same amber length, "
                      "laid on each of them in turn."):
            self.play(Transform(self.copy_study, on_study),
                      Transform(self.copy_tol, on_tol), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        sym_study = MathTex(r"\%GRR_{\text{study}}", font_size=34,
                            color=DATA_OBSERVED)
        val_study = panel_label(f"{STUDY_PCT:5.1f} %", 25, DATA_OBSERVED)
        row_study = within_frame(
            VGroup(sym_study, val_study).arrange(RIGHT, buff=0.28)
            .move_to([0.0, CAP_STUDY_Y, 0]), "shot 05 study readout")

        sym_tol = MathTex(r"\%GRR_{\text{tolerance}}", font_size=34,
                          color=DATA_TRUTH)
        val_tol = panel_label(f"{TOL_PCT:5.1f} %", 25, DATA_TRUTH)
        row_tol = within_frame(
            VGroup(sym_tol, val_tol).arrange(RIGHT, buff=0.28)
            .move_to([0.0, CAP_TOL_Y, 0]), "shot 05 tolerance readout")

        with self.say("Now, and only now, the two names. Two questions: can it "
                      "sort these parts, and can it decide whether a part "
                      "conforms. Neither is wrong."):
            self.play(Transform(self.cap_study, row_study),
                      Transform(self.cap_tol, row_tol), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        # The plain names are now the symbols on screen. Swap the transformed
        # text for the real rows so the digits can go live in shot 06. At this
        # instant the part spread is TIGHTEN_FROM, which is PART_SIGMA, so the
        # live readouts render character for character what is already there.
        self.remove(self.cap_study, self.cap_tol)
        anchor_study = val_study.get_center()
        anchor_tol = val_tol.get_center()
        self.live_study = always_redraw(lambda: panel_label(
            f"{study_ratio(GAUGE_SIGMA, self.part_t.get_value()):5.1f} %", 25,
            DATA_OBSERVED).move_to(anchor_study))
        self.live_tol = always_redraw(lambda: panel_label(
            f"{tolerance_ratio():5.1f} %", 25, DATA_TRUTH).move_to(anchor_tol))
        self.sym_study, self.sym_tol = sym_study, sym_tol
        self.add(sym_study, sym_tol, self.live_study, self.live_tol)

        home_w, home_c = self._home()
        with self.say("Both of those numbers were read off the two lengths on "
                      "screen. Nothing else went into either of them."):
            self.play(self.camera.frame.animate.set(width=home_w * 0.84)
                      .move_to([0.0, 0.0, 0]), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)
            self.play(self.camera.frame.animate.set(width=home_w)
                      .move_to(home_c), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)

    # -------------------------------------------------------------- shot 06
    def shot06_improve_the_process(self):
        """Improve the process; ruin one of the two numbers."""
        self.ghost = _edge_ghost()
        ask = within_frame(
            prose("which readout moves?", 22, INK).move_to([2.90, 2.95, 0]),
            "shot 06 ask")

        with self.say("The process is about to get better. The parts will "
                      "differ less than they did. Decide which of those two "
                      "readouts moves, and in which direction."):
            self.play(FadeIn(ask, shift=DOWN * 0.10), FadeIn(self.ghost),
                      run_time=1.0, rate_func=rf.ease_out_sine)
            self.beat(1.6)

        with self.say("The gauge did not get worse. The question got harder."):
            self.play(self.part_t.animate.set_value(TIGHTEN_TO), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        home_w, home_c = self._home()
        with self.say("The outline behind the band is where it stood before the "
                      "move. And the second readout did not shift by a pixel, "
                      "because a drawing does not know what the parts did."):
            self.play(FadeOut(ask, shift=UP * 0.10),
                      self.camera.frame.animate.set(width=home_w * 0.74)
                      .move_to([0.0, -0.80, 0]), run_time=1.8,
                      rate_func=rf.ease_in_out_sine)
            self.beat(1.4)
            self.play(self.camera.frame.animate.set(width=home_w)
                      .move_to(home_c), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        with self.say("Run it backwards. Loosen the process again and the first "
                      "number recovers, with nothing done to the instrument. So "
                      "that number is reporting the parts, not the gauge."):
            self.play(self.part_t.animate.set_value(TIGHTEN_FROM), run_time=2.6,
                      rate_func=rf.ease_in_out_sine)
            self.play(self.part_t.animate.set_value(TIGHTEN_TO), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)
        self.beat(0.9)

    # -------------------------------------------------------------- shot 07
    def shot07_the_flip_point(self):
        """The gate crossings are part spreads, and one of the lines is flat."""
        self._freeze(self.study, self.drawing, self.live_study, self.live_tol)
        leaving = VGroup(self.study, self.drawing, self.slot_study,
                         self.slot_tol, self.copy_study, self.copy_tol,
                         self.sym_study, self.sym_tol, self.live_study,
                         self.live_tol, self.ghost)

        with self.say("Park the gauge in the corner, at the width it has had "
                      "since the first shot, and put the part spread on an "
                      "axis of its own."):
            self.play(FadeOut(leaving), run_time=0.9,
                      rate_func=rf.ease_in_sine)
            self.play(self.band.animate.move_to(PARK),
                      self.band_tag.animate.move_to(
                          [PARK[0], PARK[1] - 0.62, 0]),
                      run_time=1.2, rate_func=rf.ease_in_out_sine)

        axes = Axes(x_range=[1.0, 24.0, 5.0], y_range=[0, 100, 25],
                    x_length=8.6, y_length=4.1, tips=False,
                    axis_config={"stroke_color": RULE, "stroke_width": 1.5})
        axes.shift(DOWN * 0.75 + RIGHT * 0.55)
        xl = within_frame(
            panel_label("part-to-part spread, µm", 19, INK_DIM)
            .next_to(axes, DOWN, buff=0.62), "shot 07 x label")
        yl = within_frame(
            panel_label("%GRR", 19, INK_DIM)
            .next_to(axes.c2p(1.0, 100), LEFT, buff=0.16), "shot 07 y label")
        ask = within_frame(
            prose("which line is flat?", 22, INK).move_to([0.14, 2.95, 0]),
            "shot 07 ask")

        with self.say("One of the two lines about to be drawn is flat. Decide "
                      "which, then watch the parts sweep from tight to loose."):
            self.play(Create(axes), FadeIn(xl), FadeIn(yl),
                      FadeIn(ask, shift=DOWN * 0.10), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        sweep = ValueTracker(1.02)
        study_c = always_redraw(lambda: axes.plot(
            lambda x: study_ratio(GAUGE_SIGMA, x),
            x_range=[1.0, sweep.get_value()], color=DATA_OBSERVED,
            stroke_width=4))
        tol_c = always_redraw(lambda: axes.plot(
            lambda x: tolerance_ratio(), x_range=[1.0, sweep.get_value()],
            color=DATA_TRUTH, stroke_width=4))
        head = always_redraw(lambda: Dot(
            axes.c2p(sweep.get_value(),
                     study_ratio(GAUGE_SIGMA, sweep.get_value())),
            radius=0.075, color=ACCENT))
        self.add(study_c, tol_c, head)

        with self.say("The flat one is the drawing. It does not know that the "
                      "parts exist. The falling one is the study ratio, and it "
                      "falls the whole way across."):
            self.play(sweep.animate.set_value(24.0), run_time=5.0,
                      rate_func=rf.ease_in_out_sine)

        self._freeze(study_c, tol_c, head)
        gates = VGroup()
        for pct in (REJECT_PCT, ACCEPT_PCT):
            gates.add(DashedLine(axes.c2p(1.0, pct), axes.c2p(24.0, pct),
                                 dash_length=0.13, stroke_color=RULE_STRONG,
                                 stroke_width=2))
            gates.add(within_frame(
                panel_label(f"{pct:.0f} %", 19, INK_DIM)
                .next_to(axes.c2p(24.0, pct), LEFT, buff=0.14)
                .shift(UP * 0.24), f"shot 07 gate {pct:.0f}"))

        crossings = VGroup()
        for pct, part in ((REJECT_PCT, BAND["part_at_30"]),
                          (ACCEPT_PCT, BAND["part_at_10"])):
            crossings.add(Line(axes.c2p(part, 0), axes.c2p(part, pct),
                               stroke_color=ACCENT, stroke_width=2.0))
            crossings.add(Dot(axes.c2p(part, pct), radius=0.070, color=ACCENT))
            crossings.add(within_frame(
                panel_label(f"parts {part:.1f} µm", 19, ACCENT)
                .next_to(axes.c2p(part, 0), DOWN, buff=0.14),
                f"shot 07 crossing {pct:.0f}"))

        with self.say("Put the two printed gates on it. The falling line "
                      "crosses both of them. The flat line crosses neither, "
                      "anywhere across the whole sweep."):
            self.play(FadeOut(ask, shift=UP * 0.10), Create(gates),
                      run_time=1.4, rate_func=rf.ease_out_sine)

        with self.say("And the crossings are not percentages. They are part "
                      "spreads. There is a spread of parts that decides the "
                      "study verdict, and it is a fact about the parts."):
            self.play(Create(crossings), run_time=1.6,
                      rate_func=rf.ease_out_sine)
            self.beat(1.2)

        self.chart = VGroup(axes, xl, yl, study_c, tol_c, head, gates,
                            crossings)

    # -------------------------------------------------------------- shot 08
    def shot08_the_same_gauge(self):
        """Back to shot 01, plus the two denominators act B opens on."""
        with self.say("Drain all of it away."):
            self.play(FadeOut(self.chart), run_time=1.0,
                      rate_func=rf.ease_in_sine)

        ghost = _edge_ghost()
        with self.say("Here is where the band started, and here is the band. "
                      "Nothing was ever done to the instrument. Every number "
                      "that moved during this act was a denominator."):
            self.play(FadeIn(ghost), run_time=0.8, rate_func=rf.ease_out_sine)
            self.play(self.band.animate.move_to([0.0, RAIL_Y, 0]),
                      self.band_tag.animate.move_to([0.0, RAIL_Y - 0.62, 0]),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)

        settled = within_frame(
            VGroup(
                micro("you predicted", 17, ACCENT),
                prose("yes. and the reason is\nunderneath it,\n"
                      "not inside it.", 21, INK_BRIGHT),
            ).arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(PIN),
            "shot 08 settled prediction")
        with self.say("So the prediction settles. Yes, and the reason is "
                      "underneath the band rather than inside it."):
            self.play(Transform(self.prediction, settled), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)
            self.beat(1.0)

        name_study = within_frame(
            panel_label("Study variation", 24, DATA_OBSERVED)
            .move_to([0.0, STUDY_Y, 0]), "shot 08 study denominator")
        name_tol = within_frame(
            panel_label("Tolerance", 24, DATA_TRUTH)
            .move_to([0.0, -1.55, 0]), "shot 08 tolerance denominator")

        with self.say("One instrument, two questions. The percentage belongs to "
                      "the question."):
            self.play(FadeOut(self.prediction, shift=UP * 0.10),
                      FadeOut(ghost), run_time=1.0, rate_func=rf.ease_in_sine)
            self.play(FadeIn(name_study, shift=DOWN * 0.10),
                      FadeIn(name_tol, shift=UP * 0.10), run_time=1.1,
                      rate_func=rf.ease_out_sine)

        self.beat(1.6)
