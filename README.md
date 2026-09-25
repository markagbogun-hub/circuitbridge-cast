# Castwise Audio Doctor v1.3.0

Commercial-oriented Windows audio QC and repair foundation by Castwise Studio.

## Highlights
- BS.1770-style integrated loudness workflow using pyloudnorm
- Integrated, short-term and momentary LUFS timeline
- True-peak approximation with configurable oversampling
- Peak/RMS/dynamic range/LRA-style statistics
- Clipping and silence detection
- Stereo phase correlation and width
- Waveform and loudness history visualization
- Radio, Podcast and Streaming profiles
- Batch analysis with CSV export
- PDF engineering report
- Non-destructive normalization export
- Professional PySide6 desktop UI
- Windows GitHub Actions packaging

## Important
This release is a commercial engineering foundation, not a certified compliance instrument. Final EBU/ITU compliance should be validated against independent reference material before making regulatory claims.

## Commercial packaging
This release adds an Inno Setup recipe and GitHub Actions workflow that produces a Windows Setup.exe. The installer is not code-signed by default; signing should be performed with Castwise Studio's Authenticode certificate before public distribution.

## Licensing
A 14-day trial framework and signed-license-file architecture are included. Production public-key verification and the website licensing backend should be connected before commercial sale.


## v2.6 Professional Repair Studio
- Non-destructive repair session with undo/redo
- Selection-aware gain
- Trim/delete selected regions
- Silence detection
- DC offset removal
- High-pass filtering
- Limiter/ceiling preview
- PCM-24 export


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
