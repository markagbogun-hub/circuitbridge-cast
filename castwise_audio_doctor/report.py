from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from .engine import PROFILES, score, recommendations

def make_report(path, metrics, profile, output):
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(str(output),pagesize=A4,rightMargin=36,leftMargin=36,topMargin=36,bottomMargin=36)
    story=[Paragraph("Castwise Audio Doctor",styles["Title"]),
           Paragraph("Professional Audio QC Report",styles["Heading2"]),
           Spacer(1,12)]
    s=score(metrics,profile)
    story.append(Paragraph(f"Health Score: <b>{s}/100</b>",styles["Heading2"]))
    story.append(Paragraph(f"Profile: {profile} | Target: {PROFILES[profile]['lufs']:.1f} LUFS / {PROFILES[profile]['tp']:.1f} dBTP",styles["Normal"]))
    story.append(Spacer(1,12))
    rows=[["Metric","Value"],
          ["File",metrics.file],["Duration",f"{metrics.duration:.2f} s"],
          ["Sample rate",f"{metrics.sr} Hz"],["Channels",str(metrics.channels)],
          ["Integrated LUFS",f"{metrics.lufs:.2f}"],["True peak",f"{metrics.true_peak:.2f} dBTP"],
          ["Peak",f"{metrics.peak:.2f} dBFS"],["RMS",f"{metrics.rms:.2f} dBFS"],
          ["Dynamic range",f"{metrics.dynamic:.2f} dB"],["LRA",f"{metrics.lra:.2f} LU"],
          ["Clipping",f"{metrics.clipping} samples ({metrics.clipping_pct:.3f}%)"],
          ["Silence",f"{metrics.silence_pct:.2f}%"],["DC offset",f"{metrics.dc:.5f}"],
          ["Phase correlation",f"{metrics.phase:.3f}"],["Stereo width",f"{metrics.width:.3f}"]]
    t=Table(rows,colWidths=[170,330])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,colors.grey),
                            ("BACKGROUND",(0,0),(-1,0),colors.lightgrey),
                            ("VALIGN",(0,0),(-1,-1),"TOP")]))
    story.append(t); story.append(Spacer(1,16))
    story.append(Paragraph("Engineer Recommendations",styles["Heading2"]))
    for x in recommendations(metrics,profile):
        story.append(Paragraph("• "+x,styles["Normal"]))
    doc.build(story)
