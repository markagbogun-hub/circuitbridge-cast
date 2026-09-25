"""Castwise Audio Doctor v2.5 Broadcast QC Workstation core."""
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import json, math
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy import signal

@dataclass
class Marker:
    time: float
    kind: str
    duration: float = 0.0
    value: float = 0.0
    message: str = ""

@dataclass
class QCResult:
    duration: float
    sample_rate: int
    channels: int
    peak_dbfs: float
    rms_dbfs: float
    lufs_i: float
    true_peak_dbfs_approx: float
    phase_correlation: Optional[float]
    clipping_samples: int
    silence_seconds: float
    markers: List[Marker]
    score: int
    status: str

class BroadcastQC:
    def __init__(self, target_lufs=-14.0, ceiling_dbtp=-1.0,
                 silence_db=-50.0, clip_threshold=0.999):
        self.target_lufs=float(target_lufs)
        self.ceiling_dbtp=float(ceiling_dbtp)
        self.silence_db=float(silence_db)
        self.clip_threshold=float(clip_threshold)

    def _db(self, x):
        return 20*np.log10(max(float(x),1e-12))

    def _markers(self, x, sr):
        mono=x.mean(axis=1)
        frame=max(1,int(sr*0.02))
        markers=[]
        for i in range(0,max(0,len(mono)-frame),frame):
            block=mono[i:i+frame]
            rms=np.sqrt(np.mean(block*block)+1e-20)
            db=self._db(rms)
            if db < self.silence_db:
                # Merge consecutive silence frames.
                if markers and markers[-1].kind=="silence" and abs(markers[-1].time+markers[-1].duration-i/sr)<1e-9:
                    markers[-1].duration += frame/sr
                else:
                    markers.append(Marker(i/sr,"silence",frame/sr,db,"Low-level/silence region"))
        # Clip markers: merge sample runs.
        clipped=np.any(np.abs(x)>=self.clip_threshold,axis=1)
        starts=np.where(np.diff(np.r_[False,clipped,False].astype(int))==1)[0]
        ends=np.where(np.diff(np.r_[False,clipped,False].astype(int))==-1)[0]
        for a,b in zip(starts,ends):
            markers.append(Marker(a/sr,"clip",(b-a)/sr,float(b-a),"Potential digital clipping"))
        markers.sort(key=lambda m:m.time)
        return markers

    def analyze_array(self,x,sr):
        x=np.asarray(x,dtype=np.float32)
        if x.ndim==1: x=x[:,None]
        duration=len(x)/sr
        peak=float(np.max(np.abs(x))) if len(x) else 0
        rms=float(np.sqrt(np.mean(x*x))) if len(x) else 0
        mono=x.mean(axis=1)
        meter=pyln.Meter(sr)
        try: lufs=float(meter.integrated_loudness(mono))
        except Exception: lufs=float("-inf")
        # 4x oversampled approximation, retained explicitly as approximation.
        up=np.concatenate([signal.resample_poly(x[:,c],4,1) for c in range(x.shape[1])])
        tp=self._db(np.max(np.abs(up)) if len(up) else 0)
        corr=None
        if x.shape[1]>=2:
            a,b=x[:,0],x[:,1]
            den=np.sqrt(np.sum(a*a)*np.sum(b*b))
            corr=float(np.sum(a*b)/den) if den else 0.0
        markers=self._markers(x,sr)
        clip=int(np.sum(np.any(np.abs(x)>=self.clip_threshold,axis=1)))
        silence=sum(m.duration for m in markers if m.kind=="silence")
        score=100
        if lufs != float("-inf"): score-=min(30,abs(lufs-self.target_lufs)*4)
        score-=min(25,max(0,tp-self.ceiling_dbtp)*8)
        if clip: score-=min(25,clip/10)
        score-=min(15,silence/max(duration,1)*15)
        score=max(0,min(100,int(round(score))))
        status="PASS" if score>=85 else ("WARN" if score>=70 else "FAIL")
        return QCResult(duration,sr,x.shape[1],self._db(peak),self._db(rms),lufs,tp,corr,
                        clip,silence,markers,score,status)

    def analyze_file(self,path):
        x,sr=sf.read(path,always_2d=True)
        return self.analyze_array(x,sr)

    @staticmethod
    def result_dict(result):
        d=asdict(result)
        d["markers"]=[asdict(m) for m in result.markers]
        return d

    @staticmethod
    def save_json(result,path):
        with open(path,"w",encoding="utf-8") as f:
            json.dump(BroadcastQC.result_dict(result),f,indent=2)

    def batch(self,paths):
        return [(p,self.analyze_file(p)) for p in paths]
