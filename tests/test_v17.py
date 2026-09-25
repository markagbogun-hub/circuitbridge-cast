import numpy as np, soundfile as sf
from castwise_audio_doctor.engine import analyze, level_timeline, repair_audio

def test_level_timeline(tmp_path):
    sr=48000; x=np.zeros((sr*2,2),dtype=np.float32); t=np.arange(sr*2)/sr; x[:,0]=.1*np.sin(2*np.pi*1000*t); x[:,1]=x[:,0]
    p=tmp_path/'a.wav'; sf.write(p,x,sr)
    m=analyze(p); tl=level_timeline(x,sr)
    assert m.channels==2 and len(tl)>5

def test_repair_removes_dc(tmp_path):
    sr=16000; x=np.ones((sr,1),dtype=np.float32)*.02; p=tmp_path/'in.wav'; out=tmp_path/'out.wav'; sf.write(p,x,sr)
    repair_audio(p,out,'Podcast',True,0,False); y,_=sf.read(out,always_2d=True); assert abs(float(y.mean())) < .01
