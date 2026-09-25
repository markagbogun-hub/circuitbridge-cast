# Castwise Audio Doctor 3.1.0 — Commercial Delivery Engine

## Headline upgrade
A production delivery pipeline now performs source analysis, non-destructive repair/normalization, post-delivery verification, SHA-256 hashing, and machine-readable delivery manifests.

## Workflow
1. Open source audio.
2. Select a delivery profile.
3. Run Delivery Engine.
4. Castwise creates a verified WAV plus a JSON delivery manifest.
5. The manifest records source/delivery hashes, measurements, checks, score, profile, timestamp, and PASS/FAIL status.

## Safety
The source file is never overwritten. Delivery output is written to a selected folder.
