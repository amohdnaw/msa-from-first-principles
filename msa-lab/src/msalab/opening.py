"""The plain-language opening every act begins with.

Contracted in `specs/act-opening-contract.md` after Ammar watched all seven acts:
the animation assumed you already knew the words. So each act now opens on a
concrete thing and a growing record, in ordinary language, and hands off to the
material that was already there.

Direction C with Direction A's graft, from
`diagrams/act-opening-mock-pick.png`:

    left panel    the thing              a rectangle, and jaws that close on it
    right panel   the record             a strip the readings land on
    the handoff   the left panel fades   and the right panel already IS the
                                         first figure of the act

Three rules this module enforces mechanically, so seven openings cannot drift:

1. **Plain words only.** `plain()` refuses Greek, refuses a lone Latin variable,
   and refuses a small ban list of terms the openings exist to postpone. The
   term is earned in the act, not assumed in the first ten seconds.
2. **Primitives only.** Rectangles, lines, arcs and dots. No illustration, per
   `DESIGN.md`'s ban list.
3. **One geometry.** The record strip is built from the *same* x-range the act's
   part 1 uses, so the handoff is a fade rather than a cut, and the dots the
   reader watched land are the dots part 1 then counts.
"""
from __future__ import annotations

import re

from manim import (
    Dot, FadeIn, FadeOut, Line, Rectangle, VGroup,
    rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
)

from msalab.act_style import (
    ACCENT, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM, RULE, RULE_STRONG,
    SIGNAL_ALARM, SIGNAL_OK, panel_label, prose, within_frame,
)

#: Where the divider between the two panels sits, in scene units.
DIVIDER_X = -0.35

#: The left panel's centre, and the part block's size.
THING_CENTRE = LEFT * 3.9
PART_W, PART_H = 2.0, 0.95

#: Terms an opening may not put on screen. Not a style preference: the whole
#: point of the opening is that the reader has not met these yet. `sigma` and
#: `mu` are here as words, and Greek is caught by the regex below.
POSTPONED = (
    "repeatability", "reproducibility", "variance", "distribution",
    "standard deviation", "sigma", "histogram", "interaction", "kappa",
    "bias", "linearity", "capability", "tolerance", "appraiser",
    "nominal", "quadrature", "estimator", "confidence",
)

#: Greek, or a bare single-letter variable. Same test `act_style` uses for its
#: uppercase rule, reused here for a different reason.
_SYMBOLIC = re.compile(r"[\u0370-\u03ff]|(?<![A-Za-z])[a-z](?![A-Za-z])")


def plain(txt: str, size: float = 27, color: str = INK) -> "Text":
    """Prose for an opening, checked for words the reader has not met.

    Raises rather than warns. A warning in a render log is a warning nobody
    reads; the openings exist precisely to keep these words off the screen, so
    breaking that has to stop the build.
    """
    low = txt.lower()
    hits = [w for w in POSTPONED if w in low]
    if hits:
        raise ValueError(
            f"opening text uses a postponed term {hits!r}: {txt!r}. "
            f"The opening is the part that does not assume the vocabulary - "
            f"say it in ordinary words, or move the line into the act."
        )
    if _SYMBOLIC.search(txt):
        raise ValueError(
            f"opening text carries a symbol or a bare variable: {txt!r}. "
            f"Greek and single letters are earned later in the act."
        )
    return prose(txt, size, color)


# --------------------------------------------------------------- the two panels
def two_panel(left: str, right: str, top: float = 2.55,
              bottom: float = -1.65) -> dict:
    """The divider and the two panel headings.

    Returned as a dict rather than a VGroup because the caller needs to fade the
    left heading independently at the handoff, and reaching into a group by
    index is how that becomes wrong six acts later.
    """
    rule = Line([DIVIDER_X, top, 0], [DIVIDER_X, bottom, 0],
                stroke_color=RULE, stroke_width=1.2)
    lh = within_frame(
        panel_label(left, 18, INK_DIM).move_to([DIVIDER_X - 3.6, top - 0.3, 0]),
        "opening left heading")
    rh = within_frame(
        panel_label(right, 18, INK_DIM).move_to([DIVIDER_X + 1.4, top - 0.3, 0]),
        "opening right heading")
    return {"rule": rule, "left_heading": lh, "right_heading": rh,
            "all": VGroup(rule, lh, rh)}


