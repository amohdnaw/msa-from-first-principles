"""The gates that read the built pages rather than the library.

A library test proves the arithmetic. These prove the *site* says what the
contract promised, and they exist because on the SPC build several defects lived
entirely in the gap between the two: a runtime claim that drifted from the
rendered videos, three `next` links that resolved while pointing past a level,
and equations that shipped as literal words because the source was double-escaped.

Every check here maps to a numbered line in
`specs/msa-curriculum-contract.md`. If a check has no contract line, it should
not be here; if a contract line has no check, it is a promise nobody is keeping.
"""
import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[2]
INDEX = REPO / "index.html"
CONTRACT = REPO / "specs" / "msa-curriculum-contract.md"

SPC = "amohdnaw.github.io/spc-from-first-principles"
PLATFORM = "msa.amohdnaw.xyz"

WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
         "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12}


def pages():
    """Every page the site actually serves."""
    return sorted(REPO.glob("level-[0-9][0-9].html")) + [INDEX]


def written():
    """Level pages that are real chapters rather than stubs."""
    return [p for p in sorted(REPO.glob("level-[0-9][0-9].html"))
            if 'class="sec-no"' in p.read_text()]


def _claim():
    m = re.search(r"An interactive curriculum[^<]*", INDEX.read_text())
    assert m, "the index has to state what it contains"
    return m.group(0)


def _spelled(text, unit):
    m = re.search(r"(\w+)\s+" + unit, text)
    assert m, f"no spelled number before {unit!r} in: {text!r}"
    word = m.group(1).lower()
    assert word in WORDS, f"unspelled or unknown number {word!r} before {unit!r}"
    return WORDS[word]


# ------------------------------------------------ contract check 11: the seam
def test_exactly_one_outbound_link_to_the_spc_curriculum_sitewide():
    """Contract check 11, and the reason it is counted rather than trusted.

    The first live deploy had four: one in the index nav, one in the index prose,
    and one in the footer of every page — which means the count would have grown
    by one with every level written. A per-page check would have passed on each
    page individually.
    """
    hits = {p.name: p.read_text().count(SPC) for p in pages()}
    total = sum(hits.values())
    assert total == 1, f"the seam is spent {total} times, not once: {hits}"


def test_exactly_one_outbound_link_to_the_msa_platform_sitewide():
    hits = {p.name: p.read_text().count(PLATFORM) for p in pages()}
    total = sum(hits.values())
    assert total == 1, f"the platform link is spent {total} times, not once: {hits}"


def test_the_seam_links_are_safe_to_open():
    for p in pages():
        t = p.read_text()
        for host in (SPC, PLATFORM):
            for m in re.finditer(r'<a[^>]*' + re.escape(host) + r'[^>]*>', t):
                assert 'rel="noopener"' in m.group(0), (
                    f"{p.name}: outbound seam link without noopener")


# -------------------------------------- contract check 12: the boundary rule
@pytest.mark.parametrize("banned", [
    "control limit", "control chart", "Shewhart", "Cpk", "Ppk",
    "in control", "out of control",
])
def test_this_site_never_teaches_control_limits(banned):
    """The boundary rule from §2 of the parent contract.

    The index is allowed to *name* the sibling's subject when it explains why
    two sites exist; a level page teaching it is the breach.
    """
    for p in written():
        body = p.read_text()
        main = body[body.index("<main"):body.index("</main>")]
        assert banned.lower() not in main.lower(), (
            f"{p.name} teaches {banned!r}, which belongs to the SPC site")


# ------------------------------------ contract check 5: the count is honest
def test_the_index_states_seven_levels():
    assert _spelled(_claim(), "levels") == 7


def test_the_written_count_matches_the_pages_that_exist():
    claim = _claim()
    if re.search(r"\ball written\b", claim):
        assert len(written()) == _spelled(claim, "levels")
        return
    assert _spelled(claim, "written") == len(written()), (
        f"index claims {_spelled(claim, 'written')} written, "
        f"found {len(written())}: {[p.name for p in written()]}")


