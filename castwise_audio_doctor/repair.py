"""Castwise Audio Doctor 1.9 Professional Repair Studio engine."""
from dataclasses import dataclass
import numpy as np
import soundfile as sf
from scipy import signal

@dataclass
class Selection:
    start: float
    end: float

class RepairSession:
    def __init__(self, audio: np.ndarray, sample_rate: int):
        self.audio = np.asarray(audio, dtype=np.float32).copy()
        if self.audio.ndim == 1:
            self.audio = self.audio[:, None]
        self.sample_rate = int(sample_rate)
        self.selection = Selection(0.0, len(self.audio)/self.sample_rate)
        self.undo_stack, self.redo_stack = [], []

    def _save(self):
        self.undo_stack.append(self.audio.copy())
        self.redo_stack.clear()

    def select(self,start,end):
        dur=len(self.audio)/self.sample_rate
        self.selection=Selection(max(0,min(start,dur)),max(0,min(end,dur)))

    def gain(self, db, selection_only=True):
        self._save(); factor=10**(db/20)
        if selection_only:
            i,j=[int(x*self.sample_rate) for x in (self.selection.start,self.selection.end)]
            self.audio[i:j]*=factor
        else: self.audio*=factor

    def remove_dc(self):
        self._save(); self.audio-=self.audio.mean(axis=0,keepdims=True)

    def highpass(self,hz=40):
        self._save()
        sos=signal.butter(4,hz,btype="highpass",fs=self.sample_rate,output="sos")
        for c in range(self.audio.shape[1]):
            self.audio[:,c]=signal.sosfiltfilt(sos,self.audio[:,c])

    def trim(self):
        i,j=[int(x*self.sample_rate) for x in (self.selection.start,self.selection.end)]
        if j<=i: return
        self._save(); self.audio=self.audio[i:j].copy()
        self.selection=Selection(0,len(self.audio)/self.sample_rate)

    def delete(self):
        i,j=[int(x*self.sample_rate) for x in (self.selection.start,self.selection.end)]
        if j<=i: return
        self._save(); self.audio=np.concatenate((self.audio[:i],self.audio[j:]))
        self.selection=Selection(0,len(self.audio)/self.sample_rate)

    def limiter(self,ceiling_db=-1.0):
        self._save()
        c=10**(ceiling_db/20)
        self.audio=np.tanh(self.audio/c)*c

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.audio.copy()); self.audio=self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.audio.copy()); self.audio=self.redo_stack.pop()

    def detect_silence(self,threshold_db=-50,min_ms=500):
        mono=self.audio.mean(axis=1)
        frame=max(1,int(.02*self.sample_rate)); out=[]; start=None
        frames=[]
        for i in range(0,max(0,len(mono)-frame),frame):
            db=20*np.log10(max(np.sqrt(np.mean(mono[i:i+frame]**2)+1e-20),1e-12))
            frames.append((i,i+frame,db))
        need=max(1,int(min_ms/20))
        for k,(_,_,db) in enumerate(frames):
            if db<threshold_db and start is None: start=k
            if db>=threshold_db and start is not None:
                if k-start>=need: out.append((frames[start][0]/self.sample_rate,frames[k-1][1]/self.sample_rate))
                start=None
        return out

    def save(self,path):
        sf.write(path,np.clip(self.audio,-1,1),self.sample_rate,subtype="PCM_24")
