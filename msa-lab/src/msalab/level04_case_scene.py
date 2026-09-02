"""LEVEL 4, act B - 'two masked plants, one gauge, opposite honest actions'.

Act A ended on one amber band with two denominator names under it and no
percentage anywhere. Act B picks that frame up unchanged and walks the same band
into two masked plants. Nothing is calibrated, adjusted or replaced between them,
and by the end the same instrument has earned `use` in one plant and `replace` in
the other, because the decision job chose the denominator.

Seven shots, `storyboards/msa-level-04-act-b.html`:

    B1  the frame Act A left      carry-in, the band measured against a ruler
    B2  factory A                 beat 1, sort process populations
    B3  factory B                 beat 2, judge drawing conformance
    B4  name the denominator      beat 3, the denominator before any percentage
    B5  opposite actions          beat 4, four computed ratios, first percentages
    B6  ndc is the same curve     beat 5, one curve, both printed gates on it
    B7  the chain                 beat 6, the five links

Three rules the cut runs on.

*The camera has exactly one home.* `construct` calls `save_state()` once and
every zoom ends in `Restore(self.camera.frame)`. The first cut of this act read
the camera's live width at the top of each shot and called that "home", so a zoom
taken in shot 01 became shot 02's resting frame and the zooms compounded instead
of unwinding: the act played permanently between 0.8 and 0.4 of full width and
labels were cropped off the edge. A live read is never a home.

*The band is one Mobject and its width is never animated.* It is created once in
B1 at Act A's own `GAUGE_W`, moved between contexts, and parked beside the chain
in B7 at exactly the width it had in B1. B4 is the single place a second band
exists, because the storyboard's split frame needs one numerator per factory, and
that second band is drawn as a copy sliding out of the first so the eye can see
where it came from.

*Every number is computed here, none is typed.* Geometry, lengths, ratios, bands
and actions come from `msalab.against_what` and `msalab.level04_mastery`. The
module-level block below asserts that the lengths this file draws and the ratios
those modules print are the same fact, so a scale change or a model change fails
at import rather than shipping a picture that disagrees with its own caption.
"""
from __future__ import annotations

import numpy as np
from manim import (
    Axes, Circle, Create, DashedLine, Dot, FadeIn, FadeOut, Indicate,
    LaggedStart, Line, Rectangle, Restore, Transform, VGroup, config,
    rate_functions as rf, DOWN, LEFT, RIGHT, UP,
)

from msalab.act_style import (
    ACCENT, EDGE_MARGIN, FRAME_LEFT, FRAME_RIGHT, INK, INK_BRIGHT, INK_DIM,
    PANEL, RULE, RULE_STRONG, SIGNAL_ALARM, SIGNAL_OK, gauge, micro,
    panel_label, prose, within_frame,
)
from msalab.against_what import (
    ACCEPT_PCT, A_PART, A_TOL, B_PART, B_TOL, GAUGE_SIGMA, NDC_GATE_GAP,
    NDC_IS_REDUNDANT, NDC_K, NDC_MIN, REJECT_PCT, STUDY_PCT_AT_NDC5, ndc,
    ndc_from_study_ratio, study_ratio, study_ratio_for_ndc, tolerance_ratio,
)
from msalab.level04_mastery import (
    ACTIONS, BAND_LABELS, DECIDING_FIELDS, DECISION_JOBS, DENOMINATORS,
    PRINTED_DP, action_for_ratio, band_label_for_ratio, challenge_case,
    denominator_for_job,
)
from msalab.level04_scene import BAND_H, GAUGE_W, PARK, SCALE
from msalab.measurement import SEED, observed_sigma
from msalab.narration import NarratedCameraScene

# ---------------------------------------------------------------------------
# The two masked factories, tied to the case bank rather than described twice
# ---------------------------------------------------------------------------
# Seeds 401 and 402 are the sorting plant and the conformance plant. Reading them
# back here is what stops this act and the challenge drifting apart: if a future
# edit re-points either blueprint, the assertions below fail at import instead of
# the video quietly telling a different story from the form underneath it.
CASE_A = challenge_case(401)
CASE_B = challenge_case(402)

if (CASE_A["part_sigma"], CASE_A["tolerance"]) != (A_PART, A_TOL):
    raise AssertionError(
        f"seed 401 is no longer the sorting plant: {CASE_A['part_sigma']}, "
        f"{CASE_A['tolerance']} against {A_PART}, {A_TOL}")
if (CASE_B["part_sigma"], CASE_B["tolerance"]) != (B_PART, B_TOL):
    raise AssertionError(
        f"seed 402 is no longer the conformance plant: {CASE_B['part_sigma']}, "
        f"{CASE_B['tolerance']} against {B_PART}, {B_TOL}")
if (CASE_A["decision_job"], CASE_B["decision_job"]) != DECISION_JOBS:
    raise AssertionError("the two factories no longer carry the two jobs")

#: The fifth chain label. The other four are `DECIDING_FIELDS` character for
#: character; this one is spelled from the answer key the module itself returns,
#: so it cannot drift from the field the page grades.
_ACTION_KEY = "action"
if _ACTION_KEY not in CASE_A["answer"]:
    raise AssertionError("the case answer no longer carries an action")
CHAIN_LABELS = DECIDING_FIELDS + (_ACTION_KEY.capitalize(),)

# ---------------------------------------------------------------------------
# The four cells: two factories by two jobs, computed the long way
# ---------------------------------------------------------------------------
#: rows are factories, columns are jobs, in `DECISION_JOBS` order.
RATIOS = (
    (study_ratio(GAUGE_SIGMA, A_PART), tolerance_ratio(GAUGE_SIGMA, A_TOL)),
    (study_ratio(GAUGE_SIGMA, B_PART), tolerance_ratio(GAUGE_SIGMA, B_TOL)),
)
PRINTED = tuple(tuple(round(v, PRINTED_DP) for v in row) for row in RATIOS)
CELL_ACTIONS = tuple(tuple(action_for_ratio(v) for v in row) for row in PRINTED)

# Beat 4 is "opposite honest actions". It is a claim about holding the job still
# and moving the gauge between plants, so it is checked column by column. If a
# model edit ever made a column agree with itself the shot would still render and
# would no longer show anything.
for _col in range(2):
    if CELL_ACTIONS[0][_col] == CELL_ACTIONS[1][_col]:
        raise AssertionError(
            f"job {DECISION_JOBS[_col]!r} gives {CELL_ACTIONS[0][_col]!r} in both "
            "plants: the act has no flip left to show")

# ---------------------------------------------------------------------------
# Geometry. One scene unit per micron is Act A's `SCALE`, so the band carries in
# at the width it left on.
# ---------------------------------------------------------------------------
FRAME_TOP = config.frame_height / 2.0
FRAME_BOTTOM = -FRAME_TOP
USABLE_X = FRAME_RIGHT - EDGE_MARGIN
#: Where a denominator too long for the frame is cut and given an open tip.
CLIP_X = USABLE_X - 0.32

GAUGE_UM = 6.0 * GAUGE_SIGMA

#: The four denominators, in microns, in the same (factory, job) order.
DENOM_UM = (
    (6.0 * observed_sigma(A_PART, GAUGE_SIGMA), A_TOL),
    (6.0 * observed_sigma(B_PART, GAUGE_SIGMA), B_TOL),
)
DENOM_LEN = tuple(tuple(um * SCALE for um in row) for row in DENOM_UM)

