"""Commercial delivery pipeline for Castwise Audio Doctor 3.1.

The engine is deliberately deterministic: analyze source, apply the selected
non-destructive repair/normalization chain, re-analyze the delivered file,
and emit a machine-readable manifest.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, shutil
from .engine import analyze, repair_audio, score
from .delivery_profiles import get_profile


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def evaluate_delivery(metrics, profile):
    checks = {
        "integrated_loudness": profile.loudness_min <= metrics.lufs <= profile.loudness_max,
        "true_peak": metrics.true_peak <= profile.max_true_peak_approx,
        "clipping": metrics.clipping <= profile.max_clipping_samples,
        "sample_rate": not profile.allowed_sample_rates or metrics.sr in profile.allowed_sample_rates,
        "channels": not profile.allowed_channels or metrics.channels in profile.allowed_channels,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    passed = all(checks.values()) and score(metrics, profile.name) >= profile.min_score
    return checks, passed


def deliver(path, output_dir, profile_name="Radio", *, dc_remove=True, highpass_hz=0.0):
    """Create a verified delivery package and return its manifest dictionary."""
    source = Path(path).resolve()
    outdir = Path(output_dir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    profile = get_profile(profile_name)
    source_metrics = analyze(source)

    target = outdir / f"{source.stem}_CASTWISE.wav"
    repair_audio(str(source), str(target), profile.name, dc_remove, highpass_hz, False)
    delivered_metrics = analyze(target)
    checks, passed = evaluate_delivery(delivered_metrics, profile)

    manifest = {
        "product": "Castwise Audio Doctor",
        "pipeline": "Commercial Delivery Engine",
        "version": "3.1.0",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "profile": profile.to_dict(),
        "source": {"path": str(source), "sha256": sha256_file(source), "metrics": asdict(source_metrics)},
        "delivery": {"path": str(target), "sha256": sha256_file(target), "metrics": asdict(delivered_metrics)},
        "checks": checks,
        "score": score(delivered_metrics, profile.name),
        "status": "PASS" if passed else "FAIL",
    }
    manifest_path = outdir / f"{source.stem}_CASTWISE_delivery.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
