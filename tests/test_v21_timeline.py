import numpy as np
from castwise_audio_doctor.timeline import Timeline
from castwise_audio_doctor.qc_workstation import BroadcastQC
from castwise_audio_doctor.presets import get_preset

def test_interactive_timeline_selection():
    t=Timeline(20); t.select(2,8)
    assert t.selection==(2,8)

def test_marker_generation():
    sr=1000
    x=np.zeros((2000,2),dtype=np.float32); x[:500]=.2; x[500:1500]=0; x[1500:1510]=1
    r=BroadcastQC(**get_preset("Radio")).analyze_array(x,sr)
    kinds={m.kind for m in r.markers}
    assert "silence" in kinds and "clip" in kinds
