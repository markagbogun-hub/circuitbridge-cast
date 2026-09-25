"""QC marker panel for the v2.5 workstation."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QListWidget,QListWidgetItem,QLabel

class MarkerPanel(QWidget):
    markerActivated=Signal(int)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.list=QListWidget(); self.count=QLabel("0 QC markers")
        l=QVBoxLayout(self); l.addWidget(self.count); l.addWidget(self.list)
        self.list.itemDoubleClicked.connect(self._activate)
    def set_markers(self,markers):
        self.list.clear()
        for i,m in enumerate(markers):
            t=getattr(m,"time",m.get("time",0) if isinstance(m,dict) else 0)
            k=getattr(m,"kind",m.get("kind","QC") if isinstance(m,dict) else "QC")
            d=getattr(m,"duration",m.get("duration",0) if isinstance(m,dict) else 0)
            item=QListWidgetItem(f"{t:8.2f}s   {k.upper():8}   {d:.2f}s")
            item.setData(32,i); self.list.addItem(item)
        self.count.setText(f"{len(markers)} QC markers")
    def _activate(self,item):
        self.markerActivated.emit(item.data(32))
