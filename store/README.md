# Castwise Store + Customer Portal

A starter storefront and customer portal for Castwise Audio Doctor.

## Included
- Product landing page
- Checkout endpoint architecture
- Stripe Checkout integration
- Customer/license portal
- License download endpoint
- Installer download endpoint
- Webhook architecture
- SQLite development database

## Production
Set:
CASTWISE_LICENSE_API
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
CASTWISE_STORE_SECRET

The checkout creates a Stripe Checkout Session. The webhook should be connected to the
license server after successful payment. Never put Stripe secret keys in browser code.
