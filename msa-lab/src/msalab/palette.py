"""The one palette, imported by everything that draws.

`DESIGN.md` is the authority and this module is its executable copy. The reason
it exists as code rather than as three copies of the same hex strings: on the SPC
build the matplotlib sheets used `#0e1116` for the ground while the pages used
`#0d1114`, and the Manim scenes used a fourth set of signal colours
(`#5CD0B3`, `#FC6255`) that were close to the page tokens without matching them.
Nothing broke visibly, but a figure and the video beside it were drawn in
different greens, and the ground had a one-value seam.

So here every renderer reads the same constants:

    figure sheets   matplotlib, via `rc()` below
    the acts        Manim, via the same names
    the pages       DESIGN.md tokens, which these mirror exactly

If a colour changes, it changes in DESIGN.md and here, and every render agrees
again on the next build.
"""
from __future__ import annotations

#: Ground. The exact page background, so a figure sits on the page with no seam.
GROUND = "#0d1114"
PANEL = "#14181c"
PANEL_HIGH = "#1b2026"

#: Structure.
RULE = "#2a3138"
RULE_STRONG = "#3d4650"

#: Ink.
INK_DIM = "#7d8b98"
INK = "#d7dee4"
INK_BRIGHT = "#eef3f7"

#: Wayfinding. Never encodes data - not in a figure, not in a video, not in a
#: readout. It marks what a reader can act on.
ACCENT = "#ffae00"

#: The semantic pair. Data only.
SIGNAL_OK = "#65ccaf"
SIGNAL_ALARM = "#de6a5d"
FILL_OK = "#2a534b"

#: Level 1 needs a third *neutral* data colour, because it draws three things at
#: once: the parts (truth), the readings (observed) and the gauge's own error.
#: None of the three is a pass or a fail, so none may take the semantic pair.
#: Ink at two weights carries them, and the pair stays reserved for verdicts.
DATA_TRUTH = INK_BRIGHT
DATA_OBSERVED = SIGNAL_ALARM
DATA_GAUGE = SIGNAL_OK


def rc() -> dict:
    """matplotlib rcParams for a sheet that lands on the page seamlessly."""
    return {
        "figure.facecolor": GROUND,
        "axes.facecolor": GROUND,
        "savefig.facecolor": GROUND,
        "text.color": INK,
        "axes.edgecolor": RULE_STRONG,
        "axes.labelcolor": INK_DIM,
        "xtick.color": INK_DIM,
        "ytick.color": INK_DIM,
        "grid.color": RULE,
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlecolor": INK_BRIGHT,
    }
