"""v2.5 integrated repair controls."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QDoubleSpinBox,QLabel,QGroupBox,QFormLayout

class RepairControls(QWidget):
    operationRequested=Signal(str,object)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.gain=QDoubleSpinBox(); self.gain.setRange(-24,24); self.gain.setSingleStep(.5); self.gain.setSuffix(" dB")
        self.hp=QDoubleSpinBox(); self.hp.setRange(20,500); self.hp.setValue(40); self.hp.setSuffix(" Hz")
        self.ceil=QDoubleSpinBox(); self.ceil.setRange(-6,0); self.ceil.setValue(-1); self.ceil.setSuffix(" dB")
        form=QFormLayout(); form.addRow("Gain",self.gain); form.addRow("High-pass",self.hp); form.addRow("Ceiling",self.ceil)
        b1=QPushButton("Preview Gain"); b1.clicked.connect(lambda:self.operationRequested.emit("gain",self.gain.value()))
        b2=QPushButton("Preview High-pass"); b2.clicked.connect(lambda:self.operationRequested.emit("highpass",self.hp.value()))
        b3=QPushButton("Remove DC"); b3.clicked.connect(lambda:self.operationRequested.emit("dc",None))
        b4=QPushButton("Preview Limiter"); b4.clicked.connect(lambda:self.operationRequested.emit("limiter",self.ceil.value()))
        b5=QPushButton("Trim Selection"); b5.clicked.connect(lambda:self.operationRequested.emit("trim",None))
        b6=QPushButton("Delete Selection"); b6.clicked.connect(lambda:self.operationRequested.emit("delete",None))
        u=QPushButton("Undo"); u.clicked.connect(lambda:self.operationRequested.emit("undo",None))
        r=QPushButton("Redo"); r.clicked.connect(lambda:self.operationRequested.emit("redo",None))
        box=QGroupBox("Repair Studio"); v=QVBoxLayout(box); v.addLayout(form)
        for b in (b1,b2,b3,b4,b5,b6,u,r): v.addWidget(b)
        self.status=QLabel("Select a timeline region, preview a repair, then export.")
        v.addWidget(self.status)
        main=QVBoxLayout(self); main.addWidget(box)
