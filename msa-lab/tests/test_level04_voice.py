import json
import pathlib
import pytest
from msalab.voice_check import median_f0, BAND_LOW_HZ, BAND_HIGH_HZ

LAB = pathlib.Path(__file__).resolve().parents[1]

def get_targets():
    p1 = LAB / "media/videos/level04_scene/1080p60/Level04.mp4"
    p2 = LAB / "media/videos/level04_case_scene/1080p60/Level04Case.mp4"
    targets = []
    for p in [p1, p2]:
        m = p.with_suffix(".manifest.json")
        w = p.with_suffix(".wav")
        targets.append((p, m, w))
    return targets

@pytest.mark.parametrize("mp4, manifest_path, wav_path", get_targets())
def test_level04_voice_meets_manifest_service(mp4, manifest_path, wav_path, tmp_path):
    assert mp4.exists(), f"missing {mp4}"
    assert manifest_path.exists(), f"missing manifest {manifest_path}"
    manifest = json.loads(manifest_path.read_text())
    service = manifest["service"]
    
    if not wav_path.exists():
        import subprocess
        # extract wav from mp4 to measure it if not explicitly kept
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(mp4), "-vn", "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1", str(wav_path), "-y"], check=True)
    
    r = median_f0(wav_path)
    
    assert r["voiced_fraction"] > 0.25, f"{mp4.name}: only {r['voiced_fraction']*100:.0f}% frames voiced"
    
    if service == "kokoro":
        assert r["in_band"], (f"{mp4.name} (kokoro): median F0 {r['median_f0']:.1f} Hz outside "
                              f"{BAND_LOW_HZ}-{BAND_HIGH_HZ} Hz.")
    elif service == "recorder":
        # Do not impose F0 band
        pass
    else:
        pytest.fail(f"Unknown voice service in manifest: {service}")
