import numpy as np
from castwise_audio_doctor.qc_workstation import BroadcastQC
from castwise_audio_doctor.presets import get_preset
from castwise_audio_doctor.timeline import Timeline

def test_qc_detects_clipping_and_silence():
    sr=1000
    x=np.zeros((2000,2),dtype=np.float32)
    x[0:500]=.2
    x[500:1500]=0
    x[1500:1510]=1.0
    r=BroadcastQC(**get_preset("Radio")).analyze_array(x,sr)
    assert r.clipping_samples > 0
    assert r.silence_seconds > 0

def test_timeline_bounds():
    t=Timeline(10); t.seek(20); assert t.position==10
    t.select(-2,20); assert t.selection==(0,10)

def test_json_result_shape(tmp_path):
    sr=48000
    x=np.zeros((4800,2),dtype=np.float32)
    r=BroadcastQC().analyze_array(x,sr)
    p=tmp_path/"qc.json"; BroadcastQC.save_json(r,p)
    assert p.exists()
    assert '"markers"' in p.read_text()
