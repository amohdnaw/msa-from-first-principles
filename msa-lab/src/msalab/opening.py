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
3. **One geometry.** Where the act's part 1 opens on a reading axis, the record
   strip is built from that *same* x-range, so the dots the reader watched land
   are the dots part 1 then counts.

Two handoff modes, because parts 1 do not all open on an axis:

    mode A   walk_to_axis()   levels 1, 2, 5 - part 1 opens on a reading scale,
                              so the strip moves onto it and the join is a fade
    mode B   hand_off()       levels 3, 4, 6, 7 - part 1 opens on text panels,
                              bars or a list, so the left panel leaves and the
                              record stands as the level's subject

Mode B is not a weaker join. In level 3 the opening's own two-panel split *is*
part 1's composition, and in level 4 the record is already the bars part 1 draws.
"""
from __future__ import annotations

import re

from manim import (
    Dot, FadeIn, FadeOut, Line, Rectangle, Transform, VGroup,
    rate_functions as rf,
    DOWN, LEFT, RIGHT, UP,
)

from msalab.act_style import (
    ACCENT, DATA_TRUTH, INK, INK_BRIGHT, INK_DIM, RULE, RULE_STRONG,
    SIGNAL_ALARM, SIGNAL_OK, panel_label, prose, within_frame,
)

#: Where the divider between the two panels sits, in scene units.
DIVIDER_X = -0.35

#: The panel headings sit at `top - 0.3`, i.e. 2.25 by default, and a bar
#: caption sits 0.44 above its bar. So the topmost bar in a stack must be at or
#: below this, or its own caption lands on the heading. Levels 4 and 7 both hit
#: it before this was written down.
TOP_BAR_Y = 1.55

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

#: Greek, or a bare single-letter variable.
#:
#: Borrowed from `act_style`'s uppercase rule, and it needed one change: there,
#: a lone letter is always a variable, but this module checks *English prose*,
#: where "a" is an article and "I" is a pronoun. The first version rejected
#: "a bore whose real size we know", which is as plain as a sentence gets.
_SYMBOLIC = re.compile(
    r"[\u0370-\u03ff]"                         # any Greek
    r"|(?<![A-Za-z])(?![aAiI](?![A-Za-z]))"    # not the English one-letter words
    r"[a-zA-Z](?![A-Za-z])"                    # any other lone letter
)


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

# ------------------------------------------------------------ mode A: the walk
def walk_to_axis(scene, strip: dict, dots, values, x_lo: float, x_hi: float,
                 label: str, axis_y: float, half_width: float,
                 run_time: float = 1.5):
    """Move the record onto where part 1's x-axis is about to be drawn.

    `axis_y` and `half_width` come from the act's own Axes: for
    `Axes(y_length=L).shift(DOWN*s)` the x-axis sits at `-s - L/2`, and it spans
    `+/- x_length/2` about the shift's x. Passing them in rather than guessing is
    the difference between a fade and a jump cut.
    """
    target = record_strip(x_lo, x_hi, label, y=axis_y,
                          left=-half_width, right=half_width)
    scene.play(
        Transform(strip["line"], target["line"]),
        FadeOut(strip["label"]),
        *[d.animate.move_to(target["at"](v)) for d, v in zip(dots, values)],
        run_time=run_time, rate_func=rf.ease_in_out_sine,
    )
    return target


# --------------------------------------------------- more schematic primitives
def stamp(txt: str, point, color: str = SIGNAL_OK) -> VGroup:
    """A verdict instead of a number. Level 6's record holds these.

    A boxed word, because that is what a stamp is: no scale, no position on a
    strip, nothing to subtract from anything else.
    """
    label = panel_label(txt, 22, color)
    box = Rectangle(width=label.width + 0.44, height=label.height + 0.32,
                    stroke_color=color, stroke_width=2.0, fill_opacity=0.0)
    g = VGroup(box, label)
    g.move_to(point)
    return g


def span_bar(length: float, y: float, color: str, left: float = 0.55,
             height: float = 0.34) -> Rectangle:
    """A horizontal bar standing for how wide something is.

    Levels 4 and 7 compare widths rather than positions, so their record holds
    bars where levels 1 and 5 hold dots.
    """
    r = Rectangle(width=max(0.02, length), height=height, fill_color=color,
                  fill_opacity=0.85, stroke_width=0)
    r.move_to([left + length / 2.0, y, 0])
    return r


def bar_caption(txt: str, bar: Rectangle, color: str = INK_DIM) -> "Text":
    """Names a bar, above its left end, in ordinary words.

    To the *right* of the bar was the first version, and it put the caption's
    right edge at `bar_end + caption_width` - so a longer bar pushed its own
    label off the frame and the guard rejected levels 4 and 7. Above the left end,
    the position no longer depends on the bar's length at all.
    """
    lab = plain(txt, 20, color)
    lab.move_to([bar.get_left()[0] + lab.width / 2.0,
                 bar.get_center()[1] + 0.44, 0])
    return within_frame(lab, "opening bar caption")
