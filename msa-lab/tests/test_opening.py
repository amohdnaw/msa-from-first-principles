"""The plain-language openings. specs/act-opening-contract.md.

The opening exists to keep vocabulary off the screen until it has been earned,
so the load-bearing test is that the guard which enforces that actually refuses.
"""
import ast
import pathlib
import re

import pytest

from msalab.opening import POSTPONED, plain, record_strip

SRC = pathlib.Path(__file__).resolve().parents[1] / "src" / "msalab"


def _scene_files():
    return sorted(SRC.glob("level0*_scene.py"))


# ------------------------------------------------------------- the guard bites
@pytest.mark.parametrize("term", POSTPONED)
def test_the_guard_refuses_every_postponed_term(term):
    """Each word on the list has to actually stop a build. A list nothing checks
    against is a comment."""
    with pytest.raises(ValueError, match="postponed term"):
        plain(f"and then the {term} appears")


@pytest.mark.parametrize("txt", [
    "the spread is σ",
    "call the true size μ",
    "let x be the reading",
    "d2 relates the range to it",
])
def test_the_guard_refuses_symbols_and_bare_variables(txt):
    with pytest.raises(ValueError):
        plain(txt)


def test_the_guard_passes_ordinary_english():
    for txt in ("the part never moved. the numbers did.",
                "one bore, drilled once",
                "how far off it is, in microns",
                "twenty readings of the same hole"):
        assert plain(txt) is not None


def test_the_guard_is_case_insensitive():
    with pytest.raises(ValueError, match="postponed term"):
        plain("Repeatability, in plain words")


# --------------------------------------------- the opening comes first, always
def test_the_opening_runs_before_part_one():
    """Contract check 1: the first thing on screen is the two panels. If an act
    defines an opening and then calls it second, the reader still meets an axis
    first and the whole change is pointless."""
    seen = 0
    for f in _scene_files():
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.FunctionDef) and node.name == "construct"):
                continue
            calls = [n.func.attr for n in ast.walk(node)
                     if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr.startswith("part")]
            if "part0_opening" not in calls:
                continue
            seen += 1
            assert calls[0] == "part0_opening", (
                f"{f.name}: construct calls {calls[0]!r} before the opening")
    assert seen >= 1, "no act defines an opening yet"


def test_the_record_strip_maps_the_acts_own_range():
    """Contract check 6: the join is a fade because the dots sit on the scale the
    act's part 1 is about to draw. If `at()` stopped being linear in the act's
    own range, the dots would land in the wrong place and the handoff would be a
    lie told with an animation."""
    strip = record_strip(-4.2, 4.2, "how far off it is, in microns",
                         left=0.35, right=6.4)
    at = strip["at"]
    assert at(-4.2)[0] == pytest.approx(0.35, abs=1e-12)
    assert at(4.2)[0] == pytest.approx(6.4, abs=1e-12)
    assert at(0.0)[0] == pytest.approx((0.35 + 6.4) / 2, abs=1e-12)
    # linear, so a reading twice as far off lands twice as far along
    mid = at(0.0)[0]
    assert at(2.1)[0] - mid == pytest.approx((at(4.2)[0] - mid) / 2, abs=1e-12)


def test_level_one_opening_reuses_part_ones_readings():
    """The tie-in is only real if the dots are the same draws.

    Both the opening and part 1 seed `default_rng(21)` and draw
    `ONE_PART_READS` from the same sigma, so the dots the reader watches land
    are literally the first dots part 1 counts. A different seed in either place
    would make the claim false while looking identical on screen.
    """
    src = (SRC / "level01_scene.py").read_text()
    opening = src[src.index("def part0_opening"):src.index("def part1_")]
    part1 = src[src.index("def part1_"):src.index("def part2_")]
    for block, name in ((opening, "part0"), (part1, "part1")):
        assert "default_rng(21)" in block, f"{name} does not seed rng(21)"
        assert "GAUGE_SIGMA" in block, f"{name} does not draw from GAUGE_SIGMA"
        assert "ONE_PART_TRUE" in block, f"{name} does not centre on the true size"


def test_no_opening_puts_a_postponed_term_on_screen():
    """Belt to the guard's braces.

    `plain()` refuses postponed words, but an opening could reach for
    `prose`/`panel_label`/`micro`/`gauge` directly and bypass it. So walk the
    opening's AST and check the first string argument of every display call.

    An earlier version of this test grepped for quoted spans instead, which
    matched `GAUGE_SIGMA` inside ordinary code and failed on a passing build -
    a reminder that a regex over source is not a parser.
    """
    # the scene's display surface is mostly the opening helpers, not the raw
    # act_style ones - checking only the latter inspected 2 strings and the
    # vacuity assert below caught it
    display = {"plain", "prose", "panel_label", "micro", "gauge",
               "two_panel", "thing_caption", "record_strip", "value_label"}
    allowed = {"reading, µm from nominal"}  # handoff target, never added to the scene
    checked = 0
    for f in _scene_files():
        src = f.read_text()
        if "def part0_opening" not in src:
            continue
        tree = ast.parse(src)
        opening = next(n for n in ast.walk(tree)
                       if isinstance(n, ast.FunctionDef) and n.name == "part0_opening")
        for node in ast.walk(opening):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            name = node.func.id if isinstance(node.func, ast.Name) else \
                getattr(node.func, "attr", None)
            if name not in display:
                continue
            for arg in node.args:
                if not (isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)):
                    continue
                lit = arg.value
                checked += 1
                if lit in allowed:
                    continue
                hits = [w for w in POSTPONED if w in lit.lower()]
                assert not hits, f"{f.name} opening displays {hits} in {lit!r}"
    assert checked >= 4, f"only {checked} display strings inspected; test is vacuous"
