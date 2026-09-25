import sys, csv, json, hashlib, shutil
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import soundfile as sf
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,
 QLabel,QPushButton,QComboBox,QFileDialog,QProgressBar,QTableWidget,QTableWidgetItem,QTextEdit,
 QTabWidget,QMessageBox,QAbstractItemView,QListWidget,QCheckBox,QDoubleSpinBox,QSplitter,QFrame,QSlider)
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QUrl
from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from .engine import analyze, score, recommendations, normalize, loudness_timeline, level_timeline, repair_audio
from .licensing import license_status, install_license_file
from .delivery_profiles import BUILTIN_PROFILES, DeliveryProfile
from .compliance import evaluate
from .delivery_engine import deliver

VERSION='3.1.0'


# CASTWISE_V1_9_REPAIR_STUDIO
# Professional repair controls: selection-aware gain, trim, silence detection,
# DC removal, high-pass filtering, limiter/ceiling preview, undo/redo and
# non-destructive repair queue. The original v2.5 interface remains available.
try:
    from PySide6.QtWidgets import (
        QDoubleSpinBox, QSpinBox, QCheckBox, QGroupBox, QHBoxLayout,
        QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem,
        QMessageBox, QProgressBar
    )
    from PySide6.QtCore import Qt
    import numpy as _np
    import soundfile as _sf
    from scipy import signal as _sig

    class RepairStudioMixin:
        def _cw19_init_repair(self):
            self._cw19_history=[]
            self._cw19_future=[]
            self._cw19_selected=(0.0, 0.0)
            self._cw19_audio=None
            self._cw19_sr=None

        def _cw19_snapshot(self):
            if getattr(self,"_cw19_audio",None) is not None:
                self._cw19_history.append(self._cw19_audio.copy())
                self._cw19_future.clear()

        def cw19_load_audio(self, path):
            x,sr=_sf.read(path, always_2d=True)
            self._cw19_audio=x.astype(_np.float32)
            self._cw19_sr=sr
            self._cw19_history=[]
            self._cw19_future=[]
            self._cw19_selected=(0.0, len(x)/sr)
            return len(x)/sr

        def cw19_set_selection(self, start, end):
            if self._cw19_audio is None: return
            dur=len(self._cw19_audio)/self._cw19_sr
            self._cw19_selected=(max(0,min(start,dur)), max(0,min(end,dur)))

        def cw19_apply_gain(self, db, selection_only=True):
            if self._cw19_audio is None: return
            self._cw19_snapshot()
            a,b=self._cw19_selected
            i,j=int(a*self._cw19_sr), int(b*self._cw19_sr)
            sl=slice(i,j) if selection_only else slice(None)
            self._cw19_audio[sl] *= 10**(db/20)

        def cw19_remove_dc(self):
            if self._cw19_audio is None: return
            self._cw19_snapshot()
            self._cw19_audio -= self._cw19_audio.mean(axis=0, keepdims=True)

        def cw19_highpass(self, hz=40):
            if self._cw19_audio is None: return
            self._cw19_snapshot()
            sos=_sig.butter(4, hz, btype="highpass", fs=self._cw19_sr, output="sos")
            for c in range(self._cw19_audio.shape[1]):
                self._cw19_audio[:,c]=_sig.sosfiltfilt(sos,self._cw19_audio[:,c]).astype(_np.float32)

        def cw19_trim_selection(self):
            if self._cw19_audio is None: return
            a,b=self._cw19_selected
            i,j=int(a*self._cw19_sr), int(b*self._cw19_sr)
            if j<=i: return
            self._cw19_snapshot()
            self._cw19_audio=self._cw19_audio[i:j].copy()
            self._cw19_selected=(0,len(self._cw19_audio)/self._cw19_sr)

        def cw19_delete_selection(self):
            if self._cw19_audio is None: return
            a,b=self._cw19_selected
            i,j=int(a*self._cw19_sr), int(b*self._cw19_sr)
            if j<=i: return
            self._cw19_snapshot()
            self._cw19_audio=_np.concatenate([self._cw19_audio[:i],self._cw19_audio[j:]],axis=0)
            self._cw19_selected=(0,len(self._cw19_audio)/self._cw19_sr)

        def cw19_undo(self):
            if self._cw19_history and self._cw19_audio is not None:
                self._cw19_future.append(self._cw19_audio.copy())
                self._cw19_audio=self._cw19_history.pop()

        def cw19_redo(self):
            if self._cw19_future and self._cw19_audio is not None:
                self._cw19_history.append(self._cw19_audio.copy())
                self._cw19_audio=self._cw19_future.pop()

        def cw19_detect_silence(self, threshold_db=-50.0, min_ms=500):
            if self._cw19_audio is None: return []
            mono=_np.mean(self._cw19_audio,axis=1)
            rms=_np.sqrt(_np.maximum(_np.mean(mono**2),1e-20))
            frame=max(1,int(self._cw19_sr*0.02))
            vals=[]
            for i in range(0,len(mono)-frame,frame):
                r=_np.sqrt(_np.mean(mono[i:i+frame]**2)+1e-20)
                vals.append((i,i+frame,20*_np.log10(max(r,1e-12))))
            silent=[]; start=None
            need=max(1,int(min_ms/20))
            for k,(_,_,db) in enumerate(vals):
                if db<threshold_db:
                    if start is None: start=k
                elif start is not None:
                    if k-start>=need:
                        silent.append((vals[start][0]/self._cw19_sr,vals[k-1][1]/self._cw19_sr))
                    start=None
            if start is not None and len(vals)-start>=need:
                silent.append((vals[start][0]/self._cw19_sr,vals[-1][1]/self._cw19_sr))
            return silent

        def cw19_limiter(self, ceiling_db=-1.0):
            if self._cw19_audio is None: return
            self._cw19_snapshot()
            ceiling=10**(ceiling_db/20)
            self._cw19_audio=_np.tanh(self._cw19_audio/ceiling)*ceiling

        def cw19_export_repair(self,path):
            if self._cw19_audio is None: return
            _sf.write(path, _np.clip(self._cw19_audio,-1,1), self._cw19_sr, subtype="PCM_24")

