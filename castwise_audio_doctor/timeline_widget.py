"""Castwise Audio Doctor v2.5 interactive QC timeline widget."""
import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class QCTimelineWidget(QWidget):
    selectionChanged = Signal(float, float)
    positionChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio=None; self.sr=48000; self.duration=0.0
        self.markers=[]; self.zoom=1.0; self.position=0.0
        self._drag_start=None; self._selecting=False
        self.fig=Figure(figsize=(8,2.7)); self.ax=self.fig.add_subplot(111)
        self.canvas=FigureCanvas(self.fig)
        self.playhead=self.ax.axvline(0, linewidth=1)
        self.info=QLabel("No audio loaded")
        self.zoom_slider=QSlider(Qt.Horizontal); self.zoom_slider.setRange(1,100); self.zoom_slider.setValue(1)
        self.zoom_slider.valueChanged.connect(self._zoom)
        row=QHBoxLayout(); row.addWidget(QLabel("Zoom")); row.addWidget(self.zoom_slider)
        layout=QVBoxLayout(self); layout.addWidget(self.canvas); layout.addLayout(row); layout.addWidget(self.info)
        self.canvas.mpl_connect("button_press_event",self._press)
        self.canvas.mpl_connect("motion_notify_event",self._move)
        self.canvas.mpl_connect("button_release_event",self._release)
        self.canvas.mpl_connect("scroll_event",self._scroll)

    def set_audio(self,audio,sr,markers=None):
        self.audio=np.asarray(audio)
        if self.audio.ndim>1: self.audio=self.audio.mean(axis=1)
        self.sr=int(sr); self.duration=len(self.audio)/self.sr
        self.markers=list(markers or [])
        self.position=0.0; self._render()

    def _wave(self, start=0.0, end=None):
        end=self.duration if end is None else min(end,self.duration)
        a=int(max(0,start)*self.sr); b=int(end*self.sr)
        y=self.audio[a:b]
        if len(y)>6000:
            step=max(1,len(y)//6000)
            y=y[:len(y)//step*step].reshape(-1,step)
            y=np.vstack((y.min(axis=1),y.max(axis=1))).T.ravel()
        return np.linspace(start,end,len(y)),y

    def _render(self):
        self.ax.clear()
        if self.audio is None: self.canvas.draw(); return
        span=self.duration/max(1,self.zoom)
        center=self.position
        start=max(0,min(center-span/2,self.duration-span))
        end=min(self.duration,start+span)
        x,y=self._wave(start,end)
        self.ax.plot(x,y,linewidth=.7)
        for m in self.markers:
            t=getattr(m,"time",m.get("time",0) if isinstance(m,dict) else 0)
            kind=getattr(m,"kind",m.get("kind","") if isinstance(m,dict) else "")
            if start<=t<=end:
                self.ax.axvline(t,linewidth=1,alpha=.75)
        self.playhead=self.ax.axvline(self.position,linewidth=1.5)
        self.ax.set_xlim(start,end); self.ax.set_ylim(-1.05,1.05)
        self.ax.set_ylabel("Level"); self.ax.set_xlabel("Time (s)")
        self.fig.tight_layout()
        self.info.setText(f"{self.position:.2f}s / {self.duration:.2f}s   |   Zoom {self.zoom:.1f}x")
        self.canvas.draw_idle()

    def _zoom(self,v):
        self.zoom=max(1,v/5)
        self._render()

    def _scroll(self,e):
        if e.xdata is None: return
        self.position=max(0,min(self.duration,e.xdata))
        self._render(); self.positionChanged.emit(self.position)

    def _press(self,e):
        if e.xdata is None: return
        if e.button==1:
            self._drag_start=e.xdata; self._selecting=True

    def _move(self,e):
        if self._selecting and e.xdata is not None:
            self._render()
            a,b=sorted((self._drag_start,max(0,min(self.duration,e.xdata))))
            self.ax.axvspan(a,b,alpha=.25); self.canvas.draw_idle()

    def _release(self,e):
        if not self._selecting: return
        self._selecting=False
        if e.xdata is None: return
        a,b=sorted((self._drag_start,max(0,min(self.duration,e.xdata))))
        self.position=b
        self.selectionChanged.emit(a,b); self.positionChanged.emit(b); self._render()

    def jump_to_marker(self,index):
        if not (0<=index<len(self.markers)): return
        m=self.markers[index]
        t=getattr(m,"time",m.get("time",0) if isinstance(m,dict) else 0)
        self.position=float(t); self._render(); self.positionChanged.emit(self.position)
