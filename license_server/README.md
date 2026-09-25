# Castwise License Server

Minimal production-oriented license API for Castwise Audio Doctor.

## Endpoints
- POST /v1/licenses/issue
- POST /v1/licenses/activate
- GET /v1/licenses/{license_id}
- POST /v1/licenses/{license_id}/revoke
- GET /health

Set `CASTWISE_LICENSE_ADMIN_KEY` before starting. The signing private key is generated
on first start and stored outside source control. In production, use a secrets manager
and a persistent database.

This reference implementation uses SQLite for the license ledger and Ed25519 signatures.
The private key never belongs in the desktop application.
