"""Standalone Castwise v2.5 interactive QC workstation window."""
import soundfile as sf
from PySide6.QtWidgets import QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QPushButton,QFileDialog,QLabel,QComboBox
from .qc_workstation import BroadcastQC
from .timeline_widget import QCTimelineWidget
from .marker_panel import MarkerPanel
from .presets import PRESETS

class WorkstationWindow(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Castwise Audio Doctor — Broadcast QC Workstation")
        self.audio=None; self.sr=None; self.result=None
        self.timeline=QCTimelineWidget(); self.panel=MarkerPanel()
        self.profile=QComboBox(); self.profile.addItems(PRESETS.keys())
        self.status=QLabel("Open an audio file to begin QC.")
        openb=QPushButton("Open Audio"); openb.clicked.connect(self.open_audio)
        row=QHBoxLayout(); row.addWidget(openb); row.addWidget(self.profile); row.addWidget(self.status)
        left=QVBoxLayout(); left.addLayout(row); left.addWidget(self.timeline)
        root=QHBoxLayout(); w=QWidget(); w.setLayout(root)
        leftw=QWidget(); leftw.setLayout(left); root.addWidget(leftw,4); root.addWidget(self.panel,1)
        self.setCentralWidget(w)
        self.panel.markerActivated.connect(self.timeline.jump_to_marker)

    def open_audio(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Audio","","Audio Files (*.wav *.flac *.ogg *.aiff *.aif *.mp3)")
        if not p:return
        x,sr=sf.read(p,always_2d=True); self.audio=x; self.sr=sr
        cfg=PRESETS[self.profile.currentText()]
        self.result=BroadcastQC(**cfg).analyze_array(x,sr)
        self.timeline.set_audio(x,sr,self.result.markers)
        self.panel.set_markers(self.result.markers)
        self.status.setText(f"{self.result.status}  |  Score {self.result.score}  |  {self.result.lufs_i:.1f} LUFS")
