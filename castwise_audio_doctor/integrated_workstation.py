"""v2.5 Integrated Repair + QC workstation."""
import soundfile as sf
from PySide6.QtWidgets import QMainWindow,QWidget,QHBoxLayout,QVBoxLayout,QPushButton,QFileDialog,QLabel,QTableWidget,QTableWidgetItem
from .timeline_widget import QCTimelineWidget
from .marker_panel import MarkerPanel
from .repair_controls import RepairControls
from .integrated_repair import IntegratedRepairQC
from .presets import PRESETS

class IntegratedWorkstation(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent); self.setWindowTitle("Castwise Audio Doctor — Integrated Repair & QC")
        self.ctrl=None
        self.timeline=QCTimelineWidget(); self.markers=MarkerPanel(); self.repairs=RepairControls()
        self.status=QLabel("Open audio to begin.")
        self.metrics=QTableWidget(0,3); self.metrics.setHorizontalHeaderLabels(["Metric","Before","After"])
        openb=QPushButton("Open Audio"); openb.clicked.connect(self.open_audio)
        export=QPushButton("Export Repaired + Re-QC"); export.clicked.connect(self.export)
        top=QHBoxLayout(); top.addWidget(openb); top.addWidget(export); top.addWidget(self.status)
        left=QVBoxLayout(); left.addLayout(top); left.addWidget(self.timeline); left.addWidget(self.metrics)
        lw=QWidget(); lw.setLayout(left)
        main=QHBoxLayout(); main.addWidget(lw,4); main.addWidget(self.markers,1); main.addWidget(self.repairs,1)
        w=QWidget(); w.setLayout(main); self.setCentralWidget(w)
        self.timeline.selectionChanged.connect(self.select)
        self.markers.markerActivated.connect(self.timeline.jump_to_marker)
        self.repairs.operationRequested.connect(self.operation)

    def open_audio(self):
        p,_=QFileDialog.getOpenFileName(self,"Open Audio","","Audio Files (*.wav *.flac *.ogg *.aiff *.aif *.mp3)")
        if not p:return
        x,sr=sf.read(p,always_2d=True)
        self.ctrl=IntegratedRepairQC(x,sr,PRESETS["Radio"])
        self.timeline.set_audio(x,sr,self.ctrl.before.markers); self.markers.set_markers(self.ctrl.before.markers)
        self._metrics(); self.status.setText(f"QC {self.ctrl.before.status} | Score {self.ctrl.before.score}")

    def select(self,a,b):
        if self.ctrl:self.ctrl.select(a,b); self.repairs.status.setText(f"Selection {a:.2f}s – {b:.2f}s")

    def operation(self,op,val):
        if not self.ctrl:return
        try:
            fn={"gain":lambda:self.ctrl.preview_gain(val),
                "highpass":lambda:self.ctrl.preview_highpass(val),
                "dc":self.ctrl.preview_dc,
                "limiter":lambda:self.ctrl.preview_limiter(val),
                "trim":self.ctrl.preview_trim,
                "delete":self.ctrl.preview_delete,
                "undo":self.ctrl.undo,
                "redo":self.ctrl.redo}[op]
            fn(); self._refresh(); self.repairs.status.setText(f"Applied: {self.ctrl.last_operation}")
        except Exception as e:self.repairs.status.setText(f"Repair error: {e}")

    def _metrics(self):
        b=self.ctrl.before; a=self.ctrl.after
        rows=[("LUFS-I",b.lufs_i,a.lufs_i),("Peak dBFS",b.peak_dbfs,a.peak_dbfs),
              ("True peak approx",b.true_peak_dbfs_approx,a.true_peak_dbfs_approx),
              ("RMS dBFS",b.rms_dbfs,a.rms_dbfs),("Clipping samples",b.clipping_samples,a.clipping_samples),
              ("Silence seconds",b.silence_seconds,a.silence_seconds),("Score",b.score,a.score)]
        self.metrics.setRowCount(len(rows))
        for i,(n,x,y) in enumerate(rows):
            self.metrics.setItem(i,0,QTableWidgetItem(n)); self.metrics.setItem(i,1,QTableWidgetItem(f"{x:.2f}" if isinstance(x,float) else str(x))); self.metrics.setItem(i,2,QTableWidgetItem(f"{y:.2f}" if isinstance(y,float) else str(y)))

    def _refresh(self):
        self._metrics()
        self.timeline.set_audio(self.ctrl.audio,self.ctrl.sample_rate,self.ctrl.after.markers)
        self.markers.set_markers(self.ctrl.after.markers)
        self.status.setText(f"After QC {self.ctrl.after.status} | Score {self.ctrl.after.score}")

    def export(self):
        if not self.ctrl:return
        p,_=QFileDialog.getSaveFileName(self,"Export Repaired Audio","","WAV (*.wav)")
        if p:
            r=self.ctrl.commit_and_export(p); self._refresh()
            self.status.setText(f"Exported + re-QC: {r.status} | Score {r.score}")
