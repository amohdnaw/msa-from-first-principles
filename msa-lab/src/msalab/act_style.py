"""One place for how an act looks, so seven acts cannot drift apart.

Everything here was settled in `DESIGN.md` and in the SPC craft contract; this
module is the executable form. Three rules it enforces mechanically rather than
by good intentions:

1. **Two voices.** EB Garamond claims, hypotheses and verdicts - anything you
   read. IBM Plex Mono readouts, units and quantities - anything you measure.
   Maths stays in Computer Modern via MathTex; mixing CM with Garamond prose is
   not a breach of the two-voice rule, it is the convention this curriculum
   follows, and the website serves it the same way.

2. **Case is not styling.** An uppercased label renames a variable: `n` is not
   `N`, and sigma uppercased is the summation sign. `micro()` will refuse to
   uppercase a string containing Greek or a bare single-letter Latin variable.
   On the SPC build this rule cost three separate clean-up passes because it was
   discovered late.

3. **Nothing leaves the frame.** `within_frame()` raises if a mobject runs off
   either edge. Guards that only checked the right edge shipped a label reading
   "NTERVALS THAT CAUGHT IT" on the left; both edges are checked here.

The fonts come from the repo's own woff2 via `tools/install-fonts.py`, so the
render and the browser draw identical outlines.
"""
from __future__ import annotations

import re

from manim import LEFT, Text, config

from msalab.palette import (
    ACCENT, DATA_GAUGE, DATA_OBSERVED, DATA_TRUTH, GROUND, INK, INK_BRIGHT,
    INK_DIM, PANEL, PANEL_HIGH, RULE, RULE_STRONG, SIGNAL_ALARM, SIGNAL_OK,
)

SERIF = "EB Garamond"
MONO = "IBM Plex Mono"

config.background_color = GROUND

#: Frame edges, with the margin the craft contract requires.
EDGE_MARGIN = 0.34
FRAME_RIGHT = config.frame_width / 2
FRAME_LEFT = -config.frame_width / 2

#: Greek, plus a bare single-letter Latin variable, may not be uppercased.
_CASE_CARRIES_MEANING = re.compile(r"[\u0370-\u03ff]|(?<![A-Za-z])[a-z](?![A-Za-z])")


def within_frame(mob, what: str = "label"):
    """Raise if `mob` runs off either edge. Returns `mob` so it chains."""
    left = mob.get_left()[0]
    right = mob.get_right()[0]
    if right > FRAME_RIGHT - EDGE_MARGIN:
        raise ValueError(
            f"{what} overflows the right of the frame: {right:.2f} > "
            f"{FRAME_RIGHT - EDGE_MARGIN:.2f}. Shorten it or move it inboard.")
    if left < FRAME_LEFT + EDGE_MARGIN:
        raise ValueError(
            f"{what} overflows the left of the frame: {left:.2f} < "
            f"{FRAME_LEFT + EDGE_MARGIN:.2f}. Shorten it or move it inboard.")
    return mob


def prose(txt: str, size: float = 28, color: str = INK_BRIGHT, weight="MEDIUM"):
    """A claim, a hypothesis, a verdict. Anything the viewer reads."""
    return Text(txt, font=SERIF, font_size=size, color=color, weight=weight)


def gauge(txt: str, size: float = 26, color: str = INK):
    """A readout: a quantity with its unit. Anything the viewer measures."""
    return Text(txt, font=MONO, font_size=size, color=color)


def micro(txt: str, size: float = 16, color: str = INK_DIM):
    """A small uppercase instrument label.

    Refuses to uppercase anything whose case carries meaning, because
    `text-transform: uppercase` on `sigma` or on a bare `n` silently renames the
    quantity. Pass an already-correct string if you need a symbol in a label.
    """
    if _CASE_CARRIES_MEANING.search(txt):
        raise ValueError(
            f"micro() refuses {txt!r}: it contains a symbol whose case carries "
            "meaning (Greek, or a bare single-letter variable). Use gauge() for "
            "a mixed-case instrument label instead.")
    return Text(txt.upper(), font=MONO, font_size=size, color=color)


def panel_label(txt: str, size: float = 16, color: str = INK_DIM):
    """A mono label that is allowed to keep its case, for symbol-bearing text."""
    return Text(txt, font=MONO, font_size=size, color=color)


__all__ = [
    "ACCENT", "DATA_GAUGE", "DATA_OBSERVED", "DATA_TRUTH", "EDGE_MARGIN",
    "FRAME_LEFT", "FRAME_RIGHT", "GROUND", "INK", "INK_BRIGHT", "INK_DIM",
    "MONO", "PANEL", "PANEL_HIGH", "RULE", "RULE_STRONG", "SERIF",
    "SIGNAL_ALARM", "SIGNAL_OK", "gauge", "micro", "panel_label", "prose",
    "within_frame",
]
