import numpy as np
from castwise_audio_doctor.repair import RepairSession

def test_gain_and_undo_redo():
    x=np.ones((1000,2),dtype=np.float32)*.1
    r=RepairSession(x,1000)
    r.select(0,0.5); r.gain(6)
    assert np.isclose(r.audio[100,0],.1*10**(.3),rtol=1e-3)
    r.undo(); assert np.isclose(r.audio[100,0],.1)
    r.redo(); assert r.audio[100,0]>.1

def test_trim_delete():
    x=np.zeros((1000,1),dtype=np.float32)
    r=RepairSession(x,1000); r.select(.2,.7); r.trim()
    assert len(r.audio)==500
    r.select(.1,.2); r.delete()
    assert len(r.audio)==400

def test_silence_detection():
    x=np.concatenate([np.ones(500)*.1,np.zeros(700),np.ones(500)*.1]).astype(np.float32)[:,None]
    r=RepairSession(x,1000)
    sil=r.detect_silence(-50,500)
    assert sil and sil[0][1]-sil[0][0] >= .5

def test_highpass():
    sr=1000; t=np.arange(1000)/sr
    x=np.sin(2*np.pi*5*t).astype(np.float32)[:,None]
    r=RepairSession(x,sr); r.highpass(40)
    assert np.sqrt(np.mean(r.audio**2)) < .2
