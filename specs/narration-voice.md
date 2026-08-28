# Narration voice — decided, shipping, and now gated

Inherited from the SPC build, where it was parked 2026-08-27 and then adopted.
**On this site Kokoro `am_michael` at speed 0.92 is the shipping voice**, not a
someday option — the SPC line about "keep shipping with gTTS" was stale by the
time this file was copied across, and copying a stale sentence is how the wrong
voice ships.

## The regression that added the gate (2026-08-28)

Level 1 shipped in gTTS. `narration.py` falls back from Kokoro to gTTS when the
Kokoro interpreter is missing, on purpose, so a voice problem cannot stop a
build. But `kokoro_voice.py` had never been copied into `msalab`, so every render
took the fallback, the warning it printed went into a build log that was being
filtered with `grep -v`, and nothing downstream noticed: the mp4 was the right
length, the captions were right, the poster was right. Only the sound was wrong.

Measured after the fact, the shipped audio was **215.2 Hz** against am_michael's
118. Two things changed:

1. **The fallback is fatal by default.** `MSALAB_VOICE_SERVICE=gtts` asks for
   gTTS on purpose; `MSALAB_VOICE_FALLBACK=1` re-enables the silent substitution.
   Otherwise a missing Kokoro stops the render with the reason.
2. **`msalab.voice_check` measures the rendered wav** and a test asserts the
   median F0 sits between 100 and 130 Hz. gTTS at 209 and am_michael at 118 do
   not overlap, so the check is unambiguous. Autocorrelation, no new dependency.

The general shape of this is worth keeping: a fallback nobody sees is not
resilience, and every artifact except the one that mattered was correct.

## The decision

**Kokoro `am_michael` at speed 0.92**, if a synthetic voice is ever wanted.
Second choice `am_adam`. Piper `en_US-ryan-high` if the 1.6 GB of torch is not
worth it.

Ammar's plan is to record his own voice, which beats all of them. The recorder
path is already wired and needs no code:

```bash
cd msa-lab
MSALAB_VOICE=1 MSALAB_VOICE_SERVICE=recorder ./build-media.sh
```

`RecorderService` prompts per line and caches each take, keyed on the line's
text, so a re-render only re-records lines whose words changed. 41 lines in Level 1 so far.

## Why am_michael, measured rather than argued

Median F0 over voiced frames, and words per minute, on the same test line
("Ninety nine point seven three percent. Nobody chose that number. It is what
plus and minus three sigma is worth."):

| Voice | Engine | F0 median | wpm |
|---|---|---|---|
| en_US-joe-medium | Piper | 96 Hz | 180 |
| en_US-norman-medium | Piper | 107 Hz | 182 |
| am_puck | Kokoro | 115 Hz | 154 |
| en_US-hfc_male-medium | Piper | 117 Hz | 189 |
| **am_michael** | **Kokoro** | **118 Hz** | **143** |
| am_adam | Kokoro | 121 Hz | 157 |
| en_US-bryce-medium | Piper | 125 Hz | 139 |
| am_liam | Kokoro | 127 Hz | 168 |
| am_fenrir | Kokoro | 143 Hz | 152 |
| en_US-ryan-high | Piper | 158 Hz | 200 |
| en-GB *(what ships today)* | gTTS | **209 Hz** | 136 |

The target band is an American male explainer: roughly 110–125 Hz, unhurried at
140–165 wpm. `am_michael` is the only voice inside it on both axes, and over a
twenty-second passage it stays dry instead of drifting into performance.

The current gTTS voice sits at 209 Hz, which is the measurable reason the acts
sound like a station announcement rather than an explanation.

## What was refused

Cloning Grant Sanderson's voice. It is his, he did not consent, and a
curriculum whose entire argument is *derived, not asserted* cannot open with a
stolen larynx. What is reproducible is the character — pitch, pace, restraint —
and that is what the table above measures.

## How to bring it back

Nothing about this is installed. Both engines were removed after the trial to
keep 1.6 GB off a disk that was at 93 %. To redo it:

```bash
python3 -m venv ~/tts-lab/venv
~/tts-lab/venv/bin/pip install kokoro soundfile
# pip pulls the CUDA build unasked — 5.3 GB. Fix it immediately:
~/tts-lab/venv/bin/pip install --force-reinstall torch \
  --index-url https://download.pytorch.org/whl/cpu
~/tts-lab/venv/bin/pip list | grep -i nvidia | awk '{print $1}' \
  | xargs ~/tts-lab/venv/bin/pip uninstall -y
```

```python
from kokoro import KPipeline
import soundfile as sf, numpy as np
pipe = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
chunks = [a for _, _, a in pipe(text, voice='am_michael', speed=0.92)]
sf.write(out_path, np.concatenate(chunks), 24000)
```

Wiring it into the render is one `SpeechService` subclass — `manim_voiceover`
ships gtts / azure / elevenlabs / gemini / openai / pyttsx3 / recorder and none
of these — plus one full rebuild, about twenty minutes for all nine acts.
Captions regenerate from the audio automatically, and pacing does not change,
because pacing comes from the narration script rather than from the audio.

The comparison page and its samples are kept at `~/tts-lab/` (4 MB), servable
with `python3 -m http.server 7317` from that directory.
