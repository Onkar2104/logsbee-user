# Phase 3 — Product access

Apply only after migrations 001 and 002. Back up the database first.

For an existing MySQL database:

```bash
mysql -u YOUR_DB_USER -p YOUR_DATABASE < migrations/003_product_access_mysql.sql
```

For a new database, the application imports all Phase 3 models before `Base.metadata.create_all()`.

## API

All endpoints require a valid access token.

### Platform Super Admin

- `GET /api/products/` — list catalogue
- `POST /api/products/` — create product
- `PATCH /api/products/{product_id}` — update product or deactivate it
- `GET /api/products/accounts/{account_id}` — view account entitlements
- `PUT /api/products/accounts/{account_id}` — replace account entitlements

Example product:

```json
{"code":"HRM","name":"Human Resource Management","description":"HR and employee management"}
```

Example account assignment (PUT replaces the complete set):

```json
{"product_ids":["PRODUCT-UUID"]}
```

### Account Admin

- `GET /api/products/users/{user_id}` — view product access for a user in their own account
- `PUT /api/products/users/{user_id}` — replace that user's product access

The Account Admin can assign only products already enabled for their account. A request with an empty `product_ids` list revokes all product assignments for that user.

## Enforcing access in product APIs

Use the dependency helpers from `core.product_access` inside each product-specific router/service:

- `require_product_access(db, current_user, "HRM")` checks global product status and account entitlement.
- `require_user_product_access(db, current_user, "HRM")` checks both account entitlement and the current user's assignment.

The platform Super Admin bypasses tenant entitlements. Do not trust account IDs supplied by the frontend for user access; the service derives the tenant from the authenticated user.

## Notes

This phase does not implement subscription plans, billing, pricing, seats, or automatic expiry jobs. `expires_at` is an optional account entitlement cutoff checked at request time. Disabling a product globally blocks it for every tenant.
