from pathlib import Path
import numpy as np
import soundfile as sf
from castwise_audio_doctor.engine import analyze, normalize, repair_audio

def test_stereo_analysis(tmp_path):
    sr=48000
    t=np.arange(sr,dtype=np.float32)/sr
    y=np.column_stack([0.1*np.sin(2*np.pi*440*t),0.1*np.sin(2*np.pi*440*t+0.1)]).astype('float32')
    p=tmp_path/'stereo.wav'; sf.write(p,y,sr)
    m=analyze(p)
    assert m.channels==2
    assert -1.0 <= m.phase <= 1.0

def test_repair_export(tmp_path):
    sr=48000; t=np.arange(sr,dtype=np.float32)/sr
    y=(0.08*np.sin(2*np.pi*500*t)+0.02).astype('float32')
    src=tmp_path/'src.wav'; dst=tmp_path/'repair.wav'; sf.write(src,y,sr)
    repair_audio(src,dst,'Podcast',dc_remove=True,highpass_hz=30)
    assert dst.exists()
    m=analyze(dst)
    assert abs(m.dc) < 0.01