# The load-bearing identity of the whole act: the length this file draws under a
# band and the percentage `against_what` prints beside it are the same fact. A
# drawn denominator that did not satisfy this would be a picture arguing against
# its own caption, which is the one failure a muted read cannot survive.
for _r in range(2):
    for _c in range(2):
        _implied = GAUGE_W / DENOM_LEN[_r][_c] * 100.0
        if abs(_implied - RATIOS[_r][_c]) > 1e-9:
            raise AssertionError(
                f"cell {_r},{_c}: the drawn band is {_implied:.4f} % of the drawn "
                f"denominator but the model prints {RATIOS[_r][_c]:.4f} %")

# Two of the four denominators are longer than the frame, and which two flips
# between the plants - that is beat 4's counterexample drawn rather than stated.
# Assert both facts so a scale change cannot quietly make all four fit and delete
# the contrast.
_FITS = tuple(tuple(0.5 * DENOM_LEN[r][c] <= CLIP_X for c in range(2))
              for r in range(2))
if _FITS != ((True, False), (False, True)):
    raise AssertionError(
        f"the short denominator no longer flips between the plants: {_FITS}")

# ---------------------------------------------------------------------------
# B2, the sorting plant
# ---------------------------------------------------------------------------
#: The two process families sit exactly one gauge band apart, centre to centre.
#: Not a staging number: it makes "close together on purpose" a length the shot
#: can lay the persistent band across and a viewer can check by eye.
A_GAP = GAUGE_UM
A_N = 24
A_OBS = observed_sigma(A_PART, GAUGE_SIGMA)


def _sorting_batch() -> tuple[np.ndarray, np.ndarray]:
    """One recorded batch of parts for the sorting plant.

    The shot needs a batch whose truth marks are separable and whose readings are
    not, which is a property of the draw rather than of the distribution: at this
    separation most batches interleave by one part or by none, and one stray
    crossing does not read as an overlap. So the batch is searched for rather
    than assumed, and the search states its conditions:

      * every truth mark stays on its own side of the sorting line,
      * the two truth ranges leave a gap of at least 2 microns,
      * the two reading ranges overlap by at least 6 microns,
      * and at least five parts from each family land inside that overlap.

    Raising when no seed in the sweep qualifies is deliberate. A silent fallback
    to the last seed tried would render a shot that shows nothing.
    """
    for seed in range(SEED, SEED + 6000):
        rng = np.random.default_rng(seed)
        t_lo = rng.normal(-0.5 * A_GAP, A_PART, A_N)
        t_hi = rng.normal(+0.5 * A_GAP, A_PART, A_N)
        err = rng.normal(0.0, GAUGE_SIGMA, 2 * A_N)
        r_lo, r_hi = t_lo + err[:A_N], t_hi + err[A_N:]
        if t_hi.min() - t_lo.max() < 2.0:
            continue
        if r_lo.max() - r_hi.min() < 6.0:
            continue
        if np.sum(r_lo > r_hi.min()) < 5 or np.sum(r_hi < r_lo.max()) < 5:
            continue
        return np.concatenate([t_lo, t_hi]), np.concatenate([r_lo, r_hi])
    raise RuntimeError(
        "no seed in the sweep separates the truth marks while interleaving the "
        "readings; widen the sweep or reconsider the separation")


A_TRUTH, A_READ = _sorting_batch()
A_TRUTH_GAP = float(A_TRUTH[A_N:].min() - A_TRUTH[:A_N].max())
A_READ_OVERLAP = float(A_READ[:A_N].max() - A_READ[A_N:].min())

# ---------------------------------------------------------------------------
# B3, the conformance plant
# ---------------------------------------------------------------------------
B_LIMIT = B_TOL / 2.0
#: The window in which the gauge can flip a conformance call is three sigma of
#: gauge either side of the limit - which is the persistent band's own width,
#: laid on the boundary. That is the shot, and it is not a coincidence to stage.
B_WINDOW = 0.5 * GAUGE_UM
B_N = 40
B_OBS = observed_sigma(B_PART, GAUGE_SIGMA)
B_SPREAD_UM = 6.0 * B_OBS
#: The conformance plant is drawn off centre so the band sitting on the upper
#: limit clears the right edge. Pure framing: no length changes.
B_SHIFT = -1.30


def _boundary_batch() -> tuple[np.ndarray, np.ndarray]:
    """The parts near the upper drawing limit, and what the gauge called them.

    Four to eight parts land inside the band laid on the limit, at least two of
    them are inside the drawing and read outside, and at least two are outside
    and read inside. Both directions are required: one direction alone reads as a
    gauge that is biased rather than one that is noisy.
    """
    for seed in range(SEED, SEED + 4000):
        rng = np.random.default_rng(seed)
        truth = rng.normal(0.0, B_PART, B_N)
        read = truth + rng.normal(0.0, GAUGE_SIGMA, B_N)
        near = (truth > B_LIMIT - B_WINDOW) & (truth < B_LIMIT + B_WINDOW)
        t, r = truth[near], read[near]
        if not 4 <= t.size <= 8:
            continue
        if np.any(np.abs(r - B_LIMIT) > B_WINDOW + 1.0):
            continue
        if np.sum((t < B_LIMIT) & (r > B_LIMIT)) < 2:
            continue
        if np.sum((t > B_LIMIT) & (r < B_LIMIT)) < 2:
            continue
        order = np.argsort(t)
        return t[order], r[order]
    raise RuntimeError(
        "no seed in the sweep puts a part on each wrong side of the drawing "
        "limit; widen the sweep")


B_TRUTH, B_READ = _boundary_batch()

# ---------------------------------------------------------------------------
# B4 rows, B5 grid, B6 axes, B7 chain
# ---------------------------------------------------------------------------
ROW_Y = (1.65, -1.85)
#: offsets inside one B4 row, from the row's own centre.
D_BAND, D_RULE, D_SLOT = 1.00, 0.52, 0.05
D_CAND = (-0.60, -1.35)
D_CAND_LABEL = 0.26
SLOT_HALF = 2.10
LABEL_X = -6.45

COL_X = (-2.55, 3.55)
CELL_Y = (0.95, -1.45)
CELL_W, CELL_H = 3.90, 1.86
ROW_LABEL_X = -6.55
GRID_BAND = [0.50, 3.15, 0.0]
GATE_Y = -3.05
GATE_W, GATE_H = 4.05, 0.74

AX_ORIGIN = [-5.00, -2.60, 0.0]
AX_X_MAX, AX_Y_MAX = 70.0, 20.0
AX_X_LEN, AX_Y_LEN = 10.20, 5.00

CHAIN_X = (-5.52, -2.76, 0.0, 2.76, 5.52)
CHAIN_W, CHAIN_H = 2.42, 1.94
CHAIN_Y = 0.10

# ndc has a vertical asymptote at zero per cent, so the curve is only plotted
# where it is on the board. Computed, not eyeballed: below this ratio ndc leaves
# the top of the axis.
NDC_PLOT_LEFT = study_ratio_for_ndc(AX_Y_MAX)

if not NDC_IS_REDUNDANT:
    raise AssertionError(
        "ndc no longer recovers from the study ratio alone; B6 has no claim")
if action_for_ratio(round(STUDY_PCT_AT_NDC5, PRINTED_DP)) != ACTIONS[1]:
    raise AssertionError(
        f"the ndc crossing at {STUDY_PCT_AT_NDC5:.1f} % no longer lands in the "
        f"middle band, so B6 cannot earn {ACTIONS[1]!r} without a third colour")
