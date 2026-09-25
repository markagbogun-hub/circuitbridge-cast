from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List

@dataclass
class DeliveryProfile:
    name: str
    version: str = "1.0"
    target_lufs: float = -14.0
    loudness_tolerance: float = 1.0
    max_true_peak_approx: float = -1.0
    max_clipping_samples: int = 0
    max_silence_seconds: float = 3.0
    min_score: float = 70.0
    allowed_sample_rates: Optional[List[int]] = None
    allowed_channels: Optional[List[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def loudness_min(self):
        return self.target_lufs - self.loudness_tolerance

    @property
    def loudness_max(self):
        return self.target_lufs + self.loudness_tolerance


BUILTIN_PROFILES = {
    "Radio": DeliveryProfile(
        "Radio", target_lufs=-14.0, loudness_tolerance=1.0,
        max_true_peak_approx=-1.0, max_clipping_samples=0,
        max_silence_seconds=3.0, min_score=75.0,
        allowed_sample_rates=[44100, 48000], allowed_channels=[1, 2]
    ),
    "Podcast": DeliveryProfile(
        "Podcast", target_lufs=-16.0, loudness_tolerance=1.5,
        max_true_peak_approx=-1.0, max_clipping_samples=0,
        max_silence_seconds=5.0, min_score=70.0,
        allowed_sample_rates=[44100, 48000], allowed_channels=[1, 2]
    ),
    "Streaming": DeliveryProfile(
        "Streaming", target_lufs=-14.0, loudness_tolerance=1.0,
        max_true_peak_approx=-1.0, max_clipping_samples=0,
        max_silence_seconds=4.0, min_score=70.0,
        allowed_sample_rates=[44100, 48000], allowed_channels=[1, 2]
    ),
    "Broadcast Safe": DeliveryProfile(
        "Broadcast Safe", target_lufs=-23.0, loudness_tolerance=1.0,
        max_true_peak_approx=-1.0, max_clipping_samples=0,
        max_silence_seconds=2.0, min_score=80.0,
        allowed_sample_rates=[48000], allowed_channels=[1, 2]
    ),
}

def get_profile(name: str) -> DeliveryProfile:
    return BUILTIN_PROFILES.get(name, BUILTIN_PROFILES["Radio"])

def profile_names():
    return list(BUILTIN_PROFILES.keys())
