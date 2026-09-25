import os
import numpy as np
from castwise_audio_doctor.batch_processor import BatchProcessor

def test_discover(tmp_path):
    p=tmp_path/"a.wav"; p.write_bytes(b"x")
    q=tmp_path/"b.txt"; q.write_text("x")
    b=BatchProcessor()
    assert p in b.discover([tmp_path])
    assert q not in b.discover([tmp_path])

def test_batch_output(tmp_path):
    import soundfile as sf
    p=tmp_path/"tone.wav"
    sf.write(p,np.zeros((1000,1),dtype="float32"),1000)
    out=tmp_path/"out"
    r=BatchProcessor().process([p],out)
    assert len(r)==1 and r[0].output.endswith("_repaired.wav")
    assert os.path.exists(r[0].output)
