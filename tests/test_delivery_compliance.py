from types import SimpleNamespace
from castwise_audio_doctor.delivery_profiles import get_profile, DeliveryProfile
from castwise_audio_doctor.compliance import evaluate

def qc(**kw):
    d = dict(lufs_i=-14.0, true_peak=-2.0, clipping_samples=0,
             max_silence_seconds=1.0, health_score=90,
             sample_rate=48000, channels=2)
    d.update(kw)
    return SimpleNamespace(**d)

def test_radio_pass():
    r = evaluate(qc(), get_profile("Radio"))
    assert r.status == "PASS"

def test_loudness_fail():
    r = evaluate(qc(lufs_i=-20), get_profile("Radio"))
    assert r.status == "FAIL"

def test_peak_fail():
    r = evaluate(qc(true_peak=-0.2), get_profile("Radio"))
    assert r.status == "FAIL"

def test_custom_profile():
    p = DeliveryProfile("Custom", target_lufs=-18, loudness_tolerance=.5,
                        max_true_peak_approx=-2, max_clipping_samples=0,
                        max_silence_seconds=1, min_score=80)
    r = evaluate(qc(lufs_i=-18, true_peak=-2.1, max_silence_seconds=.5, health_score=85), p)
    assert r.status == "PASS"