if not NDC_PLOT_LEFT < min(PRINTED[0][0], PRINTED[1][0]):
    raise AssertionError("a factory point sits above the top of the ndc axis")
if not ACCEPT_PCT > NDC_PLOT_LEFT:
    raise AssertionError("the accept gate falls outside the plotted curve")


def fits(mob, what: str):
    """`within_frame` plus the edge it does not check.

    `act_style.within_frame` guards the left and right margins, which is what
    every other act needs. This one stacks two full factories vertically and puts
    a gate strip under the second, so the horizontal edges are the ones a bad
    layout runs off. A clipped label fails the render here instead of shipping.
    """
    within_frame(mob, what)
    top, bottom = float(mob.get_top()[1]), float(mob.get_bottom()[1])
    if top > FRAME_TOP - EDGE_MARGIN:
        raise ValueError(
            f"{what} overflows the top of the frame: {top:.2f} > "
            f"{FRAME_TOP - EDGE_MARGIN:.2f}. Move it inboard.")
    if bottom < FRAME_BOTTOM + EDGE_MARGIN:
        raise ValueError(
            f"{what} overflows the bottom of the frame: {bottom:.2f} < "
            f"{FRAME_BOTTOM + EDGE_MARGIN:.2f}. Move it inboard.")
    return mob


def _span(xa: float, xb: float, y: float, colour: str, sw: float = 2.2,
          end_h: float = 0.15) -> VGroup:
    """A length with both ends marked. A denominator, drawn to scale."""
    return VGroup(
        Line([xa, y, 0], [xb, y, 0], stroke_color=colour, stroke_width=sw),
        *[Line([x, y - end_h, 0], [x, y + end_h, 0], stroke_color=colour,
               stroke_width=sw) for x in (xa, xb)])


def _open_span(cx: float, y: float, colour: str, sw: float = 2.2) -> VGroup:
    """A length longer than the frame, cut at the margin with an open tip.

    Nothing is compressed and no break glyph is drawn: the bar is at true scale
    and simply larger than the screen, which is the honest reading of a
    denominator this generous. The tips say the length continues. Clipping is
    absolute, against the frame margin, so a bar that has been shifted off centre
    still ends where the frame does rather than past it.
    """
    grp = VGroup()
    for edge in (-CLIP_X, CLIP_X):
        seg = Line([cx, y, 0], [edge, y, 0], stroke_color=colour,
                   stroke_width=sw)
        seg.add_tip(tip_length=0.20, tip_width=0.16)
        grp.add(seg)
    return grp


def _hard_span(half: float, y: float, colour: str, sw: float = 2.2) -> VGroup:
    """A drawing band: the same kind of length, with hard limits at its ends.

    The two denominators are told apart by their end stops rather than by colour.
    Act A used the observed/truth data pair here, but that pair's observed hex is
    the alarm colour, and Act B is the first act with `replace` on screen: a red
    denominator beside a red action would let a reviewer read the colour as the
    verdict, which the contract forbids.
    """
    return VGroup(
        Line([-half, y, 0], [half, y, 0], stroke_color=colour, stroke_width=sw),
        *[Line([x, y - 0.30, 0], [x, y + 0.30, 0], stroke_color=colour,
               stroke_width=sw + 0.5) for x in (-half, half)])


def _field(label: str, value: str, size: float = 20,
           value_colour: str = INK_BRIGHT) -> VGroup:
    """A contract field name over its value, both spelled by the module."""
    return VGroup(
        panel_label(label, 16, INK_DIM),
        gauge(value, size, value_colour),
    ).arrange(DOWN, buff=0.12, aligned_edge=LEFT)


