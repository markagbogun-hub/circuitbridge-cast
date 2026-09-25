import numpy as np
from castwise_audio_doctor.integrated_repair import IntegratedRepairQC

def test_integrated_repair_updates_qc():
    sr=1000
    x=np.ones((1000,2),dtype=np.float32)*.05
    c=IntegratedRepairQC(x,sr)
    old=c.after.rms_dbfs
    c.select(0,.5); c.preview_gain(6)
    assert c.after.rms_dbfs > old
    assert c.last_operation.startswith("Gain")

def test_undo_restores_qc_state():
    sr=1000; x=np.ones((1000,1),dtype=np.float32)*.1
    c=IntegratedRepairQC(x,sr); before=c.after.rms_dbfs
    c.preview_gain(6); c.undo()
    assert abs(c.after.rms_dbfs-before)<1e-3
