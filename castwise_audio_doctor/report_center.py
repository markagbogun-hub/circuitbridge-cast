"""Castwise Audio Doctor commercial batch QC report center."""
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
import csv, json, html

def _to_dict(obj):
    """Normalize dataclass, mapping, or namespace-like result objects."""
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return dict(obj)
    return dict(vars(obj))

def summarize(results):
    total=len(results)
    passed=sum(getattr(r,"status","")=="PASS" for r in results)
    warned=sum(getattr(r,"status","")=="WARN" for r in results)
    failed=sum(getattr(r,"status","") in ("FAIL","ERROR") for r in results)
    scores=[r.score_after for r in results if r.score_after is not None]
    return {"generated_utc":datetime.now(timezone.utc).isoformat(),
            "total":total,"passed":passed,"warned":warned,"failed":failed,
            "average_score":round(sum(scores)/len(scores),1) if scores else None}

def failure_reason(r):
    reasons=[]
    if r.status=="ERROR": return r.message
    if r.score_after is not None and r.score_after<70: reasons.append("QC score below delivery threshold")
    if r.lufs_after is not None and abs(r.lufs_after+14)>2: reasons.append("Loudness differs materially from Radio target")
    if r.peak_after is not None and r.peak_after>-1: reasons.append("True-peak approximation exceeds -1 dBTP ceiling")
    return "; ".join(reasons) if reasons else "No major delivery flag"

def write_csv(results,path):
    fields=["source","output","status","score_before","score_after","lufs_before","lufs_after",
            "peak_before","peak_after","message","failure_reason"]
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in results:
            d=_to_dict(r); d["failure_reason"]=failure_reason(r); w.writerow({k:d.get(k,"") for k in fields})

def write_json(results,path):
    payload={"summary":summarize(results),
             "items":[dict(_to_dict(r),failure_reason=failure_reason(r)) for r in results]}
    Path(path).write_text(json.dumps(payload,indent=2),encoding="utf-8")

def write_html(results,path,title="Castwise Audio Doctor — Batch QC Report"):
    s=summarize(results)
    rows=[]
    for r in results:
        cls=str(r.status).lower()
        rows.append(f"<tr class='{cls}'><td>{html.escape(Path(r.source).name)}</td>"
                    f"<td>{html.escape(r.status)}</td><td>{r.score_before}</td><td>{r.score_after}</td>"
                    f"<td>{'' if r.lufs_before is None else f'{r.lufs_before:.2f}'}</td>"
                    f"<td>{'' if r.lufs_after is None else f'{r.lufs_after:.2f}'}</td>"
                    f"<td>{html.escape(failure_reason(r))}</td></tr>")
    doc=f"""<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>
<style>
body{{font-family:Arial,sans-serif;margin:32px;background:#111;color:#eee}}
.card{{display:inline-block;padding:18px;margin:6px;background:#222;border-radius:10px}}
table{{width:100%;border-collapse:collapse;margin-top:25px}}th,td{{padding:10px;border-bottom:1px solid #333;text-align:left}}
.pass{{background:#14351f}}.warn{{background:#403515}}.fail,.error{{background:#401515}}
</style></head><body><h1>{html.escape(title)}</h1>
<p>Generated {html.escape(s["generated_utc"])}</p>
<div class='card'>Total <b>{s["total"]}</b></div><div class='card'>PASS <b>{s["passed"]}</b></div>
<div class='card'>WARN <b>{s["warned"]}</b></div><div class='card'>FAIL/ERROR <b>{s["failed"]}</b></div>
<div class='card'>Average score <b>{s["average_score"]}</b></div>
<table><tr><th>File</th><th>Status</th><th>Before</th><th>After</th><th>LUFS Before</th><th>LUFS After</th><th>Delivery flag</th></tr>
{''.join(rows)}</table></body></html>"""
    Path(path).write_text(doc,encoding="utf-8")

def write_pdf(results,path,title="Castwise Audio Doctor — Batch QC Report"):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(path,pagesize=landscape(A4),rightMargin=28,leftMargin=28,topMargin=28,bottomMargin=28)
    s=summarize(results)
    story=[Paragraph(title,styles["Title"]),
           Paragraph(f"Generated UTC: {s['generated_utc']}",styles["Normal"]),
           Spacer(1,10),
           Paragraph(f"Total: {s['total']} | PASS: {s['passed']} | WARN: {s['warned']} | FAIL/ERROR: {s['failed']} | Average score: {s['average_score']}",styles["Normal"]),
           Spacer(1,14)]
    data=[["File","Status","Before","After","LUFS B","LUFS A","Delivery flag"]]
    for r in results:
        data.append([Path(r.source).name,r.status,str(r.score_before),str(r.score_after),
                     "" if r.lufs_before is None else f"{r.lufs_before:.1f}",
                     "" if r.lufs_after is None else f"{r.lufs_after:.1f}",
                     failure_reason(r)])
    t=Table(data,repeatRows=1,colWidths=[150,55,45,45,50,50,310])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.black),("TEXTCOLOR",(0,0),(-1,0),colors.white),
                           ("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),7),
                           ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t); doc.build(story)
