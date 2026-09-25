from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from scipy.signal import resample_poly

PROFILES = {
    "Radio": {"lufs": -14.0, "tp": -1.0},
    "Podcast": {"lufs": -16.0, "tp": -1.0},
    "Streaming": {"lufs": -14.0, "tp": -1.0},
}

@dataclass
class Metrics:
    file: str
    duration: float
    sr: int
    channels: int
    subtype: str
    fmt: str
    lufs: float
    true_peak: float
    peak: float
    rms: float
    dynamic: float
    clipping: int
    clipping_pct: float
    silence_pct: float
    dc: float
    phase: float
    width: float
    lra: float

    def as_dict(self):
        return asdict(self)

def load_audio(path):
    path = str(path)
    data, sr = sf.read(path, always_2d=True, dtype="float32")
    return data, sr

def dbfs(x, floor=-120.0):
    v = 20*np.log10(max(float(abs(x)), 10**(floor/20)))
    return v

def true_peak_db(data, oversample=4):
    peak = 0.0
    for c in range(data.shape[1]):
        y = resample_poly(data[:, c], oversample, 1)
        peak = max(peak, float(np.max(np.abs(y))))
    return dbfs(peak)

def loudness_timeline(data, sr, frame=3.0, hop=1.0):
    meter = pyln.Meter(sr)
    mono = np.mean(data, axis=1)
    frame_n=max(1, int(frame*sr))
    hop_n=max(1, int(hop*sr))
    vals=[]
    for i in range(0, max(1, len(mono)-frame_n+1), hop_n):
        chunk=mono[i:i+frame_n]
        if len(chunk) < max(1, int(sr*0.4)):
            continue
        try:
            vals.append((i/sr, float(meter.integrated_loudness(chunk)))
            )
        except Exception:
            pass
    return vals

def analyze(path):
    p=Path(path)
    info=sf.info(str(p))
    data,sr=load_audio(p)
    n=len(data)
    duration=n/sr if sr else 0
    meter=pyln.Meter(sr)
    mono=np.mean(data,axis=1)
    try:
        lufs=float(meter.integrated_loudness(mono))
    except Exception:
        lufs=-70.0
    tp=true_peak_db(data)
    peak=dbfs(np.max(np.abs(data)))
    rms=dbfs(np.sqrt(np.mean(data**2)))
    dynamic=max(0.0, peak-rms)
    clip=np.sum(np.any(np.abs(data)>=0.999,axis=1))
    clip_pct=100*clip/max(1,n)
    silence=100*np.mean(np.max(np.abs(data),axis=1) < 10**(-50/20))
    dc=float(np.mean(mono))
    if data.shape[1]>=2:
        l=data[:,0]; r=data[:,1]
        den=np.sqrt(np.sum(l*l)*np.sum(r*r))
        phase=float(np.sum(l*r)/den) if den else 0.0
        width=float(np.std(l-r)/(np.std(l+r)+1e-12))
    else:
        phase=1.0; width=0.0
    try:
        lra=float(meter.loudness_range(mono))
    except Exception:
        lra=0.0
    return Metrics(
        file=p.name,duration=duration,sr=sr,channels=info.channels,
        subtype=info.subtype or "",fmt=info.format or "",lufs=lufs,
        true_peak=tp,peak=peak,rms=rms,dynamic=dynamic,clipping=int(clip),
        clipping_pct=clip_pct,silence_pct=float(silence),dc=dc,
        phase=phase,width=width,lra=lra
    )

def score(m, profile):
    t=PROFILES[profile]
    s=100.0
    s-=min(25, abs(m.lufs-t["lufs"])*2.0)
    if m.true_peak > t["tp"]: s-=min(20,(m.true_peak-t["tp"])*5)
    s-=min(20,m.clipping_pct*2)
    if m.silence_pct>5: s-=min(10,(m.silence_pct-5)*0.5)
    if abs(m.dc)>0.01: s-=min(8,abs(m.dc)*200)
    if m.phase<0.2: s-=min(12,(0.2-m.phase)*40)
    return int(max(0,min(100,round(s))))

def recommendations(m, profile):
    t=PROFILES[profile]
    r=[]
    if abs(m.lufs-t["lufs"])>1: r.append(f"Adjust integrated loudness toward {t['lufs']:.1f} LUFS.")
    if m.true_peak>t["tp"]: r.append(f"Reduce true peak below {t['tp']:.1f} dBTP.")
    if m.clipping_pct>0: r.append("Clipping detected: inspect the source chain and reduce pre-limiter gain.")
    if m.silence_pct>5: r.append("Significant silence/dead-air detected; review pauses and automation.")
    if abs(m.dc)>0.01: r.append("DC offset is elevated; apply DC removal before further processing.")
    if m.phase<0.2: r.append("Low stereo phase correlation; check polarity, widening and stereo processing.")
    if m.dynamic<6: r.append("Low peak-to-RMS contrast; review compression/limiting.")
    if not r: r.append("No major automated QC issue detected for the selected profile.")
    return r

def normalize(path, out_path, profile):
    data,sr=load_audio(path)
    m=analyze(path)
    target=PROFILES[profile]["lufs"]
    gain_db=target-m.lufs
    if not np.isfinite(gain_db):
        gain_db=0.0
    gain_db=float(np.clip(gain_db,-40.0,40.0))
    gain=10**(gain_db/20)
    y=np.nan_to_num(data*gain,nan=0.0,posinf=0.0,neginf=0.0)
    ceiling=10**(PROFILES[profile]["tp"]/20)
    mx=float(np.max(np.abs(y)))
    if mx>ceiling:
        y*=ceiling/mx
    y=np.clip(y,-1,1)
    sf.write(out_path,y,sr,subtype="PCM_24")
    return out_path


def level_timeline(data, sr, frame=0.4, hop=0.1):
    """Fast peak/RMS timeline for UI meters and history graphs."""
    mono=np.mean(data,axis=1)
    frame_n=max(1,int(frame*sr)); hop_n=max(1,int(hop*sr))
    out=[]
    for i in range(0,max(1,len(mono)-frame_n+1),hop_n):
        c=mono[i:i+frame_n]
        if len(c)==0: continue
        pk=float(np.max(np.abs(c)))
        rmsv=float(np.sqrt(np.mean(c*c)))
        out.append((i/sr,dbfs(pk),dbfs(rmsv)))
    return out

def repair_audio(path,out_path,profile,dc_remove=True,highpass_hz=0.0,trim_silence=False):
    """Non-destructive repair chain: DC removal, optional high-pass, loudness/ceiling normalization."""
    from scipy.signal import butter, sosfiltfilt
    data,sr=load_audio(path)
    y=data.astype(np.float32,copy=True)
    if dc_remove:
        y-=np.mean(y,axis=0,keepdims=True)
    if highpass_hz and highpass_hz>0 and highpass_hz < sr/2:
        sos=butter(4,highpass_hz,btype='highpass',fs=sr,output='sos')
        for c in range(y.shape[1]): y[:,c]=sosfiltfilt(sos,y[:,c]).astype(np.float32)
    tmp=Path(out_path).with_suffix('.tmp.wav')
    sf.write(tmp,y,sr,subtype='PCM_24')
    normalize(str(tmp),out_path,profile)
    try: tmp.unlink()
    except OSError: pass
    return out_path