def test_the_spine_has_a_card_for_every_level():
    t = INDEX.read_text()
    live = len(re.findall(r'<a class="lv"', t))
    inert = t.count('class="lv soon"')
    assert live + inert == _spelled(_claim(), "levels")
    assert live == len(written()), "a live card must have a written page behind it"


# ------------------------------- contract check 9: the chain has to be walked
def test_every_level_links_to_the_next_written_one_or_the_index():
    """Resolving is not sufficient.

    The SPC build shipped three `next` links that returned 200 while pointing
    *past* a level, so readers were walked straight over content that existed.
    A link is correct only if it lands on the next written level, or on the index
    when there is no next.
    """
    have = [p.name for p in written()]
    for i, p in enumerate(written()):
        m = re.search(r'<a class="next"[^>]*href="([^"]+)"', p.read_text())
        assert m, f"{p.name} has no next link"
        target = m.group(1)
        expected = have[i + 1] if i + 1 < len(have) else "index.html"
        assert target == expected, (
            f"{p.name} points at {target}, skipping {expected}")
        assert (REPO / target).exists(), f"{p.name} points at a missing {target}"


# ------------------------- contract check 6: media exists and is opt-in only
def test_every_written_level_has_its_act_poster_and_captions():
    for p in written():
        t = p.read_text()
        src = re.search(r'<source src="([^"]+\.mp4)"', t)
        assert src, f"{p.name} has no act"
        assert (REPO / src.group(1)).exists(), f"{p.name}: missing {src.group(1)}"
        poster = re.search(r'poster="([^"]+)"', t)
        assert poster and (REPO / poster.group(1)).exists(), f"{p.name}: no poster"
        track = re.search(r'<track[^>]*src="([^"]+\.vtt)"', t)
        assert track and (REPO / track.group(1)).exists(), f"{p.name}: no captions"


def test_no_caption_track_is_forced_on():
    """WCAG 1.2.2 asks that captions be available, not enabled."""
    for p in pages():
        for m in re.finditer(r"<track[^>]*>", p.read_text()):
            assert "default" not in m.group(0), f"{p.name}: a track is defaulted on"


# ------------------- contract check 8: no number on the page is asserted
def test_the_equations_render_as_maths_and_not_as_words():
    """The SPC build shipped two pages whose equations read as the literal words
    `alpha` and `longrightarrow`, because a heredoc doubled every backslash and
    KaTeX read the result as a line break. Every existing check passed, because
    they all asked whether KaTeX emitted anything.
    """
    for p in pages():
        t = p.read_text()
        # KaTeX emits two layers: a `katex-mathml` block whose <annotation> holds
        # the LaTeX source verbatim, and a `katex-html` block that is what a
        # sighted reader sees. Stripping tags reads the source and can never
        # pass. The visible layer is the only one that answers the question.
        for m in re.finditer(r'class="katex-html"(.*?)</span></span>', t, re.S):
            visible = re.sub(r"<[^>]+>", "", m.group(1))
            for word in ("sigma", "alpha", "dfrac", "sqrt", "longrightarrow",
                         "operatorname", "\\\\"):
                assert word not in visible, (
                    f"{p.name}: an equation rendered {word!r} as text: "
                    f"{visible[:70]!r}")
        # and the source layer must still be present, or there is no maths at all
        if 'class="eq-body"' in t:
            assert 'class="katex-mathml"' in t, f"{p.name}: no maths rendered"


def test_no_data_tex_is_left_unrendered():
    for p in pages():
        t = p.read_text()
        for m in re.finditer(r'<[^>]*data-tex="[^"]*"[^>]*>(.*?)</', t, re.S):
            assert "katex" in m.group(1), f"{p.name}: a data-tex never rendered"


