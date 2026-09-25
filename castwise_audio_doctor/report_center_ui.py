"""v2.5 Batch Report Center widget."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QTableWidget,QTableWidgetItem,QFileDialog
from .report_center import summarize,write_csv,write_json,write_html,write_pdf

class ReportCenter(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.results=[]
        self.summary=QLabel("No batch results loaded.")
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["File","Status","Before","After","LUFS Before","LUFS After"])
        self.csv=QPushButton("CSV"); self.csv.clicked.connect(lambda:self.export("csv"))
        self.json=QPushButton("JSON"); self.json.clicked.connect(lambda:self.export("json"))
        self.html=QPushButton("HTML"); self.html.clicked.connect(lambda:self.export("html"))
        self.pdf=QPushButton("PDF"); self.pdf.clicked.connect(lambda:self.export("pdf"))
        top=QHBoxLayout(); [top.addWidget(b) for b in (self.csv,self.json,self.html,self.pdf)]
        l=QVBoxLayout(self); l.addWidget(self.summary); l.addLayout(top); l.addWidget(self.table)

    def set_results(self,results):
        self.results=results; s=summarize(results)
        self.summary.setText(f"Total {s['total']} | PASS {s['passed']} | WARN {s['warned']} | FAIL/ERROR {s['failed']} | Average {s['average_score']}")
        self.table.setRowCount(len(results))
        for i,r in enumerate(results):
            vals=[str(r.source),r.status,str(r.score_before),str(r.score_after),
                  "" if r.lufs_before is None else f"{r.lufs_before:.2f}",
                  "" if r.lufs_after is None else f"{r.lufs_after:.2f}"]
            for j,v in enumerate(vals): self.table.setItem(i,j,QTableWidgetItem(v))

    def export(self,kind):
        if not self.results:return
        ext={"csv":"csv","json":"json","html":"html","pdf":"pdf"}[kind]
        p,_=QFileDialog.getSaveFileName(self,"Export Report","","*."+ext)
        if not p:return
        {"csv":write_csv,"json":write_json,"html":write_html,"pdf":write_pdf}[kind](self.results,p)
