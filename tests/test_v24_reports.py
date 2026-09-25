from types import SimpleNamespace
from castwise_audio_doctor.report_center import summarize,write_csv,write_json,write_html

def sample():
    return [SimpleNamespace(source="a.wav",output="a_repaired.wav",status="PASS",score_before=70,score_after=95,lufs_before=-18,lufs_after=-14,peak_before=-.5,peak_after=-1,message="ok"),
            SimpleNamespace(source="b.wav",output="",status="FAIL",score_before=60,score_after=55,lufs_before=-20,lufs_after=-19,peak_before=0,peak_after=0,message="bad")]

def test_summary():
    s=summarize(sample()); assert s["total"]==2 and s["passed"]==1 and s["failed"]==1

def test_report_exports(tmp_path):
    rs=sample()
    for ext,fn in [("csv",write_csv),("json",write_json),("html",write_html)]:
        p=tmp_path/f"report.{ext}"; fn(rs,p); assert p.exists() and p.stat().st_size>0
