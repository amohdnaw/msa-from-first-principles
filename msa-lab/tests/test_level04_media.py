import json
import pathlib
import subprocess
import pytest

LAB = pathlib.Path(__file__).resolve().parents[1]

def get_mp4s():
    p1 = LAB / "media/videos/level04_scene/1080p60/Level04.mp4"
    p2 = LAB / "media/videos/level04_case_scene/1080p60/Level04Case.mp4"
    return [p1, p2]

def get_manifests():
    p1 = LAB / "media/videos/level04_scene/1080p60/Level04.manifest.json"
    p2 = LAB / "media/videos/level04_case_scene/1080p60/Level04Case.manifest.json"
    return [p1, p2]

def get_posters():
    p1 = LAB.parent / "posters/level04.jpg"
    p2 = LAB.parent / "posters/level04-case.jpg"
    return [p1, p2]

def get_captions():
    p1 = LAB.parent / "captions/level04.vtt"
    p2 = LAB.parent / "captions/level04-case.vtt"
    return [p1, p2]

@pytest.mark.parametrize("mp4", get_mp4s())
def test_mp4_dimensions_and_framerate(mp4):
    assert mp4.exists(), f"missing {mp4}"
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True, check=True).stdout.strip().split(',')
    w, h, r = out
    assert int(w) == 1920
    assert int(h) == 1080
    assert r == "60/1"

@pytest.mark.parametrize("mp4", get_mp4s())
def test_mp4_has_audio_stream(mp4):
    assert mp4.exists(), f"missing {mp4}"
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                          "-show_entries", "stream=codec_type",
                          "-of", "csv=p=0", str(mp4)],
                         capture_output=True, text=True).stdout.strip()
    assert out == "audio", f"{mp4.name} has no audio stream"
    
    out_duration = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=duration", "-select_streams", "a:0", "-of", "csv=p=0", str(mp4)], capture_output=True, text=True).stdout.strip()
    assert out_duration, "no duration for audio stream"
    # Some builds might output multiple lines if there are multiple packets/streams, just get first
    out_duration = out_duration.split()[0].split(',')[0]
    assert float(out_duration) > 0, "audio stream duration is 0"

@pytest.mark.parametrize("mp4", get_mp4s())
def test_mp4_is_faststart(mp4):
    out = subprocess.run(["ffprobe", "-v", "trace", "-i", str(mp4)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
    moov_pos = out.find("type:'moov'")
    mdat_pos = out.find("type:'mdat'")
    assert moov_pos != -1
    assert mdat_pos != -1
    assert moov_pos < mdat_pos, f"{mp4.name} moov atom is after mdat (not faststart)"

@pytest.mark.parametrize("caption", get_captions())
def test_caption_is_non_empty(caption):
    assert caption.exists(), f"missing {caption}"
    text = caption.read_text()
    assert "WEBVTT" in text
    cues = text.count("-->")
    assert cues > 0, f"{caption.name} has no cues"

@pytest.mark.parametrize("poster", get_posters())
def test_poster_is_non_empty(poster):
    assert poster.exists(), f"missing {poster}"
    assert poster.stat().st_size > 0, f"{poster.name} is empty"

@pytest.mark.parametrize("manifest_path", get_manifests())
def test_manifest_has_required_fields(manifest_path):
    assert manifest_path.exists(), f"missing {manifest_path}"
    manifest = json.loads(manifest_path.read_text())
    assert "scene" in manifest
    assert "service" in manifest
    assert "duration" in manifest
    assert "poster_time" in manifest
    assert "cue_count" in manifest
