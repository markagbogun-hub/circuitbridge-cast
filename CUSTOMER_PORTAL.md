# v1.6 Customer Portal

Implemented:
- Passwordless email-code login architecture
- Customer sessions
- Customer license records
- Protected installer download
- Protected license download
- Stripe checkout webhook fulfillment
- Automatic license issuance hook to the Castwise License Server

Production hardening required:
- Send login codes through an email provider.
- Store sessions securely behind HTTPS.
- Use PostgreSQL.
- Queue webhook fulfillment jobs and retry failures.
- Fetch and verify the full signed license payload from the license service.
- Add customer terms, privacy and refund pages.
- Add rate limiting and bot protection.
