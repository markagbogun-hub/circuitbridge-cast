"""Batch Repair & QC panel for Castwise Audio Doctor v2.5."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QProgressBar,QFileDialog,QListWidget,QComboBox,QDoubleSpinBox,QCheckBox,QSpinBox
from .batch_processor import BatchProcessor

class BatchWorker(QThread):
    progress=Signal(int,int,str,str); finished=Signal(object)
    def __init__(self,processor,files,outdir):
        super().__init__(); self.processor=processor; self.files=files; self.outdir=outdir
    def run(self):
        def cb(n,total,item): self.progress.emit(n,total,item.source,item.status)
        self.finished.emit(self.processor.process(self.files,self.outdir,cb))

class BatchPanel(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.files=[]; self.worker=None
        self.profile=QComboBox(); self.profile.addItems(["Radio","Podcast","Streaming","Broadcast Safe"])
        self.gain=QDoubleSpinBox(); self.gain.setRange(-24,24); self.gain.setSuffix(" dB")
        self.hp=QSpinBox(); self.hp.setRange(0,500); self.hp.setValue(40); self.hp.setSpecialValueText("Off")
        self.dc=QCheckBox("Remove DC"); self.dc.setChecked(True)
        self.start=QPushButton("Add Files / Folder"); self.start.clicked.connect(self.add)
        self.runb=QPushButton("Run Batch Repair + QC"); self.runb.clicked.connect(self.run)
        self.cancel=QPushButton("Cancel"); self.cancel.clicked.connect(self.stop)
        self.list=QListWidget(); self.bar=QProgressBar(); self.status=QLabel("0 files")
        l=QVBoxLayout(self)
        top=QHBoxLayout(); [top.addWidget(x) for x in (self.start,self.runb,self.cancel)]
        l.addLayout(top); l.addWidget(self.profile); l.addWidget(self.gain); l.addWidget(self.hp); l.addWidget(self.dc)
        l.addWidget(self.list); l.addWidget(self.bar); l.addWidget(self.status)

    def add(self):
        fs,_=QFileDialog.getOpenFileNames(self,"Select Audio Files","","Audio (*.wav *.flac *.ogg *.aiff *.aif *.mp3)")
        self.files.extend(fs); self.list.addItems(fs); self.status.setText(f"{len(self.files)} files queued")

    def run(self):
        if not self.files:return
        out=QFileDialog.getExistingDirectory(self,"Output Folder")
        if not out:return
        p=BatchProcessor(self.profile.currentText(),self.gain.value(),self.hp.value() or None,self.dc.isChecked())
        self.worker=BatchWorker(p,self.files,out); self.worker.progress.connect(self._progress)
        self.worker.finished.connect(self._done); self.worker.start()

    def stop(self):
        if self.worker and self.worker.isRunning(): self.worker.processor.cancel(); self.status.setText("Cancelling...")

    def _progress(self,n,total,src,status):
        self.bar.setMaximum(total); self.bar.setValue(n); self.status.setText(f"{n}/{total} — {status} — {src}")

    def _done(self,results):
        self.status.setText(f"Batch complete: {len(results)} files")
