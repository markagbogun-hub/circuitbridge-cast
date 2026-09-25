"""Broadcast QC presets for Castwise Audio Doctor v2."""
PRESETS = {
    "Radio": {"target_lufs": -14.0, "ceiling_dbtp": -1.0, "silence_db": -50.0},
    "Podcast": {"target_lufs": -16.0, "ceiling_dbtp": -1.0, "silence_db": -50.0},
    "Streaming": {"target_lufs": -14.0, "ceiling_dbtp": -1.0, "silence_db": -55.0},
    "Broadcast Safe": {"target_lufs": -23.0, "ceiling_dbtp": -1.0, "silence_db": -55.0},
}
def get_preset(name):
    if name not in PRESETS: raise KeyError(name)
    return dict(PRESETS[name])