# ------------------------------------- the page has to have a title at all
def test_every_page_has_a_non_empty_title_and_dek():
    """A page with no h1 shipped live, and no check noticed.

    `build_main()` replaces everything between <main> and </main>, and the title
    is folded in afterwards from a standalone `header.opener`. Put that opener
    INSIDE main - as the first MSA page source did - and it is deleted before the
    fold can read it, so the page renders with an empty `<h1 class="page-title">`.
    The browser sweep passed: an empty heading overflows nothing.
    """
    for p in pages():
        t = p.read_text()
        m = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
        assert m, f"{p.name} has no h1 at all"
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        assert len(title) > 3, f"{p.name} has an empty h1"
        d = re.search(r'<p class="dek"[^>]*>(.*?)</p>', t, re.S)
        assert d, f"{p.name} has no dek"
        dek = re.sub(r"<[^>]+>", "", d.group(1)).strip()
        assert len(dek) > 20, f"{p.name} has an empty dek"


def test_the_chapter_block_is_centred_not_flush_left():
    """The same root cause, measured structurally.

    `div.wrap` carries `margin:0 auto`. It has to sit OUTSIDE main for the same
    reason the opener does, and when it sat inside, the prose rendered at x = 0
    against SPC's x = 253 at the same viewport - identical measure, identical
    figure width, wrong position.
    """
    for p in written():
        t = p.read_text()
        wrap = t.index('<div class="wrap">')
        main = t.index("<main")
        assert wrap < main, (
            f"{p.name}: div.wrap is inside main, so build_main deletes it and "
            "the chapter loses its centring")


# --------------------------- contract check 1: it is the same kind of artifact
def test_the_pages_wear_the_inherited_ground_and_wordmark():
    for p in pages():
        t = p.read_text()
        assert "--ground:#0d1114" in t.replace(" ", ""), f"{p.name}: wrong ground"
        assert "/ MSA" in t, f"{p.name}: wrong wordmark"
        assert "/ SPC<" not in t, f"{p.name}: SPC wordmark leaked in"


def test_amber_never_encodes_data():
    """DESIGN.md: amber is wayfinding. A verdict class may not carry it."""
    for p in pages():
        t = p.read_text()
        for m in re.finditer(r"\.tile\.(pass|fail|cond)[^{]*\{([^}]*)\}", t):
            assert "--accent" not in m.group(2), (
                f"{p.name}: a verdict state uses the wayfinding accent")


def test_the_conditional_state_has_no_hue():
    """Amendment 2: conditional is neutral, never a third colour."""
    for p in pages():
        for m in re.finditer(r"\.tile\.cond[^{]*\{([^}]*)\}", p.read_text()):
            body = m.group(1)
            assert "--signal-ok" not in body and "--signal-alarm" not in body, (
                f"{p.name}: the conditional state took a semantic colour")


# ------------------------------------------- the contract itself has to exist
def test_the_contract_is_in_the_repo_and_names_its_checks():
    t = CONTRACT.read_text()
    assert "## 1. What you will see" in t
    assert t.count("\n1. ") >= 1
    for phrase in ("exactly one", "Seven level pages exist",
                   "never teaches control limits"):
        assert phrase in t, f"the contract no longer says {phrase!r}"


def test_every_page_declares_a_24px_tap_target():
    """WCAG 2.5.8. The nav, rail, wordmark and footer links are 11-13px mono, so
    their text boxes come out 16-23px tall and need an explicit min-height.

    Found by a browser sweep at 390px, not by reading the CSS - four levels had
    already shipped with rail links at 23px and footer links at 17px.
    """
    for p in sorted(REPO.glob("level-0*.html")) + [REPO / "index.html"]:
        css = p.read_text()
        assert "min-height:24px" in css, f"{p.name}: no 24px tap-target rule"


def test_range_inputs_are_tall_enough_to_touch():
    """A native range track is about 16px. Every lab slider sets its own height."""
    for p in sorted(REPO.glob("level-0*.html")):
        css = p.read_text()
        if "type=\"range\"" not in css:
            continue
        i = css.index("input[type=range]{")
        rule = css[i:css.index("}", i)]
        assert "height:24px" in rule, f"{p.name}: slider under 24px"


