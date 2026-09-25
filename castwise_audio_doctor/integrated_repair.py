"""v2.5 integrated Repair <-> QC controller."""
from dataclasses import dataclass
import numpy as np
from .repair import RepairSession
from .qc_workstation import BroadcastQC

@dataclass
class RepairPreview:
    before: object
    after: object
    changed: bool
    operation: str

class IntegratedRepairQC:
    """Keeps an editable RepairSession and QC snapshots synchronized."""
    def __init__(self,audio,sr,profile=None):
        self.session=RepairSession(audio,sr)
        cfg=profile or {"target_lufs":-14.0,"ceiling_dbtp":-1.0,"silence_db":-50.0}
        self.qc=BroadcastQC(**cfg)
        self.before=self.qc.analyze_array(self.session.audio,sr)
        self.after=self.before
        self.last_operation="Loaded"

    @property
    def audio(self): return self.session.audio
    @property
    def sample_rate(self): return self.session.sample_rate

    def _apply(self,operation,fn):
        before=self.qc.analyze_array(self.session.audio,self.sample_rate)
        fn()
        self.after=self.qc.analyze_array(self.session.audio,self.sample_rate)
        self.last_operation=operation
        return RepairPreview(before,self.after,True,operation)

    def preview_gain(self,db,selection_only=True):
        return self._apply(f"Gain {db:+.1f} dB",lambda:self.session.gain(db,selection_only))

    def preview_highpass(self,hz=40):
        return self._apply(f"High-pass {hz:.0f} Hz",lambda:self.session.highpass(hz))

    def preview_dc(self):
        return self._apply("DC removal",self.session.remove_dc)

    def preview_limiter(self,ceiling=-1.0):
        return self._apply(f"Limiter ceiling {ceiling:.1f} dB",lambda:self.session.limiter(ceiling))

    def preview_trim(self):
        return self._apply("Trim selection",self.session.trim)

    def preview_delete(self):
        return self._apply("Delete selection",self.session.delete)

    def undo(self):
        self.session.undo()
        self.after=self.qc.analyze_array(self.session.audio,self.sample_rate)
        self.last_operation="Undo"
        return self.after

    def redo(self):
        self.session.redo()
        self.after=self.qc.analyze_array(self.session.audio,self.sample_rate)
        self.last_operation="Redo"
        return self.after

    def select(self,start,end):
        self.session.select(start,end)

    def compare(self):
        return {"before":self.qc.result_dict(self.before),
                "after":self.qc.result_dict(self.after),
                "operation":self.last_operation}

    def commit_and_export(self,path):
        self.session.save(path)
        # Always provide a fresh QC result for the rendered file.
        self.after=self.qc.analyze_file(path)
        return self.after
