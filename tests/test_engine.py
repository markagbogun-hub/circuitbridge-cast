import numpy as np
import soundfile as sf
from castwise_audio_doctor.engine import analyze, score, normalize

def test_analysis(tmp_path):
    sr=48000
    t=np.arange(sr)/sr
    y=(0.1*np.sin(2*np.pi*1000*t)).astype("float32")
    p=tmp_path/"tone.wav"; sf.write(p,y,sr)
    m=analyze(p)
    assert m.sr==48000
    assert m.channels==1
    assert m.duration > .99
    assert m.true_peak < 0
    assert 0 <= score(m,"Radio") <= 100

def test_normalize(tmp_path):
    sr=48000
    y=np.zeros(sr,dtype="float32")
    y[:sr//2]=0.05
    src=tmp_path/"src.wav"; dst=tmp_path/"out.wav"
    sf.write(src,y,sr)
    normalize(src,dst,"Podcast")
    assert dst.exists()