def test_no_kept_block_is_silently_dropped():
    """chapterise exits if the spec forgets a block the source provides.

    Level 5 shipped a build with its interactive missing because chapter_05 never
    emitted K["lab"]: the source had it, extract kept it, the build succeeded and
    the page had no lab. The tool now refuses; this holds the refusal in place.
    """
    src = (REPO / "tools" / "chapterise.py").read_text()
    assert 'for name in ("lab", "sys", "next")' in src
    assert "dropped the" in src
    assert 'for fname, fig in keep["figs"].items()' in src


def test_the_tile_grid_stacks_on_a_phone():
    """Two readout tiles need ~284 px including the gap; a 320 px viewport has
    272 px of content width. Level 5 overflowed by 9 px the moment its labels
    grew longer than Level 4's, on CSS that had passed the sweep before.
    """
    for p in sorted(REPO.glob("level-0*.html")):
        css = p.read_text()
        if "lab-grid-tiles" not in css:
            continue
        assert "@media(max-width:400px)" in css, f"{p.name}: no tile stack rule"
        i = css.index("@media(max-width:400px)")
        block = css[i:css.index("}", css.index("{", i) + 1) + 1]
        assert "grid-template-columns:1fr" in block, f"{p.name}: tiles never stack"


def test_no_tile_label_opts_out_of_the_label_voice():
    """`nc` exists for symbols whose case carries meaning - the micro sign, sigma,
    d2. A spelled-out word has no case meaning, and Level 6 shipped a lowercase
    `kappa` tile beside four uppercase siblings before this caught it.
    """
    for p in sorted(REPO.glob("level-0*.html")):
        for m in re.finditer(r'<dt>(.*?)</dt>', p.read_text(), re.S):
            inner = m.group(1)
            for nc in re.findall(r'<span class="nc">(.*?)</span>', inner):
                assert not re.fullmatch(r"[a-z]{4,}", nc.strip()), (
                    f"{p.name}: tile label opts a plain word out of caps: {nc!r}")


def test_no_regenerable_build_output_is_tracked():
    """The repo tracks the six 1080p60 mp4s the site serves, and nothing else
    that ./build-media.sh can rebuild.

    The gitignore was copied from a repo where `media/` sat at the root. Here it
    is `msa-lab/media/`, and a pattern containing a slash is anchored to the
    directory holding the gitignore - so every rule was dead from the first
    commit. 444 MB went in unnoticed: 6 wav files at 252 MB, 2447 Text-cache
    entries, 766 partial movies, 389 low-quality proofs. `git status` was clean
    throughout, because the files were tracked rather than untracked.
    """
    import subprocess
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True,
                         text=True, check=True).stdout.split()
    junk = [f for f in out if any(
        pat in f for pat in ("/480p15/", "/partial_movie_files/",
                             "/media/voiceovers/", "/media/texts/",
                             "/media/images/", "/media/Tex/"))
        or f.endswith((".wav", ".srt"))]
    assert junk == [], f"{len(junk)} regenerable files tracked, e.g. {junk[:4]}"


def test_every_asset_the_site_serves_is_tracked():
    """The other half of the same claim: untracking the build output must not
    take an asset a page references with it."""
    import subprocess
    tracked = set(subprocess.run(["git", "ls-files"], cwd=REPO,
                                 capture_output=True, text=True,
                                 check=True).stdout.split())
    missing = []
    for p in sorted(REPO.glob("level-0*.html")) + [REPO / "index.html"]:
        for ref in re.findall(r'(?:src|href)="((?:msa-lab|posters|captions|'
                              r'vendor|fonts)/[^"]+)"', p.read_text()):
            if ref not in tracked:
                missing.append(f"{p.name} -> {ref}")
    assert missing == [], f"referenced but untracked: {missing[:4]}"
