# Castwise Audio Doctor 1.7.0

Customer account and automated purchase fulfillment foundation.

Payment -> webhook -> license issuance -> customer account -> protected downloads.

This is a production-oriented foundation. Email delivery, persistent database, HTTPS,
queue/retry, payment configuration and final license payload retrieval must be configured
before public launch.

## v2.6.0 Professional Playback & A/B
- Desktop playback transport using Qt Multimedia.
- Play original (A) and latest repaired/normalized export (B).
- Seek, pause and stop controls.
- Playback peak/RMS indicators tied to the QC history.
- A/B state shown in the UI.
- Repair and normalization exports automatically become B source.
- True-peak remains explicitly documented as an oversampled approximation.


## v2.6.0 — Professional Repair Studio
Released as a production-oriented repair workflow. Adds selection-aware editing, undo/redo, silence detection, DC removal, high-pass filtering, limiter preview and destructive export from an explicit repair session. True-peak remains an oversampled approximation unless separately validated.


## v2.6 Broadcast QC Workstation
Professional QC core with timeline model, visualizable silence/clipping markers, batch analysis, presets, JSON QC output, and re-QC oriented workflow.


## v2.6 Interactive Workstation
Interactive waveform timeline, zoom/scroll, region selection, QC marker navigation, marker panel, and standalone workstation window.


## v2.6 Integrated Repair + QC
Timeline selection is now connected to non-destructive Repair Studio controls, before/after QC metrics, undo/redo, and automatic re-QC after export.


## v2.6 Batch Repair & QC Automation
Batch queue, repeatable repair presets, rendered outputs, automatic re-QC, cancellation, CSV/JSON-ready results.


## v2.6 Professional Batch QC Report Center
Batch delivery dashboard with PASS/WARN/FAIL summaries, failure reasons, before/after metrics, and PDF/CSV/JSON/HTML report export.
