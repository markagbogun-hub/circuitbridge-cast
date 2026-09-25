# Castwise licensing deployment

1. Deploy `license_server` behind HTTPS.
2. Set `CASTWISE_LICENSE_ADMIN_KEY` using your hosting provider's secret store.
3. Start with `uvicorn main:app --host 0.0.0.0 --port 8000`.
4. Generate/read the Ed25519 public key from the server and place its base64 value in the desktop build as `CASTWISE_PUBLIC_KEY_B64`.
5. Do NOT ship the private key.
6. Put the API behind HTTPS and rate limiting before customer use.
7. Connect checkout/webhook logic to `/v1/licenses/issue`.
8. For production, migrate SQLite to PostgreSQL and add authenticated customer accounts, audit logs, backups and revocation policy.
