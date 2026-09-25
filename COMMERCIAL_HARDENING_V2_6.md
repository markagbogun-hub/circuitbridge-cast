# Castwise Audio Doctor 2.6.0 — Commercial Hardening

## What changed

- Fixed a release-blocking syntax defect in the Batch QC Report Center.
- Report exports now accept dataclass results, dictionaries, and namespace/object results safely.
- Preserved stereo audio as a two-dimensional PCM buffer in `RepairSession`; corrected the regression test to validate a channel explicitly.
- Updated application and Windows installer version to 2.6.0.
- Added a repeatable automated verification baseline: 25 tests passing.
- Kept compliance wording conservative: the product performs engineering QC checks and does not claim regulatory certification.

## Commercial-readiness priorities after this release

1. Code-sign the Windows installer and executable.
2. Add crash logging with opt-in diagnostics and a privacy notice.
3. Add persistent application settings and per-user delivery-profile management.
4. Add deterministic project/session files so QC work can be reopened and audited.
5. Add audio fixture tests for LUFS, true-peak approximation, clipping, silence and sample-rate/channel compliance.
6. Add signed license verification against the production licensing service before public sale.
7. Run Windows 10/11 packaging tests on clean machines and verify install, upgrade and uninstall paths.
8. Add release checksums and a signed release manifest.
