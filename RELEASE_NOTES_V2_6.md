# Castwise Audio Doctor 2.6.0

Commercial hardening release focused on release reliability, report-center compatibility, and packaging consistency.

### Fixed
- Batch QC Report Center syntax defect caused by an incorrectly serialized import line.
- Report exports failing when batch results are namespace/object instances instead of dataclasses.
- Repair regression test now correctly addresses a selected stereo channel.

### Verified
- 25 automated tests passing.
- Python package compiles successfully with `python -m compileall`.

### Commercial note
This release remains an engineering QC/repair application. Delivery profiles are configurable engineering checks and are not a substitute for independent regulatory certification.