def part_block(centre=None, w: float = PART_W, h: float = PART_H,
               color: str = INK) -> Rectangle:
    """The thing being measured. A rectangle, deliberately."""
    r = Rectangle(width=w, height=h, fill_color="#1b2026", fill_opacity=1.0,
                  stroke_color=color, stroke_width=2.0)
    r.move_to(THING_CENTRE if centre is None else centre)
    return r


def gauge_jaws(target: Rectangle, open_by: float = 1.30,
               color: str = ACCENT) -> VGroup:
    """Direction A's graft: two jaws that close onto the block.

    Built as two L-shaped polylines from `Line` segments rather than a `Polygon`,
    so they can be animated apart and together without the fill flickering.
    """
    edge_l = target.get_left()[0]
    edge_r = target.get_right()[0]
    left_x = edge_l - open_by
    right_x = edge_r + open_by
    top_y = target.get_top()[1] + 1.15
    mid_y = target.get_center()[1]

    def jaw(x, face_x):
        # The foot ends AT the block's face, never across it. A fixed reach drew
        # a line over the part and the whole thing read as a bracket with the
        # part sitting inside it, rather than two jaws closing on it.
        return VGroup(
            Line([x, top_y, 0], [x, mid_y, 0], stroke_color=color,
                 stroke_width=2.4),
            Line([x, mid_y, 0], [face_x, mid_y, 0], stroke_color=color,
                 stroke_width=2.4),
        )

    return VGroup(jaw(left_x, edge_l), jaw(right_x, edge_r))


def closed_jaws(target: Rectangle, **kw) -> VGroup:
    """Where the jaws end up: touching the block on both sides."""
    return gauge_jaws(target, open_by=0.02, **kw)


def thing_caption(txt: str, target: Rectangle) -> "Text":
    """Names the thing in ordinary words, under it.

    The left panel is otherwise mostly air, and the ask was for deeper visuals,
    not emptier ones.
    """
    return within_frame(
        plain(txt, 22, INK_DIM).next_to(target, DOWN, buff=0.52),
        "opening thing caption")


# ------------------------------------------------------------- the record strip
def record_strip(x_lo: float, x_hi: float, label: str, y: float = 0.15,
                 left: float = 0.35, right: float = 6.4) -> dict:
    """The strip readings land on, built from the act's own x-range.

    `x_lo`/`x_hi` must be the range the act's part 1 axes use. That is what makes
    the handoff a fade: the dots sit at the same scene coordinates the histogram
    will later count them at.
    """
    line = Line([left, y, 0], [right, y, 0], stroke_color=RULE_STRONG,
                stroke_width=1.6)
    cap = within_frame(
        panel_label(label, 17, INK_DIM).move_to([(left + right) / 2, y - 0.62, 0]),
        "opening record label")

    def at(value: float):
        """Scene point for a reading, on the same scale part 1 will use."""
        t = (value - x_lo) / (x_hi - x_lo)
        return [left + t * (right - left), y, 0]

    return {"line": line, "label": cap, "at": at,
            "all": VGroup(line, cap)}


def tick(point, color: str = SIGNAL_ALARM, r: float = 0.075) -> Dot:
    """One reading, landed."""
    return Dot(point, radius=r, color=color)


def value_label(txt: str, point, color: str = INK) -> "Text":
    """The number a reading gave, under its dot. Mono, because it is a readout."""
    # above the strip: below it the caption already lives 0.62 down, and 0.46
    # put the two within 0.16 of each other
    return within_frame(
        panel_label(txt, 20, color).move_to([point[0], point[1] + 0.44, 0]),
        "opening value label")


# ------------------------------------------------------------------ the handoff
def hand_off(scene, thing_group, panels: dict, run_time: float = 1.3):
    """Fade the left half away and leave the right half standing.

    Every act calls this, so the join between the plain opening and the material
    that was already there looks the same seven times.
    """
    scene.play(
        FadeOut(thing_group, shift=LEFT * 0.35),
        FadeOut(panels["rule"]),
        FadeOut(panels["left_heading"]),
        FadeOut(panels["right_heading"]),
        run_time=run_time, rate_func=rf.ease_in_sine,
    )