except Exception:
    pass

class AnalyzeWorker(QThread):
    done=Signal(object,object,object); fail=Signal(str)
    def __init__(self,path,profile): super().__init__(); self.path=path; self.profile=profile
    def run(self):
        try:
            m=analyze(self.path); data,sr=sf.read(self.path,always_2d=True,dtype='float32')
            self.done.emit(m,loudness_timeline(data,sr),level_timeline(data,sr))
        except Exception as e: self.fail.emit(str(e))

class BatchWorker(QThread):
    row=Signal(object); progress=Signal(int); done=Signal(); fail=Signal(str)
    def __init__(self,paths,profile): super().__init__(); self.paths=paths; self.profile=profile
    def run(self):
        try:
            total=max(1,len(self.paths))
            for i,p in enumerate(self.paths,1):
                m=analyze(p); self.row.emit((p,m,score(m,self.profile))); self.progress.emit(int(i*100/total))
            self.done.emit()
        except Exception as e: self.fail.emit(str(e))

class Chart(FigureCanvas):
    def __init__(self): self.fig=Figure(figsize=(8,3.8)); super().__init__(self.fig)
    def plot_wave(self,path,selection=None):
        self.fig.clear(); ax=self.fig.add_subplot(111); data,sr=sf.read(path,always_2d=True,dtype='float32'); y=np.mean(data,axis=1)
        step=max(1,len(y)//7000); x=np.arange(0,len(y),step)/sr; ax.plot(x,y[::step],linewidth=.65); ax.set_title('Waveform'); ax.set_xlabel('Time (s)'); ax.set_ylabel('Amplitude'); ax.grid(alpha=.18)
        if selection: ax.axvspan(selection[0],selection[1],alpha=.18)
        self.fig.tight_layout(); self.draw()
    def plot_loudness(self,timeline,levels):
        self.fig.clear(); ax=self.fig.add_subplot(111)
        if timeline:
            x=[a for a,b in timeline]; y=[b for a,b in timeline]; ax.plot(x,y,label='Loudness (3s window)')
        if levels:
            x=[a for a,b,c in levels]; y=[b for a,b,c in levels]; ax.plot(x,y,alpha=.45,label='Peak')
        ax.set_title('Loudness & Level History'); ax.set_xlabel('Time (s)'); ax.set_ylabel('dB / LUFS'); ax.grid(alpha=.18); ax.legend(); ax.set_ylim(-80,2); self.fig.tight_layout(); self.draw()

class MeterCard(QFrame):
    def __init__(self,name):
        super().__init__(); l=QVBoxLayout(self); self.name=QLabel(name); self.name.setObjectName('cardLabel'); self.value=QLabel('--'); self.value.setObjectName('cardValue'); l.addWidget(self.name); l.addWidget(self.value); self.setObjectName('card')
    def set(self,text): self.value.setText(text)

class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle(f'Castwise Audio Doctor {VERSION}'); self.resize(1380,900); self.setAcceptDrops(True)
        self.path=None; self.metrics=None; self.timeline=[]; self.levels=[]; self.batch_rows=[]; self.repaired_path=None; self.playing_source='A'; self.session_started=datetime.now(timezone.utc).isoformat(); self.recent=[]
        self.audio=QAudioOutput(); self.player=QMediaPlayer(); self.player.setAudioOutput(self.audio); self.player.positionChanged.connect(self.on_position); self.player.durationChanged.connect(self.on_duration)
        root=QWidget(); self.setCentralWidget(root); lay=QVBoxLayout(root)
        top=QHBoxLayout(); title=QLabel('CASTWISE AUDIO DOCTOR'); title.setObjectName('title'); top.addWidget(title); top.addStretch();
        self.profile=QComboBox(); self.profile.addItems(['Radio','Podcast','Streaming']); top.addWidget(QLabel('Profile')); top.addWidget(self.profile)
        for text,fn in [('Open Audio',self.open),('Batch QC',self.batch_open),('Deliver',self.deliver_current),('Save Session',self.save_session),('Load Session',self.load_session)]: b=QPushButton(text); b.clicked.connect(fn); top.addWidget(b)
        lay.addLayout(top)
        self.tabs=QTabWidget(); lay.addWidget(self.tabs)
        self.build_dashboard(); self.build_loudness(); self.build_waveform(); self.build_transport(); self.build_batch(); self.build_repair(); self.build_profiles()
        self.setStyleSheet('''QMainWindow,QWidget{background:#0d1218;color:#e8edf4;font-family:Segoe UI} QLabel#title{font-size:25px;font-weight:900;letter-spacing:1px} QPushButton{background:#1685e5;border:0;border-radius:7px;padding:10px 16px;font-weight:800;color:white} QPushButton:hover{background:#39a1ff} QComboBox,QTextEdit,QTableWidget,QListWidget{background:#151c24;border:1px solid #2b3541;border-radius:6px;color:#e8edf4} QHeaderView::section{background:#202a35;color:#fff;padding:8px} QFrame#card{background:#151c24;border:1px solid #2b3541;border-radius:9px} QLabel#cardLabel{color:#91a0b2;font-size:12px} QLabel#cardValue{font-size:23px;font-weight:900} QProgressBar{background:#151c24;border:1px solid #2b3541;border-radius:6px;text-align:center} QProgressBar::chunk{background:#1685e5;border-radius:5px}''')
        self.refresh_license()
    def build_dashboard(self):
        w=QWidget(); l=QVBoxLayout(w); head=QHBoxLayout(); self.status=QLabel('Drop an audio file here or click Open Audio.'); head.addWidget(self.status); head.addStretch(); self.license_label=QLabel(); head.addWidget(self.license_label); lb=QPushButton('Install License'); lb.clicked.connect(self.install_license); head.addWidget(lb); l.addLayout(head)
        cards=QGridLayout(); self.health=MeterCard('QC HEALTH'); self.lufs=MeterCard('INTEGRATED LOUDNESS'); self.tp=MeterCard('TRUE PEAK'); self.phase=MeterCard('PHASE CORRELATION'); self.lra=MeterCard('LOUDNESS RANGE'); self.clip=MeterCard('CLIPPING');
        for i,c in enumerate([self.health,self.lufs,self.tp,self.phase,self.lra,self.clip]): cards.addWidget(c,i//3,i%3)
        l.addLayout(cards)
        self.table=QTableWidget(0,2); self.table.setHorizontalHeaderLabels(['Metric','Value']); self.table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.table)
        self.recs=QTextEdit(); self.recs.setReadOnly(True); self.recs.setMaximumHeight(150); l.addWidget(self.recs)
        buttons=QHBoxLayout()
        for txt,fn in [('PDF Report',self.pdf),('Compliance Report',self.compliance_report),('Normalize & Export',self.norm),('Export CSV',self.csv)]: b=QPushButton(txt); b.clicked.connect(fn); buttons.addWidget(b)
        l.addLayout(buttons); self.tabs.addTab(w,'QC Dashboard')
    def build_loudness(self):
        w=QWidget(); l=QVBoxLayout(w); self.loudchart=Chart(); l.addWidget(self.loudchart); note=QLabel('History is calculated from the loaded program. Integrated loudness uses pyloudnorm; true-peak is an oversampled approximation.'); note.setWordWrap(True); l.addWidget(note); self.tabs.addTab(w,'Loudness History')
    def build_waveform(self):
        w=QWidget(); l=QVBoxLayout(w); self.wavechart=Chart(); l.addWidget(self.wavechart); self.sel=QLabel('Selection: none'); l.addWidget(self.sel); self.tabs.addTab(w,'Waveform')
    def build_transport(self):
        w=QWidget(); l=QVBoxLayout(w)
        self.transport_file=QLabel('No audio loaded')
        self.transport_file.setObjectName('transportFile'); l.addWidget(self.transport_file)
        row=QHBoxLayout()
        for txt,fn in [('▶ Play A',lambda:self.play_source('A')),('▶ Play B',lambda:self.play_source('B')),('⏸ Pause',self.pause_audio),('■ Stop',self.stop_audio)]:
            b=QPushButton(txt); b.clicked.connect(fn); row.addWidget(b)
        row.addStretch(); l.addLayout(row)
        seek=QHBoxLayout(); self.time_label=QLabel('00:00 / 00:00'); self.seek=QSlider(Qt.Horizontal); self.seek.sliderMoved.connect(self.seek_audio); seek.addWidget(self.seek); seek.addWidget(self.time_label); l.addLayout(seek)
        meters=QGridLayout()
        self.play_peak=MeterCard('PLAYBACK PEAK'); self.play_rms=MeterCard('PLAYBACK RMS'); self.play_phase=MeterCard('PLAYBACK PHASE')
        for i,c in enumerate([self.play_peak,self.play_rms,self.play_phase]): meters.addWidget(c,0,i)
        l.addLayout(meters)
        self.ab=QLabel('A/B: A = original • B = latest repair/normalization export')
        l.addWidget(self.ab)
        self.tabs.addTab(w,'Playback & A/B')
    def on_duration(self,ms): self.seek.setRange(0,max(0,int(ms)))
    def on_position(self,ms):
        if not self.seek.isSliderDown(): self.seek.setValue(int(ms))
        self.time_label.setText(f'{ms/1000:05.1f} / {self.player.duration()/1000:05.1f}')
        if self.path and self.timeline:
            sec=ms/1000.0; vals=[x for x in self.levels if abs(x[0]-sec)<=0.25]
            if vals:
                _,pk,rms=vals[-1]; self.play_peak.set(f'{pk:.1f} dBFS'); self.play_rms.set(f'{rms:.1f} dBFS')
            if self.metrics: self.play_phase.set(f'{self.metrics.phase:.3f}')
    def seek_audio(self,v): self.player.setPosition(int(v))
    def play_source(self,which):
        p=self.path if which=='A' else self.repaired_path
        if not p:
            QMessageBox.information(self,'A/B','Create a repair/normalization export first to use B playback.'); return
        self.playing_source=which; self.player.setSource(QUrl.fromLocalFile(str(p))); self.player.play(); self.transport_file.setText(f'{which}: {Path(p).name}')
    def pause_audio(self): self.player.pause()
    def stop_audio(self): self.player.stop()
    def build_batch(self):
        w=QWidget(); l=QVBoxLayout(w); bar=QHBoxLayout(); add=QPushButton('Add Files'); add.clicked.connect(self.batch_open); clear=QPushButton('Clear'); clear.clicked.connect(lambda:self.batch_list.clear()); run=QPushButton('Run Batch QC'); run.clicked.connect(self.run_batch); export=QPushButton('Export Batch CSV'); export.clicked.connect(self.batch_csv); bar.addWidget(add); bar.addWidget(clear); bar.addWidget(run); bar.addWidget(export); l.addLayout(bar)
        self.batch_list=QListWidget(); l.addWidget(self.batch_list); self.batch_progress=QProgressBar(); l.addWidget(self.batch_progress); self.batch_table=QTableWidget(0,6); self.batch_table.setHorizontalHeaderLabels(['File','LUFS','dBTP','LRA','Clips','Score']); self.batch_table.horizontalHeader().setStretchLastSection(True); l.addWidget(self.batch_table); self.tabs.addTab(w,'Batch QC')
    def build_profiles(self):
        w=QWidget(); l=QVBoxLayout(w)
        l.addWidget(QLabel('Delivery Profiles — configure customer-specific QC targets. Built-in profiles remain read-only.'))
        self.profile_info=QTextEdit(); self.profile_info.setReadOnly(True); l.addWidget(self.profile_info)
        self.profile.currentTextChanged.connect(self.show_profile_info)
        b=QPushButton('Export Profile JSON'); b.clicked.connect(self.export_profile); l.addWidget(b)
        self.tabs.addTab(w,'Delivery Profiles'); self.show_profile_info(self.profile.currentText())

    def show_profile_info(self,name):
        p=BUILTIN_PROFILES.get(name)
        if p: self.profile_info.setPlainText(json.dumps(p.to_dict(),indent=2))

    def export_profile(self):
        p=BUILTIN_PROFILES.get(self.profile.currentText())
        if not p:return
        out,_=QFileDialog.getSaveFileName(self,'Export Delivery Profile','','JSON (*.json)')
        if out: Path(out).write_text(json.dumps(p.to_dict(),indent=2),encoding='utf8')

    def compliance_report(self):
        if not self.metrics:return
        prof=BUILTIN_PROFILES.get(self.profile.currentText())
        result=evaluate(self.metrics,prof)
        out,_=QFileDialog.getSaveFileName(self,'Save Compliance Report','','JSON (*.json)')
        if out:
            payload={'product':'Castwise Audio Doctor','version':VERSION,'generated_utc':datetime.now(timezone.utc).isoformat(),'file':self.path,'profile':result.to_dict()}
            Path(out).write_text(json.dumps(payload,indent=2),encoding='utf8')

    def save_session(self):
        out,_=QFileDialog.getSaveFileName(self,'Save Castwise Session','','Castwise Session (*.cwa-session.json)')
        if not out:return
        data={'format':'castwise-session','version':VERSION,'saved_utc':datetime.now(timezone.utc).isoformat(),'audio_path':self.path,'profile':self.profile.currentText(),'repaired_path':self.repaired_path,'metrics':self.metrics.as_dict() if self.metrics else None}
        Path(out).write_text(json.dumps(data,indent=2,default=str),encoding='utf8')

    def load_session(self):
        p,_=QFileDialog.getOpenFileName(self,'Load Castwise Session','','Castwise Session (*.cwa-session.json *.json)')
        if not p:return
        try:
            d=json.loads(Path(p).read_text(encoding='utf8'))
            if d.get('format')!='castwise-session': raise ValueError('Not a Castwise session file.')
            idx=self.profile.findText(d.get('profile','Radio')); self.profile.setCurrentIndex(max(0,idx))
            audio=d.get('audio_path'); repaired=d.get('repaired_path')
            if audio and Path(audio).exists(): self.load(audio)
            self.repaired_path=repaired if repaired and Path(repaired).exists() else None
            self.status.setText(f'Session loaded • {Path(p).name}')
        except Exception as e: QMessageBox.warning(self,'Session',f'Could not load session: {e}')

    def build_delivery(self):
        w=QWidget(); l=QVBoxLayout(w)
        l.addWidget(QLabel('Commercial Delivery Engine — analyze, repair, re-check, and package a verified delivery.'))
        self.delivery_status=QLabel('Ready')
        self.delivery_status.setObjectName('deliveryStatus')
        l.addWidget(self.delivery_status)
        row=QHBoxLayout(); row.addWidget(QLabel('Profile')); self.delivery_profile=QComboBox(); self.delivery_profile.addItems(list(BUILTIN_PROFILES.keys())); self.delivery_profile.setCurrentText(self.profile.currentText()); row.addWidget(self.delivery_profile); row.addStretch(); l.addLayout(row)
        opts=QHBoxLayout(); self.delivery_dc=QCheckBox('Remove DC'); self.delivery_dc.setChecked(True); opts.addWidget(self.delivery_dc); opts.addWidget(QLabel('High-pass Hz')); self.delivery_hp=QDoubleSpinBox(); self.delivery_hp.setRange(0,500); self.delivery_hp.setDecimals(0); self.delivery_hp.setValue(0); opts.addWidget(self.delivery_hp); opts.addStretch(); l.addLayout(opts)
        self.delivery_log=QTextEdit(); self.delivery_log.setReadOnly(True); l.addWidget(self.delivery_log)
        b=QPushButton('RUN DELIVERY PIPELINE'); b.clicked.connect(self.deliver_current); l.addWidget(b); l.addStretch(); self.tabs.addTab(w,'Delivery Engine')

    def deliver_current(self):
        if not self.path:
            QMessageBox.information(self,'Delivery Engine','Open an audio file first.'); return
        out=QFileDialog.getExistingDirectory(self,'Choose Delivery Folder')
        if not out:return
        try:
            profile=self.delivery_profile.currentText() if hasattr(self,'delivery_profile') else self.profile.currentText()
            m=deliver(self.path,out,profile,dc_remove=(self.delivery_dc.isChecked() if hasattr(self,'delivery_dc') else True),highpass_hz=(self.delivery_hp.value() if hasattr(self,'delivery_hp') else 0.0))
            self.repaired_path=m['delivery']['path']
            self.delivery_status.setText(f"{m['status']} • Score {m['score']}/100")
            self.delivery_log.setPlainText(json.dumps(m,indent=2))
            self.ab.setText(f"A/B ready • A: {Path(self.path).name} • B: {Path(self.repaired_path).name}")
            QMessageBox.information(self,'Delivery Engine',f"Delivery {m['status']}\nScore: {m['score']}/100\n\nPackage: {out}")
        except Exception as e:
            self.error(str(e))

    def build_repair(self):
        w=QWidget(); l=QVBoxLayout(w); l.addWidget(QLabel('Professional repair chain — review the QC result before exporting.'))
        self.dc=QCheckBox('Remove DC offset'); self.dc.setChecked(True); l.addWidget(self.dc)
        hp=QHBoxLayout(); hp.addWidget(QLabel('High-pass filter (Hz)')); self.hp=QDoubleSpinBox(); self.hp.setRange(0,500); self.hp.setValue(0); self.hp.setDecimals(0); hp.addWidget(self.hp); hp.addStretch(); l.addLayout(hp)
        self.trim=QCheckBox('Trim silence (review manually; disabled in automated export)'); l.addWidget(self.trim)
        rb=QPushButton('Repair + Normalize Export'); rb.clicked.connect(self.repair); l.addWidget(rb); l.addStretch(); self.tabs.addTab(w,'Repair')
    def refresh_license(self):
        st=license_status(); self.license_label.setText((f"Licensed • {st.get('customer','')}" if st.get('reason')=='licensed' else f"Trial • {st.get('days_left',0)} day(s) remaining") if st.get('active') else 'Trial expired • Install a valid license')
    def install_license(self):
        p,_=QFileDialog.getOpenFileName(self,'Install Castwise License','','License (*.json)')
        if p:
            ok,msg=install_license_file(p); QMessageBox.information(self,'License',msg) if ok else QMessageBox.warning(self,'License',msg); self.refresh_license()
    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self,e):
        u=e.mimeData().urls();
        if u: self.load(u[0].toLocalFile())
    def open(self):
        p,_=QFileDialog.getOpenFileName(self,'Open audio','','Audio (*.wav *.flac *.ogg *.aiff *.aif *.mp3 *.m4a)');
        if p:self.load(p)
    def load(self,p):
        self.path=p; self.status.setText('Analyzing…'); self.worker=AnalyzeWorker(p,self.profile.currentText()); self.worker.done.connect(self.finish); self.worker.fail.connect(self.error); self.worker.start()
    def finish(self,m,timeline,levels):
        self.metrics=m; self.timeline=timeline; self.levels=levels; s=score(m,self.profile.currentText()); self.status.setText(f'Health Score: {s}/100  •  {m.file}')
        self.health.set(f'{s}/100'); self.lufs.set(f'{m.lufs:.2f} LUFS'); self.tp.set(f'{m.true_peak:.2f} dBTP'); self.phase.set(f'{m.phase:.3f}'); self.lra.set(f'{m.lra:.2f} LU'); self.clip.set(f'{m.clipping} / {m.clipping_pct:.3f}%')
        vals=[('Integrated LUFS',f'{m.lufs:.2f}'),('True Peak',f'{m.true_peak:.2f} dBTP'),('Peak',f'{m.peak:.2f} dBFS'),('RMS',f'{m.rms:.2f} dBFS'),('Dynamic',f'{m.dynamic:.2f} dB'),('LRA',f'{m.lra:.2f} LU'),('Clipping',f'{m.clipping} ({m.clipping_pct:.3f}%)'),('Silence',f'{m.silence_pct:.2f}%'),('DC Offset',f'{m.dc:.5f}'),('Phase',f'{m.phase:.3f}'),('Stereo Width',f'{m.width:.3f}'),('Sample Rate',f'{m.sr} Hz'),('Channels',str(m.channels)),('Duration',f'{m.duration:.2f} s')]
        self.table.setRowCount(len(vals));
        for i,(a,b) in enumerate(vals): self.table.setItem(i,0,QTableWidgetItem(a)); self.table.setItem(i,1,QTableWidgetItem(b))
        self.recs.setPlainText('\n'.join('• '+x for x in recommendations(m,self.profile.currentText()))); self.wavechart.plot_wave(self.path); self.loudchart.plot_loudness(timeline,levels)
    def error(self,e): QMessageBox.critical(self,'Analysis Error',e); self.status.setText('Analysis failed.')
    def pdf(self):
        if not self.metrics:return
        out,_=QFileDialog.getSaveFileName(self,'Save PDF','','PDF (*.pdf)');
        if out:
            from .report import make_report; make_report(self.path,self.metrics,self.profile.currentText(),out)
    def norm(self):
        if not self.path:return
        out,_=QFileDialog.getSaveFileName(self,'Export normalized WAV','','WAV (*.wav)');
        if out: normalize(self.path,out,self.profile.currentText()); self.repaired_path=out; self.ab.setText(f'A/B ready • A: {Path(self.path).name} • B: {Path(out).name}')
    def csv(self):
        if not self.metrics:return
        out,_=QFileDialog.getSaveFileName(self,'Export CSV','','CSV (*.csv)');
        if out:
            with open(out,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['Metric','Value']); [w.writerow([k,v]) for k,v in self.metrics.as_dict().items()]
    def batch_open(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Add audio files','','Audio (*.wav *.flac *.ogg *.aiff *.aif *.mp3 *.m4a)')
        for p in paths:
            if not any(self.batch_list.item(i).text()==p for i in range(self.batch_list.count())): self.batch_list.addItem(p)
    def run_batch(self):
        paths=[self.batch_list.item(i).text() for i in range(self.batch_list.count())]
        if not paths:return
        self.batch_table.setRowCount(0); self.batch_rows=[]; self.batch_progress.setValue(0); self.bw=BatchWorker(paths,self.profile.currentText()); self.bw.row.connect(self.batch_row); self.bw.progress.connect(self.batch_progress.setValue); self.bw.done.connect(lambda:self.status.setText(f'Batch QC complete • {len(paths)} files')); self.bw.fail.connect(self.error); self.bw.start()
    def batch_row(self,item):
        p,m,s=item; self.batch_rows.append(item); r=self.batch_table.rowCount(); self.batch_table.insertRow(r); vals=[Path(p).name,f'{m.lufs:.2f}',f'{m.true_peak:.2f}',f'{m.lra:.2f}',str(m.clipping),str(s)];
        for c,v in enumerate(vals):self.batch_table.setItem(r,c,QTableWidgetItem(v))
    def batch_csv(self):
        if not self.batch_rows:return
        out,_=QFileDialog.getSaveFileName(self,'Save batch CSV','','CSV (*.csv)');
        if out:
            with open(out,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['File','LUFS','True Peak','LRA','Clipping','Score']); [w.writerow([Path(p).name,m.lufs,m.true_peak,m.lra,m.clipping,s]) for p,m,s in self.batch_rows]
    def repair(self):
        if not self.path:return
        out,_=QFileDialog.getSaveFileName(self,'Save repaired WAV','','WAV (*.wav)');
        if out:
            try: repair_audio(self.path,out,self.profile.currentText(),self.dc.isChecked(),self.hp.value(),self.trim.isChecked()); self.repaired_path=out; self.ab.setText(f'A/B ready • A: {Path(self.path).name} • B: {Path(out).name}'); QMessageBox.information(self,'Repair','Repair export completed. B is now available for A/B playback.')
            except Exception as e: self.error(str(e))

def main():
    app=QApplication(sys.argv); w=Main(); w.show(); sys.exit(app.exec())
