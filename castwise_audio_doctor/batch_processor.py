"""Castwise Audio Doctor v2.5 Batch Repair & QC Automation."""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Callable
import csv, json, traceback
import soundfile as sf
from .integrated_repair import IntegratedRepairQC
from .presets import get_preset

SUPPORTED={".wav",".flac",".ogg",".aiff",".aif",".mp3"}

@dataclass
class BatchItem:
    source:str
    output:str=""
    status:str="PENDING"
    score_before:Optional[int]=None
    score_after:Optional[int]=None
    lufs_before:Optional[float]=None
    lufs_after:Optional[float]=None
    peak_before:Optional[float]=None
    peak_after:Optional[float]=None
    message:str=""

class BatchProcessor:
    def __init__(self, profile="Radio", gain_db=0.0, highpass_hz=None,
                 remove_dc=True, limiter_ceiling=-1.0):
        self.profile=profile
        self.gain_db=float(gain_db)
        self.highpass_hz=highpass_hz
        self.remove_dc=remove_dc
        self.limiter_ceiling=float(limiter_ceiling)
        self.cancelled=False

    def cancel(self): self.cancelled=True

    def discover(self, paths, recursive=True):
        files=[]
        for p in paths:
            p=Path(p)
            if p.is_file() and p.suffix.lower() in SUPPORTED: files.append(p)
            elif p.is_dir():
                it=p.rglob("*") if recursive else p.glob("*")
                files.extend(x for x in it if x.is_file() and x.suffix.lower() in SUPPORTED)
        return sorted(set(files))

    def process(self, files, output_dir, progress:Optional[Callable]=None):
        outdir=Path(output_dir); outdir.mkdir(parents=True,exist_ok=True)
        results=[]
        cfg=get_preset(self.profile)
        for n,p in enumerate(files,1):
            item=BatchItem(str(p))
            try:
                if self.cancelled:
                    item.status="CANCELLED"; item.message="Batch cancelled"; results.append(item); break
                x,sr=sf.read(str(p),always_2d=True)
                c=IntegratedRepairQC(x,sr,cfg)
                item.score_before=c.before.score; item.lufs_before=c.before.lufs_i
                item.peak_before=c.before.true_peak_dbfs_approx
                if self.remove_dc: c.preview_dc()
                if self.highpass_hz: c.preview_highpass(self.highpass_hz)
                if self.gain_db: c.preview_gain(self.gain_db,selection_only=False)
                c.preview_limiter(self.limiter_ceiling)
                out=outdir/(p.stem+"_repaired.wav")
                after=c.commit_and_export(str(out))
                item.output=str(out); item.score_after=after.score; item.lufs_after=after.lufs_i
                item.peak_after=after.true_peak_dbfs_approx
                item.status=after.status
                item.message="Processed and re-QC'd"
            except Exception as e:
                item.status="ERROR"; item.message=f"{type(e).__name__}: {e}"
            results.append(item)
            if progress: progress(n,len(files),item)
        return results

    @staticmethod
    def save_csv(results,path):
        rows=[asdict(r) for r in results]
        if not rows:return
        with open(path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    @staticmethod
    def save_json(results,path):
        with open(path,"w",encoding="utf-8") as f:
            json.dump([asdict(r) for r in results],f,indent=2)
