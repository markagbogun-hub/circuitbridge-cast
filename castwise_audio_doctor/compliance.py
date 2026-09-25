from dataclasses import dataclass, asdict
from typing import List, Dict, Any

from .delivery_profiles import DeliveryProfile

@dataclass
class CheckItem:
    name: str
    status: str
    measured: object
    target: object
    reason: str = ""

    def to_dict(self):
        return asdict(self)

@dataclass
class DeliveryCheck:
    profile: str
    status: str
    checks: List[CheckItem]
    reasons: List[str]
    report_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checks"] = [c.to_dict() for c in self.checks]
        return d

def _status(ok, warn=False):
    return "PASS" if ok else ("WARN" if warn else "FAIL")

def evaluate(qc, profile: DeliveryProfile) -> DeliveryCheck:
    checks = []
    reasons = []

    lufs = float(getattr(qc, "lufs_i", getattr(qc, "lufs", -999)))
    lo, hi = profile.loudness_min, profile.loudness_max
    l_ok = lo <= lufs <= hi
    l_warn = (lo - 1.0 <= lufs <= hi + 1.0)
    s = _status(l_ok, l_warn)
    checks.append(CheckItem("Integrated Loudness", s, round(lufs, 2), f"{profile.target_lufs:.1f} ± {profile.loudness_tolerance:.1f} LUFS"))
    if s != "PASS":
        reasons.append(f"Loudness is {lufs:.2f} LUFS; target is {profile.target_lufs:.1f} ± {profile.loudness_tolerance:.1f} LUFS.")

    peak = float(getattr(qc, "true_peak", getattr(qc, "true_peak_approx", -999)))
    p_ok = peak <= profile.max_true_peak_approx
    p_warn = peak <= profile.max_true_peak_approx + 0.2
    s = _status(p_ok, p_warn)
    checks.append(CheckItem("True Peak (approx.)", s, round(peak, 2), f"≤ {profile.max_true_peak_approx:.1f} dBTP"))
    if s != "PASS":
        reasons.append(f"Peak is {peak:.2f} dBTP; limit is {profile.max_true_peak_approx:.1f} dBTP.")

    clips = int(getattr(qc, "clipping_samples", getattr(qc, "clips", 0)))
    c_ok = clips <= profile.max_clipping_samples
    c_warn = clips <= profile.max_clipping_samples + 10
    s = _status(c_ok, c_warn)
    checks.append(CheckItem("Clipping Samples", s, clips, f"≤ {profile.max_clipping_samples}"))
    if s != "PASS":
        reasons.append(f"{clips} clipping samples detected; limit is {profile.max_clipping_samples}.")

    silence = float(getattr(qc, "max_silence_seconds", getattr(qc, "silence_seconds", 0.0)))
    si_ok = silence <= profile.max_silence_seconds
    si_warn = silence <= profile.max_silence_seconds * 1.25
    s = _status(si_ok, si_warn)
    checks.append(CheckItem("Longest Silence", s, round(silence, 2), f"≤ {profile.max_silence_seconds:.1f} s"))
    if s != "PASS":
        reasons.append(f"Longest silence is {silence:.2f}s; limit is {profile.max_silence_seconds:.1f}s.")

    score = float(getattr(qc, "health_score", getattr(qc, "score", 0)))
    sc_ok = score >= profile.min_score
    sc_warn = score >= profile.min_score - 5
    s = _status(sc_ok, sc_warn)
    checks.append(CheckItem("Health Score", s, round(score, 1), f"≥ {profile.min_score:.0f}"))
    if s != "PASS":
        reasons.append(f"Health score is {score:.1f}; minimum is {profile.min_score:.0f}.")

    sr = getattr(qc, "sample_rate", getattr(qc, "samplerate", None))
    if profile.allowed_sample_rates and sr is not None:
        ok = int(sr) in profile.allowed_sample_rates
        s = _status(ok, False)
        checks.append(CheckItem("Sample Rate", s, sr, ", ".join(map(str, profile.allowed_sample_rates))))
        if not ok:
            reasons.append(f"Sample rate {sr} Hz is not allowed by the {profile.name} profile.")

    channels = getattr(qc, "channels", None)
    if profile.allowed_channels and channels is not None:
        ok = int(channels) in profile.allowed_channels
        s = _status(ok, False)
        checks.append(CheckItem("Channels", s, channels, ", ".join(map(str, profile.allowed_channels))))
        if not ok:
            reasons.append(f"{channels} channel(s) are not allowed by the {profile.name} profile.")

    statuses = [c.status for c in checks]
    overall = "FAIL" if "FAIL" in statuses else ("WARN" if "WARN" in statuses else "PASS")
    return DeliveryCheck(profile.name, overall, checks, reasons)