def _two_lines(txt: str) -> str:
    """The same string over two lines, broken at the most even space.

    The contract's decision jobs are three and four words long and no chain link
    is wide enough for either on one line. Only whitespace changes: every
    character the page grades against is still here, in order.
    """
    words = txt.split()
    best = min(range(1, len(words)),
               key=lambda k: abs(len(" ".join(words[:k]))
                                 - len(" ".join(words[k:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


class Level04Case(NarratedCameraScene):
    def construct(self):
        # One home, saved once. Every zoom below ends in Restore, so the frame
        # this act finishes on is the frame it started on.
        self.camera.frame.save_state()
        self.b1_carry_in()
        self.b2_sort_what_looks_the_same()
        self.b3_judge_against_the_drawing()
        self.b4_name_the_denominator()
        self.b5_opposite_actions()
        self.b6_ndc_is_the_same_curve()
        self.b7_the_chain()

    # ------------------------------------------------------------- helpers
    def _ask(self, question: str, at) -> VGroup:
        """A prediction, on screen as a question and not only in the voice."""
        grp = VGroup(micro("predict", 16, ACCENT), prose(question, 24, INK))
        grp.arrange(DOWN, buff=0.14, aligned_edge=LEFT).move_to(at)
        return fits(grp, f"prediction {question[:24]!r}")

    def _tag_side(self, side):
        """Which side of the band its width readout rides on.

        The readout is the proof that the band never resized, so it follows the
        band into every shot rather than being re-placed by hand. Only the side
        changes, because each shot fills a different edge of it: the ruler is
        under the band in B1, the drawing runs through it in B3, and the chain
        sits below it in B7.
        """
        self.band_tag.clear_updaters()
        self.band_tag.add_updater(
            lambda m: m.next_to(self.band, side, buff=0.16))
        self.band_tag.update()

    # -------------------------------------------------------------- B1
    def b1_carry_in(self):
        """Carry-in. The band's width is measured on screen, not asserted."""
        self.band = Rectangle(width=GAUGE_W, height=BAND_H, fill_color=ACCENT,
                              fill_opacity=0.85, stroke_color=ACCENT,
                              stroke_width=2.0)
        self.band.move_to([0.0, 0.0, 0])
        self.band_tag = panel_label(f"gauge 6\u03c3   {GAUGE_UM:.1f} \u00b5m",
                                    21, ACCENT)
        self._tag_side(DOWN)

        # Act A's closing frame: the band, its readout, and the two denominator
        # names above and below it. All four are carried in; only the names go.
        carried = VGroup(
            fits(panel_label(DENOMINATORS[0], 24, INK).move_to([0.0, 1.35, 0]),
                 "carry-in study name"),
            fits(panel_label(DENOMINATORS[1], 24, INK).move_to([0.0, -1.55, 0]),
                 "carry-in tolerance name"))
        self.add(self.band, self.band_tag, carried)

        with self.say("Same gauge. Nothing has been calibrated, adjusted, or "
                      "replaced."):
            self.beat(0.7)

        rail = Line([-USABLE_X + 0.4, -0.55, 0], [USABLE_X - 0.4, -0.55, 0],
                    stroke_color=RULE_STRONG, stroke_width=1.6)
        rail_cap = fits(micro("plant rail", 16, INK_DIM)
                        .move_to([-USABLE_X + 0.4, -0.32, 0],
                                 aligned_edge=LEFT), "B1 rail caption")
        with self.say("Act A left two names under one band. Both go. The band "
                      "goes on a plant rail."):
            self._tag_side(UP)
            self.play(FadeOut(carried, shift=UP * 0.12), run_time=0.9,
                      rate_func=rf.ease_in_sine)
            self.play(Create(rail), FadeIn(rail_cap),
                      self.band.animate.move_to([0.0, -0.55 + BAND_H / 2, 0]),
                      run_time=1.3, rate_func=rf.ease_in_out_sine)

        # A ruler, so the width is measured rather than claimed in a title.
        # Ticks every two microns, laid out from the gauge's own sigma.
        y0 = -0.72
        ruler = VGroup(Line([-GAUGE_W / 2, y0, 0], [GAUGE_W / 2, y0, 0],
                            stroke_color=INK, stroke_width=1.8))
        marks = int(GAUGE_UM // 2)
        for i in range(marks + 1):
            x = (-GAUGE_UM / 2 + 2.0 * i) * SCALE
            tall = 0.22 if i % 3 == 0 else 0.12
            ruler.add(Line([x, y0, 0], [x, y0 - tall, 0], stroke_color=INK,
                           stroke_width=1.6))
        ruler.add(fits(panel_label("0", 18, INK)
                       .move_to([-GAUGE_W / 2, y0 - 0.52, 0]), "B1 ruler zero"))
        ruler.add(fits(panel_label(f"{2 * marks}", 18, INK)
                       .move_to([2.0 * marks * SCALE - GAUGE_W / 2,
                                 y0 - 0.52, 0]), "B1 ruler end"))
        ruler.add(fits(micro("microns", 16, INK_DIM)
                       .move_to([GAUGE_W / 2 + 0.34, y0 - 0.52, 0],
                                aligned_edge=LEFT), "B1 ruler unit"))

        with self.say("A ruler against it. Not a caption about the width, the "
                      "width itself."):
            self.play(Create(ruler), run_time=1.5, rate_func=rf.ease_out_sine)

        with self.say(f"Six sigma of gauge, end to end: {GAUGE_UM:.1f} microns. "
                      "It does not move again."):
            self.play(self.camera.frame.animate.scale(0.60)
                      .move_to([0.0, -0.44, 0]), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.6)

        with self.say("Two plants are about to divide by different things. This "
                      "is the thing they both divide."):
            self.play(Restore(self.camera.frame), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)
            self.play(FadeOut(VGroup(ruler, rail, rail_cap)), run_time=0.8,
                      rate_func=rf.ease_in_sine)

    # -------------------------------------------------------------- B2
    def b2_sort_what_looks_the_same(self):
        """Beat 1. The sorting plant, and an overlap made only of the band.

        Static camera on purpose: the interleaving readings are the only motion,
        so the overlap cannot be something the camera did.
        """
        self._tag_side(DOWN)
        job = fits(_field(DECIDING_FIELDS[0], DECISION_JOBS[0], 20)
                   .move_to([LABEL_X, 3.36, 0], aligned_edge=LEFT),
                   "B2 job card")

        divider = DashedLine([0.0, 2.32, 0], [0.0, -2.05, 0], dash_length=0.10,
                             stroke_color=RULE_STRONG, stroke_width=1.8)
        div_cap = fits(micro("the sorting line", 16, INK)
                       .move_to([0.20, 1.55, 0], aligned_edge=LEFT),
                       "B2 divider caption")

        truth_y, read_y = 2.05, -0.35
        truth = VGroup(*[self._mark(A_TRUTH[i], truth_y, i < A_N, INK_BRIGHT)
                         for i in range(2 * A_N)])
        reads = VGroup(*[self._mark(A_READ[i], read_y, i < A_N, ACCENT)
                         for i in range(2 * A_N)])

        t_lo, t_hi = A_TRUTH[:A_N], A_TRUTH[A_N:]
        r_lo, r_hi = A_READ[:A_N], A_READ[A_N:]
        truth_env = VGroup(
            _span(t_lo.min() * SCALE, t_lo.max() * SCALE, 2.55, INK_BRIGHT),
            _span(t_hi.min() * SCALE, t_hi.max() * SCALE, 2.55, INK_BRIGHT))
        read_env = VGroup(
            _span(r_lo.min() * SCALE, r_lo.max() * SCALE, -0.85, ACCENT),
            _span(r_hi.min() * SCALE, r_hi.max() * SCALE, -0.85, ACCENT))

        gap_cap = fits(panel_label(
            f"truth marks: a {A_TRUTH_GAP:.2f} \u00b5m gap", 19, INK_BRIGHT)
            .move_to([0.0, 2.98, 0]), "B2 truth gap")
        ov_lo, ov_hi = r_hi.min() * SCALE, r_lo.max() * SCALE
        overlap = Rectangle(width=ov_hi - ov_lo, height=1.30,
                            fill_color=ACCENT, fill_opacity=0.16,
                            stroke_color=ACCENT, stroke_width=1.4)
        overlap.move_to([0.5 * (ov_lo + ov_hi), read_y - 0.25, 0])
        ov_cap = fits(panel_label(
            f"readings: a {A_READ_OVERLAP:.2f} \u00b5m overlap", 19, ACCENT)
            .move_to([0.0, -1.40, 0]), "B2 overlap caption")

        bins = VGroup()
        for sign, name in ((-1, "bin one"), (1, "bin two")):
            box = Rectangle(width=4.10, height=0.92, stroke_color=RULE,
                            stroke_width=1.6, fill_color=PANEL,
                            fill_opacity=1.0)
            box.move_to([sign * 2.20, -2.60, 0])
            bins.add(box, fits(micro(name, 16, INK)
                               .move_to(box.get_center()), f"B2 {name}"))

        ask = self._ask("Will this gauge separate\ntwo populations sitting\n"
                        "this close together?", [4.35, 0.95, 0])

        with self.say("This plant has to put parts in the right bin, and the "
                      "parts are close together on purpose."):
            self.play(FadeIn(job, shift=RIGHT * 0.12), FadeIn(bins),
                      Create(divider), FadeIn(div_cap), run_time=1.6,
                      rate_func=rf.ease_out_sine)

        with self.say("One feature, two process families, sitting exactly one "
                      "gauge band apart."):
            self.play(self.band.animate.move_to([0.0, 0.95, 0]), run_time=1.3,
                      rate_func=rf.ease_in_out_sine)

        with self.say("Here is the truth. Every part where it really is, each on "
                      "its own side of the sorting line."):
            self.play(FadeIn(truth, lag_ratio=0.03), run_time=1.5,
                      rate_func=rf.ease_out_sine)
            self.play(Create(truth_env), FadeIn(gap_cap), run_time=1.1,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        with self.say("Now read the same parts through the band."):
            self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(LaggedStart(*[FadeIn(m, shift=DOWN * 0.20) for m in reads],
                                  lag_ratio=0.03), run_time=2.0,
                      rate_func=rf.ease_out_sine)
            self.play(Create(read_env), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        with self.say(f"The truth left a {A_TRUTH_GAP:.2f} micron gap. The "
                      f"readings overlap by {A_READ_OVERLAP:.2f}, filled and open "
                      "marks interleaved. Nothing came between the two pictures "
                      "except the band."):
            self.play(FadeIn(overlap), FadeIn(ov_cap), run_time=1.3,
                      rate_func=rf.ease_out_sine)
            self.beat(0.9)

        self.a_plant = VGroup(truth, reads, truth_env, read_env, overlap,
                              gap_cap, ov_cap, divider, div_cap)
        self.a_bins = bins
        self.a_job = job

    def _mark(self, um: float, y: float, filled: bool, colour: str):
        """One part. Family is carried by shape, so no colour reads as a verdict."""
        x = um * SCALE
        if filled:
            return Dot([x, y, 0], radius=0.078, color=colour)
        return Circle(radius=0.078, stroke_color=colour, stroke_width=2.4,
                      fill_opacity=0.0).move_to([x, y, 0])

    # -------------------------------------------------------------- B3
    def b3_judge_against_the_drawing(self):
        """Beat 2. The same band on a drawing limit, and both wrong calls."""
        with self.say("A second masked plant. The first greys out at the edge "
                      "of frame: two jobs, one instrument between them."):
            self.play(FadeOut(self.a_plant),
                      self.a_bins.animate.scale(0.40)
                      .move_to([-4.90, -3.42, 0]).set_opacity(0.28),
                      self.a_job.animate.scale(0.78).set_opacity(0.30)
                      .move_to([-2.60, -3.42, 0], aligned_edge=LEFT),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)

        job = fits(_field(DECIDING_FIELDS[0], DECISION_JOBS[1], 20)
                   .move_to([LABEL_X, 3.36, 0], aligned_edge=LEFT),
                   "B3 job card")

        rail_y = 0.10
        half = B_LIMIT * SCALE
        limit_x = half + B_SHIFT
        drawing = _hard_span(half, rail_y, INK_BRIGHT, sw=2.4)
        drawing.shift(RIGHT * B_SHIFT)
        draw_cap = fits(panel_label(f"drawing   {B_TOL:.0f} \u00b5m", 19,
                                    INK_BRIGHT)
                        .move_to([B_SHIFT, rail_y - 0.62, 0]),
                        "B3 drawing caption")
        spread = _open_span(B_SHIFT, -1.45, INK_DIM, sw=2.0)
        spread_cap = fits(panel_label(
            f"process spread   {B_SPREAD_UM:.1f} \u00b5m", 19, INK_DIM)
            .move_to([LABEL_X, -1.95, 0], aligned_edge=LEFT),
            "B3 spread caption")

        ask = self._ask("Will this gauge decide conformance here?",
                        [1.20, -2.75, 0])

        with self.say("This plant does not care which parts differ. It has to "
                      "say pass or fail against a drawing."):
            self.play(FadeIn(job, shift=RIGHT * 0.12), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(Create(drawing), FadeIn(draw_cap), run_time=1.2,
                      rate_func=rf.ease_out_sine)

        with self.say(f"The process is wide: {B_SPREAD_UM:.0f} microns against "
                      f"a drawing of {B_TOL:.0f}, and nobody is fixing that."):
            self.play(Create(spread), FadeIn(spread_cap), run_time=1.3,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)

        limit_line = DashedLine([limit_x, -0.30, 0], [limit_x, 3.05, 0],
                                dash_length=0.10, stroke_color=RULE_STRONG,
                                stroke_width=1.6)
        pairs, wrong = VGroup(), VGroup()
        for t, r in zip(B_TRUTH, B_READ):
            tx, rx = t * SCALE + B_SHIFT, r * SCALE + B_SHIFT
            link = Line([tx, 2.60, 0], [rx, 1.20, 0], stroke_color=RULE_STRONG,
                        stroke_width=1.4)
            pairs.add(link, Dot([tx, 2.60, 0], radius=0.076, color=INK_BRIGHT),
                      Dot([rx, 1.20, 0], radius=0.076, color=ACCENT))
            if (t < B_LIMIT) != (r < B_LIMIT):
                link.set_stroke(ACCENT, width=2.6)
                wrong.add(link)
        t_cap = fits(micro("where the part is", 16, INK_BRIGHT)
                     .move_to([LABEL_X, 2.60, 0], aligned_edge=LEFT),
                     "B3 truth caption")
        r_cap = fits(micro("what the gauge said", 16, ACCENT)
                     .move_to([LABEL_X, 1.20, 0], aligned_edge=LEFT),
                     "B3 reading caption")

        with self.say("Lay the same band on the upper limit. Same object, same "
                      "width. Every part under it can be called either way."):
            self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(self.band.animate.move_to([limit_x, rail_y, 0]),
                      run_time=1.5, rate_func=rf.ease_in_out_sine)
            self.bring_to_front(drawing)
            self.play(Create(limit_line), FadeIn(t_cap), FadeIn(r_cap),
                      run_time=0.9, rate_func=rf.ease_out_sine)
            self.play(LaggedStart(*[FadeIn(p) for p in pairs], lag_ratio=0.05),
                      run_time=1.8, rate_func=rf.ease_out_sine)

        n_out = int(np.sum((B_TRUTH < B_LIMIT) & (B_READ > B_LIMIT)))
        n_in = int(np.sum((B_TRUTH > B_LIMIT) & (B_READ < B_LIMIT)))
        with self.say(f"{n_out} good parts read as scrap. {n_in} bad parts read "
                      "as good. From the band that could not sort next door."):
            self.play(self.camera.frame.animate.scale(0.46)
                      .move_to([limit_x - 0.35, 1.25, 0]), run_time=1.8,
                      rate_func=rf.ease_in_out_sine)
            self.play(Indicate(wrong, color=ACCENT, scale_factor=1.0),
                      run_time=1.3)

        with self.say("Same width, a different kind of mistake, and still no "
                      "percentage."):
            self.play(Restore(self.camera.frame), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)

        self.b_plant = VGroup(pairs, drawing, draw_cap, spread, spread_cap,
                              t_cap, r_cap, limit_line)
        self.b_job = job

    # -------------------------------------------------------------- B4
    def b4_name_the_denominator(self):
        """Beat 3. The denominator, named before any percentage exists."""
        with self.say("Both plants in one frame, so the choice is made side by "
                      "side."):
            self.play(FadeOut(VGroup(self.b_plant, self.a_bins)),
                      FadeOut(self.a_job), FadeOut(self.b_job),
                      run_time=1.1, rate_func=rf.ease_in_sine)

        self._tag_side(UP)
        self.band_b = self.band.copy()
        rows, self.slots, self.cands = VGroup(), [], []
        for r in range(2):
            y = ROW_Y[r]
            row = VGroup(
                fits(_field(DECIDING_FIELDS[0], DECISION_JOBS[r], 19)
                     .move_to([LABEL_X, y + D_BAND, 0], aligned_edge=LEFT),
                     f"B4 row {r} job"),
                Line([-SLOT_HALF, y + D_RULE, 0], [SLOT_HALF, y + D_RULE, 0],
                     stroke_color=INK, stroke_width=2.4))
            slot = DashedLine([-SLOT_HALF, y + D_SLOT, 0],
                              [SLOT_HALF, y + D_SLOT, 0], dash_length=0.11,
                              stroke_color=RULE_STRONG, stroke_width=1.8)
            row.add(slot)
            self.slots.append(slot)
            rows.add(row)
        self.b4_rows = rows
        self.b4_divider = Line([FRAME_LEFT + 0.5, -0.12, 0],
                               [FRAME_RIGHT - 0.5, -0.12, 0],
                               stroke_color=RULE, stroke_width=1.2)

        with self.say("One band each. The second is a copy sliding out of the "
                      "first, so the widths are identical by construction."):
            self.play(self.band.animate.move_to([0.0, ROW_Y[0] + D_BAND, 0]),
                      run_time=1.0, rate_func=rf.ease_in_out_sine)
            self.add(self.band_b)
            self.play(self.band_b.animate.move_to([0.0, ROW_Y[1] + D_BAND, 0]),
                      run_time=1.4, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(rows), FadeIn(self.b4_divider), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        ask = self._ask("Which length goes under each band?", [0.0, -0.12, 0])
        ask.set_z_index(3)
        with self.say("Before a percentage exists, say what you are dividing by."):
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.beat(0.7)
        self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)

        for r in range(2):
            y, pair = ROW_Y[r], []
            for c in range(2):
                length, um = DENOM_LEN[r][c], DENOM_UM[r][c]
                yc = y + D_CAND[c]
                if 0.5 * length <= CLIP_X:
                    bar = (_span(-0.5 * length, 0.5 * length, yc, INK_BRIGHT)
                           if c == 0 else _hard_span(0.5 * length, yc,
                                                     INK_BRIGHT))
                    tail = ""
                else:
                    bar = _open_span(0.0, yc, INK_BRIGHT)
                    tail = "   runs past the frame"
                lab = fits(panel_label(
                    f"{DENOMINATORS[c]}   {um:.1f} \u00b5m{tail}", 17,
                    INK_BRIGHT).move_to([LABEL_X, yc + D_CAND_LABEL, 0],
                                        aligned_edge=LEFT),
                    f"B4 row {r} candidate {c}")
                pair.append(VGroup(bar, lab))
            self.cands.append(pair)

        with self.say("Two candidates per plant: how much its parts differ, and "
                      "how much room its drawing gives."):
            self.play(FadeIn(self.cands[0][0]), FadeIn(self.cands[0][1]),
                      run_time=1.2, rate_func=rf.ease_out_sine)
            self.play(FadeIn(self.cands[1][0]), FadeIn(self.cands[1][1]),
                      run_time=1.2, rate_func=rf.ease_out_sine)

        # The counterexample: a legal move that answers an unasked question. The
        # fraction forms and no value appears, because beat 3 owns the
        # denominator and beat 4 owns the first percentage in the act.
        ghost = self.cands[0][1][0].copy().set_stroke(opacity=0.55)
        note = fits(prose("a legal move, answering a question\n"
                          "this plant never asked", 22, INK)
                    .move_to([3.45, ROW_Y[0] + D_BAND, 0]),
                    "B4 counterexample note")
        with self.say("Drop the drawing under the sorting plant. A legal move, "
                      "answering a question nobody there asked."):
            self.add(ghost)
            self.play(ghost.animate.shift(UP * (D_SLOT - D_CAND[1])),
                      FadeIn(note, shift=LEFT * 0.12), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.6)
            self.play(FadeOut(ghost), FadeOut(note), run_time=0.7,
                      rate_func=rf.ease_in_sine)

        picks, cards = [], VGroup()
        for r in range(2):
            name = denominator_for_job(DECISION_JOBS[r])
            picks.append(DENOMINATORS.index(name))
            cards.add(fits(_field(DECIDING_FIELDS[1], name, 20)
                           .move_to([2.45, ROW_Y[r] + D_BAND, 0],
                                    aligned_edge=LEFT), f"B4 row {r} chosen"))
        self.b4_cards, self.b4_picks = cards, picks

        with self.say("The numerators are identical, so this is not a fact "
                      "about the gauge. The job picks: sorting divides by the "
                      "study, conformance by the drawing."):
            self.play(Indicate(VGroup(self.band, self.band_b), color=ACCENT,
                               scale_factor=1.0), run_time=1.3)
            self.play(*[self.cands[r][picks[r]][0].animate
                        .shift(UP * (D_SLOT - D_CAND[picks[r]]))
                        for r in range(2)],
                      *[FadeOut(self.cands[r][picks[r]][1])
                        for r in range(2)],
                      *[FadeOut(self.cands[r][1 - picks[r]]) for r in range(2)],
                      *[FadeOut(self.slots[r]) for r in range(2)],
                      run_time=1.6, rate_func=rf.ease_in_out_sine)
            self.play(FadeIn(cards, shift=LEFT * 0.12), run_time=1.0,
                      rate_func=rf.ease_out_sine)

        with self.say("Both fractions are complete, and there is still no "
                      "percentage on this screen."):
            self.beat(0.7)

    # -------------------------------------------------------------- B5
    def b5_opposite_actions(self):
        """Beat 4. Four ratios, one shared numerator, and the flip."""
        leaving = VGroup(self.b4_rows, self.b4_cards, self.b4_divider,
                         *[self.cands[r][self.b4_picks[r]] for r in range(2)])
        with self.say("Two plants, two jobs. Four questions, and the other two "
                      "are the interesting ones."):
            self.play(FadeOut(leaving), FadeOut(self.band_b), run_time=1.1,
                      rate_func=rf.ease_in_sine)
            self.play(self.band.animate.move_to(GRID_BAND),
                      self.camera.frame.animate.scale(1.08), run_time=1.5,
                      rate_func=rf.ease_in_out_sine)

        heads = VGroup(*[fits(gauge(DECISION_JOBS[c], 18, INK_BRIGHT)
                              .move_to([COL_X[c], 2.32, 0]), f"B5 column {c}")
                         for c in range(2)])
        rows = VGroup(*[fits(panel_label(f"Factory {'AB'[r]}", 19, INK)
                             .move_to([ROW_LABEL_X, CELL_Y[r], 0],
                                      aligned_edge=LEFT), f"B5 row {r}")
                        for r in range(2)])

        boxes, links = VGroup(), VGroup()
        for r in range(2):
            for c in range(2):
                box = Rectangle(width=CELL_W, height=CELL_H,
                                stroke_color=RULE_STRONG if r == c else RULE,
                                stroke_width=1.8, fill_color=PANEL,
                                fill_opacity=1.0)
                box.move_to([COL_X[c], CELL_Y[r], 0])
                boxes.add(box)
                # The feed runs band to top cell to bottom cell rather than four
                # rays from the band: four rays cross the cells they do not feed,
                # and a line through a cell it has nothing to do with reads as a
                # claim about that cell.
                if r == 0:
                    start = [GRID_BAND[0] + (0.9 if c else -0.9),
                             GRID_BAND[1] - BAND_H / 2, 0]
                else:
                    start = [COL_X[c], CELL_Y[0] - CELL_H / 2, 0]
                links.add(Line(start, box.get_top(), stroke_color=ACCENT,
                               stroke_width=1.4).set_stroke(opacity=0.55))

        ask = self._ask("Which cells earn use, and which earn replace?",
                        [0.50, GATE_Y, 0])
        with self.say("One band, feeding four cells. Rows are the plants, "
                      "columns the jobs. Which cells earn use, and which earn "
                      "replace?"):
            self.play(FadeIn(heads), FadeIn(rows), run_time=0.9,
                      rate_func=rf.ease_out_sine)
            self.play(Create(boxes), Create(links), run_time=1.5,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.beat(0.9)
        self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)

        cells = {}
        for r in range(2):
            for c in range(2):
                pct, act = PRINTED[r][c], CELL_ACTIONS[r][c]
                colour = (SIGNAL_OK if act == ACTIONS[0]
                          else SIGNAL_ALARM if act == ACTIONS[2] else INK)
                grp = VGroup(panel_label(DENOMINATORS[c], 16, INK_DIM),
                             gauge(f"{pct:.{PRINTED_DP}f} %", 32, INK_BRIGHT),
                             gauge(act, 22, colour)).arrange(DOWN, buff=0.13)
                grp.move_to([COL_X[c], CELL_Y[r], 0])
                cells[(r, c)] = fits(grp, f"B5 cell {r},{c}")

        with self.say("The cells each plant asked for, on the diagonal. Both "
                      "asked the question their gauge is worst at, so both read "
                      "replace."):
            self.play(FadeIn(cells[(0, 0)]), FadeIn(cells[(1, 1)]),
                      run_time=1.3, rate_func=rf.ease_out_sine)
            self.beat(0.6)

        with self.say("Now the cells nobody asked for. Same band, same gates, "
                      "different question."):
            self.play(FadeIn(cells[(0, 1)]), FadeIn(cells[(1, 0)]),
                      run_time=1.3, rate_func=rf.ease_out_sine)

        for c in range(2):
            hl = VGroup(*[Rectangle(width=CELL_W + 0.16, height=CELL_H + 0.16,
                                    stroke_color=ACCENT, stroke_width=2.4,
                                    fill_opacity=0.0)
                          .move_to([COL_X[c], CELL_Y[r], 0]) for r in range(2)])
            top, bot = CELL_ACTIONS[0][c], CELL_ACTIONS[1][c]
            with self.say(f"Hold the job still, move the gauge between plants. "
                          f"{DECISION_JOBS[c].capitalize()}: {top}, then {bot}. "
                          f"Nothing else moved."):
                self.play(Create(hl), run_time=0.8, rate_func=rf.ease_out_sine)
                self.beat(0.6)
                self.play(FadeOut(hl), run_time=0.4, rate_func=rf.ease_in_sine)

        tiles = VGroup()
        for i, (lab, act) in enumerate(zip(BAND_LABELS, ACTIONS)):
            colour = SIGNAL_OK if i == 0 else SIGNAL_ALARM if i == 2 else INK
            tile = Rectangle(width=GATE_W, height=GATE_H, stroke_color=colour,
                             stroke_width=1.8, fill_color=colour,
                             fill_opacity=0.0 if i == 1 else 0.14)
            tile.move_to([0.50 + (i - 1) * (GATE_W + 0.12), GATE_Y, 0])
            text = VGroup(panel_label(lab, 18, INK_BRIGHT),
                          gauge(act, 18, colour)).arrange(RIGHT, buff=0.42)
            text.move_to(tile.get_center())
            tiles.add(tile, fits(text, f"B5 gate tile {lab!r}"))

        with self.say("Both of these are honest. They are answers to different "
                      "questions."):
            self.play(FadeIn(tiles), run_time=1.3, rate_func=rf.ease_out_sine)

        with self.say("The middle band is still empty and still uncoloured. "
                      "Improve is a next action, not a third verdict."):
            self.play(Restore(self.camera.frame), run_time=1.6,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.6)

        self.b5_board = VGroup(heads, rows, boxes, links, tiles,
                               *cells.values())

    # -------------------------------------------------------------- B6
    def b6_ndc_is_the_same_curve(self):
        """Beat 5. One curve, both factory points, all three printed gates."""
        with self.say("A second number is printed in the same table."):
            self.play(FadeOut(self.b5_board), run_time=1.1,
                      rate_func=rf.ease_in_sine)
            self._tag_side(UP)
            self.play(self.band.animate.move_to(PARK), run_time=1.1,
                      rate_func=rf.ease_in_out_sine)

        axes = Axes(x_range=[0, AX_X_MAX, 10], y_range=[0, AX_Y_MAX, 5],
                    x_length=AX_X_LEN, y_length=AX_Y_LEN, tips=False,
                    axis_config={"stroke_color": RULE_STRONG,
                                 "stroke_width": 1.6, "include_ticks": True,
                                 "tick_size": 0.06})
        axes.shift(np.array(AX_ORIGIN) - axes.c2p(0, 0))
        xl = fits(panel_label("%GRR_study", 20, INK)
                  .move_to([AX_ORIGIN[0] + AX_X_LEN, AX_ORIGIN[1] - 0.44, 0],
                           aligned_edge=RIGHT), "B6 x label")
        yl = fits(panel_label("ndc", 20, INK)
                  .move_to([AX_ORIGIN[0] - 0.10,
                            AX_ORIGIN[1] + AX_Y_LEN + 0.26, 0],
                           aligned_edge=LEFT), "B6 y label")
        ask = self._ask("Can ndc and %GRR_study ever disagree\n"
                        "about the same gauge?", [-1.05, -3.15, 0])

        with self.say("Number of distinct categories: how many groups of parts "
                      "this gauge can tell apart."):
            self.play(Create(axes), FadeIn(xl), FadeIn(yl), run_time=1.5,
                      rate_func=rf.ease_out_sine)
            self.play(FadeIn(ask, shift=UP * 0.10), run_time=0.8,
                      rate_func=rf.ease_out_sine)
            self.beat(0.6)

        curve = axes.plot(ndc_from_study_ratio,
                          x_range=[NDC_PLOT_LEFT, AX_X_MAX, 0.25],
                          stroke_color=ACCENT, stroke_width=3.0)
        with self.say("One curve. Every ndc a gauge can have against the study "
                      "ratio it came from, falling the whole way."):
            self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)
            self.play(Create(curve), run_time=2.0, rate_func=rf.ease_in_out_sine)

        dots, dot_caps = VGroup(), VGroup()
        for r, part in enumerate((A_PART, B_PART)):
            long_way = ndc(GAUGE_SIGMA, part)
            pt = axes.c2p(RATIOS[r][0], long_way)
            dots.add(Dot(pt, radius=0.085, color=INK_BRIGHT))
            cap = panel_label(f"Factory {'AB'[r]}   ndc {long_way:.2f}", 18,
                              INK_BRIGHT)
            cap.next_to(pt, RIGHT if r == 1 else UP, buff=0.18)
            dot_caps.add(fits(cap, f"B6 factory {r} caption"))
        residual = max(abs(ndc(GAUGE_SIGMA, p) - ndc_from_study_ratio(
            study_ratio(GAUGE_SIGMA, p))) for p in (A_PART, B_PART))

        with self.say(f"Both plants, computed the long way from the gauge and "
                      f"the parts, land on it. Not near it: the two routes "
                      f"differ by under {residual:.0e}. The only thing ndc adds "
                      f"is the constant {NDC_K}."):
            self.play(FadeIn(dots, scale=1.6), FadeIn(dot_caps), run_time=1.4,
                      rate_func=rf.ease_out_sine)
            self.beat(1.0)

        gate_v = VGroup()
        for pct in (ACCEPT_PCT, REJECT_PCT):
            gate_v.add(DashedLine(axes.c2p(pct, 0), axes.c2p(pct, AX_Y_MAX),
                                  dash_length=0.10, stroke_color=INK_DIM,
                                  stroke_width=2.0))
            gate_v.add(fits(panel_label(f"{pct:.0f} %", 18, INK_DIM)
                            .next_to(axes.c2p(pct, AX_Y_MAX), UP, buff=0.10),
                            f"B6 gate {pct:.0f}"))
        gate_h = DashedLine(axes.c2p(0, NDC_MIN), axes.c2p(AX_X_MAX, NDC_MIN),
                            dash_length=0.10, stroke_color=INK_DIM,
                            stroke_width=2.0)
        gate_h_lab = fits(panel_label(f"ndc {NDC_MIN}", 18, INK_DIM)
                          .next_to(axes.c2p(AX_X_MAX, NDC_MIN), UP, buff=0.10)
                          .shift(LEFT * 0.30), "B6 ndc gate label")

        x_ndc = STUDY_PCT_AT_NDC5
        cross = VGroup(
            Dot(axes.c2p(x_ndc, NDC_MIN), radius=0.075, color=ACCENT),
            Dot(axes.c2p(REJECT_PCT, ndc_from_study_ratio(REJECT_PCT)),
                radius=0.075, color=ACCENT))

        with self.say("Now the printed gates: ten per cent, thirty per cent, "
                      "five categories. All three come off the same table, and "
                      "the last two miss each other."):
            self.play(Create(gate_v), Create(gate_h), FadeIn(gate_h_lab),
                      run_time=1.6, rate_func=rf.ease_out_sine)
            self.play(FadeIn(cross, scale=1.6), FadeOut(dot_caps), run_time=0.9,
                      rate_func=rf.ease_out_sine)

        base_y = float(axes.c2p(0, NDC_MIN)[1])
        gap_span = _span(float(axes.c2p(x_ndc, NDC_MIN)[0]),
                         float(axes.c2p(REJECT_PCT, NDC_MIN)[0]),
                         base_y - 0.34, ACCENT, sw=1.4, end_h=0.06)
        gap_lab = panel_label(f"{NDC_GATE_GAP:.2f} points", 8, ACCENT)
        gap_lab.next_to(gap_span, DOWN, buff=0.06)
        tile = Rectangle(width=1.15, height=0.32, stroke_color=INK,
                         stroke_width=1.0, fill_opacity=0.0)
        tile.move_to([float(axes.c2p(x_ndc, NDC_MIN)[0]) - 0.90,
                      base_y + 0.62, 0])
        tile_lab = gauge(ACTIONS[1], 8, INK).move_to(tile.get_center())

        with self.say(f"{NDC_GATE_GAP:.2f} points apart. The ndc rule bites "
                      f"first, at {STUDY_PCT_AT_NDC5:.1f} per cent, inside the "
                      f"middle band where the action reads {ACTIONS[1]} in plain "
                      f"ink."):
            self.play(self.camera.frame.animate.scale(0.40)
                      .move_to([float(axes.c2p(0.5 * (x_ndc + REJECT_PCT),
                                               NDC_MIN)[0]), base_y - 0.30, 0]),
                      run_time=2.0, rate_func=rf.ease_in_out_sine)
            self.play(Create(gap_span), FadeIn(gap_lab), Create(tile),
                      FadeIn(tile_lab), run_time=1.2,
                      rate_func=rf.ease_out_sine)
            self.beat(0.6)

        with self.say("One of these two printed rules is stricter than the "
                      "other, and the table they share does not say so."):
            self.play(Restore(self.camera.frame), run_time=2.0,
                      rate_func=rf.ease_in_out_sine)
            self.beat(0.6)

        self.b6_board = VGroup(axes, xl, yl, curve, dots, gate_v, gate_h,
                               gate_h_lab, cross, gap_span, gap_lab, tile,
                               tile_lab)

    # -------------------------------------------------------------- B7
    def b7_the_chain(self):
        """Beat 6. Five links, and only the first of them is a decision."""
        with self.say("Everything this act built, in order, for one plant. "
                      "Which link is the only choice a person makes?"):
            self.play(FadeOut(self.b6_board), run_time=1.1,
                      rate_func=rf.ease_in_sine)
            self.play(self.band.animate.move_to([0.0, 2.90, 0]), run_time=1.0,
                      rate_func=rf.ease_in_out_sine)
            band_cap = fits(micro("not one of these links", 16, ACCENT)
                            .move_to([0.0, 2.24, 0]), "B7 band caption")
            ask = self._ask("Which link is the only place\n"
                            "a person makes a choice?", [0.0, -2.30, 0])
            self.play(FadeIn(band_cap), FadeIn(ask, shift=UP * 0.10),
                      run_time=0.9, rate_func=rf.ease_out_sine)
            self.beat(0.9)
        self.play(FadeOut(ask), run_time=0.4, rate_func=rf.ease_in_sine)

        job = DECISION_JOBS[0]
        links, arrows, self.b7_values = VGroup(), VGroup(), []
        # Each link starts where its content was earned, so the assembly is a
        # recap of the act rather than five boxes appearing.
        froms = ([-5.20, 3.36, 0], [-2.00, ROW_Y[0], 0], [COL_X[0], CELL_Y[0], 0],
                 [-3.55, GATE_Y, 0], [3.55, GATE_Y, 0])
        for i, (label, value) in enumerate(zip(CHAIN_LABELS,
                                               self._chain_values(job))):
            box = Rectangle(width=CHAIN_W, height=CHAIN_H, fill_color=PANEL,
                            fill_opacity=1.0, stroke_color=RULE,
                            stroke_width=1.6)
            box.move_to([CHAIN_X[i], CHAIN_Y, 0])
            body = gauge(value, 19, INK_BRIGHT)
            stack = VGroup(panel_label(label, 14, ACCENT), body)
            stack.arrange(DOWN, buff=0.24).move_to(box.get_center())
            link = VGroup(box, stack)
            fits(link, f"B7 link {label!r}")
            link.save_state()
            link.move_to(froms[i]).scale(0.55).set_opacity(0.0)
            links.add(link)
            self.b7_values.append(body)
            if i:
                arrows.add(Line([CHAIN_X[i - 1] + CHAIN_W / 2 + 0.02, CHAIN_Y, 0],
                                [CHAIN_X[i] - CHAIN_W / 2 - 0.02, CHAIN_Y, 0],
                                stroke_color=RULE_STRONG, stroke_width=1.6))
        self.b7_links, self.b7_arrows = links, arrows

        with self.say("They fly in from where they were earned: the job from "
                      "the plants, the denominator from the fractions, the rest "
                      "from the grid and the gates."):
            self.play(LaggedStart(*[Restore(link) for link in links],
                                  lag_ratio=0.42), run_time=3.2,
                      rate_func=rf.ease_out_sine)
            self.play(Create(arrows), run_time=0.9, rate_func=rf.ease_out_sine)

        with self.say("Only the first link was a decision. The rest is "
                      "arithmetic and a lookup, and the band never joins in."):
            self.play(Indicate(links[0], color=ACCENT, scale_factor=1.03),
                      run_time=1.5)

        with self.say("Swap the job token, and touch nothing else on the screen."):
            self.play(*self._retarget(self._chain_values(DECISION_JOBS[1])),
                      run_time=1.8, rate_func=rf.ease_in_out_sine)
            self.beat(0.6)

        with self.say("Same plant, same parts, same band. One word at the "
                      "front, and the last four links moved. Put it back."):
            self.beat(1.0)
            self.play(*self._retarget(self._chain_values(job)), run_time=1.4,
                      rate_func=rf.ease_in_out_sine)

        claim = fits(prose("the gauge does not own a verdict", 30, INK_BRIGHT)
                     .move_to([0.0, -2.40, 0]), "B7 claim")
        with self.say("The gauge does not own a verdict. The job chooses the "
                      "denominator, and the denominator carries the rest."):
            self.play(FadeIn(claim, shift=UP * 0.12), run_time=1.3,
                      rate_func=rf.ease_out_sine)
            self.play(Restore(self.camera.frame), run_time=1.2,
                      rate_func=rf.ease_in_out_sine)
            self.beat(1.2)

    def _retarget(self, values):
        """Transforms that rewrite the chain's five values where they stand."""
        out = []
        for held, value in zip(self.b7_values, values):
            new = gauge(value, 19, INK_BRIGHT).move_to(held.get_center())
            out.append(Transform(held, new))
        return out

    def _chain_values(self, job: str) -> tuple[str, ...]:
        """The five link values for one plant, computed from the job alone.

        Factory A's parts and drawing stay fixed. Only the job moves, which is
        the shot's whole gesture: the denominator, the percentage, the band and
        the action are all downstream of it.
        """
        name = denominator_for_job(job)
        pct = PRINTED[0][DENOMINATORS.index(name)]
        return (_two_lines(job), name, f"{pct:.{PRINTED_DP}f} %",
                band_label_for_ratio(pct), action_for_ratio(pct))
