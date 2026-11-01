# Phase 4 – Subscription & Licensing Management

## Goal

Introduce account-level subscriptions and enforce subscription validity alongside the Phase 3 product entitlements. This phase starts with administrator-managed subscriptions; payment gateway integration is explicitly out of scope.

## Scope

1. Super Admin creates, updates, activates, and deactivates subscription plans.
2. Super Admin assigns, renews, upgrades, downgrades, and cancels subscriptions for accounts.
3. Account Admin can view their own account's current subscription and subscription history, but cannot change the plan directly.
4. The API validates subscription status and date range before allowing account product access.
5. Subscription changes are recorded in an immutable history/audit table.
6. Existing account-level product enablement and user-level product assignments remain separate gates.

## Proposed data model

### subscription_plans

- id: UUID primary key
- code: unique plan code
- name: plan display name
- description: nullable text
- billing_interval: monthly | yearly | lifetime
- price: decimal(12, 2), default 0
- currency: 3-character ISO currency code, default INR
- is_active: boolean
- created_at, updated_at

### subscription_plan_products

Defines which products a plan includes.

- id: UUID primary key
- plan_id: FK -> subscription_plans.id
- product_id: FK -> products.id
- unique(plan_id, product_id)

### account_subscriptions

Stores the current and historical subscription records for an account.

- id: UUID primary key
- account_id: FK -> accounts.account_id
- plan_id: FK -> subscription_plans.id
- status: trial | active | past_due | expired | cancelled
- starts_at: datetime
- ends_at: nullable datetime (null for lifetime)
- auto_renew: boolean, default false
- assigned_by: nullable UUID of the Super Admin
- notes: nullable text
- created_at, updated_at

Only one non-cancelled, non-expired current subscription should be effective for an account at a time. Enforce this in the service layer with a transaction; do not rely only on a database uniqueness constraint.

### subscription_history

Append-only record of subscription lifecycle changes.

- id: UUID primary key
- account_subscription_id: FK -> account_subscriptions.id
- account_id: FK -> accounts.account_id
- action: created | renewed | upgraded | downgraded | cancelled | expired
- previous_plan_id: nullable FK -> subscription_plans.id
- new_plan_id: nullable FK -> subscription_plans.id
- previous_status: nullable string
- new_status: string
- effective_at: datetime
- performed_by: nullable UUID
- notes: nullable text
- created_at

## Access rule

An account may access a product only when all conditions are true:

1. The account is active and not deleted.
2. The account has an active subscription whose start/end dates are valid.
3. The product is included in that subscription plan.
4. The product is enabled and unexpired in account_products.
5. For a normal user, the product is also assigned and enabled in user_products.
6. The product itself is active.

Super Admin access remains governed by the existing platform-level authorization rules.

## Proposed API

### Plans (Super Admin only)

- POST /api/subscriptions/plans
- GET /api/subscriptions/plans
- GET /api/subscriptions/plans/{plan_id}
- PATCH /api/subscriptions/plans/{plan_id}

### Account subscriptions

- POST /api/subscriptions/accounts/{account_id} – assign a plan (Super Admin)
- GET /api/subscriptions/accounts/{account_id} – current subscription (Super Admin; Account Admin for own account)
- GET /api/subscriptions/accounts/{account_id}/history – history (Super Admin; Account Admin for own account)
- PATCH /api/subscriptions/accounts/{account_id}/renew – renew (Super Admin)
- PATCH /api/subscriptions/accounts/{account_id}/change-plan – upgrade/downgrade (Super Admin)
- PATCH /api/subscriptions/accounts/{account_id}/cancel – cancel (Super Admin)

## Implementation sequence

1. Add SQLAlchemy models and register them with the application's model metadata/import path.
2. Add Pydantic schemas.
3. Add repositories, services, controllers, and routers following the existing layered architecture.
4. Add a SQL migration script compatible with the project's current migration approach.
5. Add subscription validation to the central product-access service so the checks are not duplicated across endpoints.
6. Add endpoint and access-control tests, including expiry and cross-account cases.
7. Document local migration and API test steps.

## Explicitly out of scope for this first iteration

- Payment gateway / checkout / webhook integration.
- Automatic charging and payment retries.
- Tax invoices and refunds.
- Self-service plan purchase by Account Admin.

## Open implementation decision

The initial plan supports administrator-managed assignment with no payment collection. A future payment phase can add gateway references and webhook-driven subscription state transitions without changing the core account/product access model.
