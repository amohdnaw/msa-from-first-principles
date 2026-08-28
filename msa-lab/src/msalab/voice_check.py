"""Measure the voice that actually got rendered.

This module exists because of a real regression. `narration.py` falls back from
Kokoro to gTTS when the Kokoro interpreter is missing, deliberately, so that a
voice problem does not stop a build. Level 1 of this site shipped in gTTS because
`kokoro_voice.py` had not been copied across, the fallback printed a warning, and
the warning was filtered out of the build log by a `grep -v`.

Nothing downstream could catch it: the mp4 was the right length, the captions
were right, the poster was right. Only the sound was wrong, and no gate listened.

So this measures the rendered audio and answers one question with a number: is
the median fundamental frequency inside the band an American male explainer
occupies? gTTS sits at 209 Hz. Kokoro `am_michael` sits at 118 Hz. There is no
overlap, which makes the check unambiguous.

Autocorrelation rather than a library, because the alternative is 1.6 GB of torch
in the render venv for one number.

    PYTHONPATH=src .venv/bin/python -m msalab.voice_check <file.wav>
"""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

#: The band from `specs/narration-voice.md`, measured across nine candidate
#: voices. am_michael is 118 Hz; the nearest reject above the band is gTTS at
#: 209 Hz and the nearest below is Piper's en_US-joe at 96 Hz.
BAND_LOW_HZ = 100.0
BAND_HIGH_HZ = 130.0

#: Search range for the estimator itself, wider than the band so a voice outside
#: it is measured rather than clipped to the edge.
F0_MIN_HZ = 60.0
F0_MAX_HZ = 320.0

FRAME_S = 0.045
HOP_S = 0.020
#: A frame is voiced if its RMS clears this fraction of the loudest frame.
VOICED_RMS_FRACTION = 0.18


def _read_mono(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        n = w.getnframes()
        width = w.getsampwidth()
        chans = w.getnchannels()
        raw = w.readframes(n)
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(width)
    if dtype is None:
        raise ValueError(f"{path.name}: unsupported sample width {width}")
    x = np.frombuffer(raw, dtype=dtype).astype(np.float64)
    if dtype is np.uint8:
        x -= 128.0
    if chans > 1:
        x = x.reshape(-1, chans).mean(axis=1)
    peak = np.abs(x).max()
    return (x / peak if peak else x), rate


def _frame_f0(frame: np.ndarray, rate: int) -> float | None:
    """Median-of-one F0 for a frame, by autocorrelation. None if unvoiced."""
    frame = frame - frame.mean()
    if not np.any(frame):
        return None
    corr = np.correlate(frame, frame, mode="full")[len(frame) - 1:]
    lo = int(rate / F0_MAX_HZ)
    hi = min(int(rate / F0_MIN_HZ), len(corr) - 1)
    if hi <= lo:
        return None
    window = corr[lo:hi]
    lag = int(np.argmax(window)) + lo
    # a genuine period needs the peak to stand clear of the zero-lag energy
    if corr[0] <= 0 or window.max() / corr[0] < 0.30:
        return None
    return rate / lag


def median_f0(path: str | Path) -> dict:
    """Median F0 over voiced frames, plus how much of the file was voiced."""
    path = Path(path)
    x, rate = _read_mono(path)
    fl = int(FRAME_S * rate)
    hop = int(HOP_S * rate)
    if len(x) < fl:
        raise ValueError(f"{path.name}: too short to measure")

    frames = [x[i:i + fl] for i in range(0, len(x) - fl, hop)]
    rms = np.array([float(np.sqrt(np.mean(f ** 2))) for f in frames])
    if rms.max() <= 0:
        raise ValueError(f"{path.name}: silent")
    loud = rms >= VOICED_RMS_FRACTION * rms.max()

    f0s = [f for f, keep in zip((_frame_f0(f, rate) for f in frames), loud)
           if keep and f is not None]
    if not f0s:
        raise ValueError(f"{path.name}: no voiced frames found")
    return {
        "file": path.name,
        "seconds": len(x) / rate,
        "median_f0": float(np.median(f0s)),
        "voiced_frames": len(f0s),
        "voiced_fraction": len(f0s) / max(1, len(frames)),
        "in_band": BAND_LOW_HZ <= float(np.median(f0s)) <= BAND_HIGH_HZ,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bad = 0
    for arg in sys.argv[1:]:
        try:
            r = median_f0(arg)
        except Exception as exc:                        # noqa: BLE001
            print(f"  {arg}: {exc}")
            bad = 1
            continue
        verdict = "in band" if r["in_band"] else "OUT OF BAND"
        print(f"  {r['file']:<28} {r['median_f0']:6.1f} Hz  "
              f"{r['seconds']:6.1f} s  voiced {r['voiced_fraction']*100:4.0f} %  "
              f"{verdict}")
        if not r["in_band"]:
            bad = 1
    print(f"  band: {BAND_LOW_HZ:.0f}-{BAND_HIGH_HZ:.0f} Hz "
          f"(am_michael 118, gTTS 209)")
    return bad


if __name__ == "__main__":
    raise SystemExit(main())
