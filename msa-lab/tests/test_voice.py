"""The voice gate.

Level 1 shipped narrated in gTTS instead of Kokoro `am_michael`, and every other
artifact was correct: right duration, right captions, right poster, right frames.
The only wrong thing was the sound, and nothing was listening.

These tests listen. They read the rendered wav and measure it, so the check is
independent of the plumbing that produced it — a future refactor of the speech
service, the worker interpreter or the build script cannot fool them.

Skipped rather than failed when no render exists, because a fresh clone has no
media and a missing file is not a voice regression.
"""
import pathlib

import numpy as np
import pytest

from msalab.voice_check import (
    BAND_HIGH_HZ, BAND_LOW_HZ, F0_MAX_HZ, F0_MIN_HZ, median_f0,
)

LAB = pathlib.Path(__file__).resolve().parents[1]
RENDERS = sorted(LAB.glob("media/videos/*/1080p60/*.wav"))


def _rendered():
    if not RENDERS:
        pytest.skip("no 1080p60 render present to measure")
    return RENDERS


# ------------------------------------------------- the estimator itself first
# A measurement gate is only worth having if the instrument is calibrated, and
# the cheapest calibration is a signal whose answer is known exactly.
@pytest.mark.parametrize("hz", [90.0, 118.0, 150.0, 209.0, 300.0])
def test_the_estimator_recovers_a_known_tone(tmp_path, hz):
    import wave
    rate = 24000
    t = np.arange(int(rate * 1.5)) / rate
    # a couple of harmonics, so it is not a pure sine the autocorrelator finds
    # trivially, and an envelope so some frames are quiet
    sig = (np.sin(2 * np.pi * hz * t)
           + 0.5 * np.sin(4 * np.pi * hz * t)
           + 0.25 * np.sin(6 * np.pi * hz * t))
    sig *= 0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t)
    pcm = (sig / np.abs(sig).max() * 32000).astype(np.int16)
    f = tmp_path / f"tone_{int(hz)}.wav"
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    got = median_f0(f)["median_f0"]
    assert got == pytest.approx(hz, rel=0.04), f"measured {got:.1f} for a {hz} tone"


def test_the_estimator_refuses_silence(tmp_path):
    import wave
    f = tmp_path / "silence.wav"
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(np.zeros(24000, dtype=np.int16).tobytes())
    with pytest.raises(ValueError):
        median_f0(f)


def test_the_band_excludes_gtts_and_includes_am_michael():
    """The two numbers the band exists to separate, from specs/narration-voice.md."""
    assert BAND_LOW_HZ <= 118.0 <= BAND_HIGH_HZ, "am_michael must be inside"
    assert not (BAND_LOW_HZ <= 209.0 <= BAND_HIGH_HZ), "gTTS must be outside"
    assert F0_MIN_HZ < BAND_LOW_HZ and BAND_HIGH_HZ < F0_MAX_HZ, (
        "the search range has to be wider than the band, or a voice outside it "
        "gets clipped to the edge and measures as a pass")


# ------------------------------------------------------ then the real renders
def test_every_rendered_act_is_in_the_explainer_band():
    for wav in _rendered():
        r = median_f0(wav)
        assert r["in_band"], (
            f"{wav.parent.parent.name}: median F0 {r['median_f0']:.1f} Hz is "
            f"outside {BAND_LOW_HZ:.0f}-{BAND_HIGH_HZ:.0f} Hz. gTTS measures "
            f"around 209 and am_michael 118 — this render is almost certainly "
            f"in the wrong voice.")


def test_every_rendered_act_is_actually_narrated():
    """Guards the other direction: an act with no speech in it at all.

    A silent render would pass a pitch check by having no voiced frames to
    measure, so the fraction is asserted rather than assumed.
    """
    for wav in _rendered():
        r = median_f0(wav)
        assert r["voiced_fraction"] > 0.25, (
            f"{wav.name}: only {r['voiced_fraction']*100:.0f} % of frames are "
            "voiced — is the narration actually there?")
        assert r["seconds"] > 30, f"{wav.name}: {r['seconds']:.0f} s is too short"
