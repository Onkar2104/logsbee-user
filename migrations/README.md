# Account multi-tenancy migration

## Existing MySQL database

1. Take a full database backup.
2. Confirm that the existing `user_roles` table has the old unique index named `name`. The migration drops that index and replaces it with account-scoped uniqueness.
3. Run the migration exactly once, before deploying the updated application:

```bash
mysql -u YOUR_DB_USER -p YOUR_DATABASE < migrations/001_account_multi_tenancy_mysql.sql
```

4. Review the resulting ownership:

```sql
SELECT id, email, account_id, user_role_id FROM users;
SELECT id, name, account_id, is_system_role FROM user_roles;
SELECT account_id, name FROM accounts;
```

The migration creates one temporary organization named `Migrated account - update organization name` and assigns all existing users except users with the `Super admin` role to it. This preserves the current single-organization data as one tenant. Update that account's name and contact details after migration.

Existing users with the `Super admin` role remain platform users with `account_id = NULL`. If no Super Admin user exists yet, create/promote one through a controlled database operation; do not expose a public registration endpoint for this role.

## New database

For a brand-new database, the application imports all models and `Base.metadata.create_all()` creates the tables. The SQL migration is intended only for an existing database.

## Account user creation API

An authenticated Account Admin can create users only inside their own account:

`POST /api/users/`

Omit `user_role_id` to assign the default system `user` role. A supplied role must be the global system `user` role or a custom role belonging to the same account. Account Admins cannot assign the platform `Super admin` or system `admin` role.

## Important deployment note

`create_all()` does not alter existing tables. Do not deploy the updated app against an old database until the migration has completed successfully. Run the migration on a backup/staging copy first.


## Phase 2: Role-Based Access Control (RBAC)

After Phase 1 is applied, back up the database and run:

```sql
SOURCE migrations/002_rbac_mysql.sql;
```

The application seeds the permission catalogue at startup. The initial permission codes are:

- `users.view`
- `users.create`
- `users.update`
- `users.delete`
- `roles.view`
- `roles.manage`

For a new database, `Base.metadata.create_all()` creates the RBAC tables because the models are imported in `main.py`. The SQL migration is provided for explicit/versioned deployment and should be run only once.

### RBAC API

All endpoints require a valid access token:

- `GET /api/roles/` — list account custom roles (requires `roles.view`)
- `GET /api/roles/permissions` — list the permission catalogue (requires `roles.view`)
- `POST /api/roles/` — create a custom role and assign permissions (requires `roles.manage`)
- `PATCH /api/roles/{role_id}` — update a custom role (requires `roles.manage`)
- `DELETE /api/roles/{role_id}` — soft-delete an unassigned custom role (requires `roles.manage`)

Account Admins and Platform Super Admins retain their administrative bypass. Custom roles are account-scoped. A role cannot be read or modified across account boundaries.


## Public VoiceDocs organization registration

- `POST /api/accounts/register` is the public endpoint for creating an organization and its initial Account Admin.
- The organization email is verified first through `POST /api/accounts/register/verify-account-email` with `{"account_id":"...","otp":"123456"}`.
- Only after organization email verification, the backend sends the Admin email OTP. The Admin verifies it through `POST /api/users/{user_id}/verification/email` with `{"otp":"123456"}`.
- `POST /api/accounts/register/resend-otp` accepts `account_id` and `verification_type` (`account` or `admin`) to resend the appropriate OTP. Admin OTP resend is blocked until the organization email is verified.
- The organization is activated only after both `accounts.is_email_verified` and `users.is_email_verified` are true. Existing `accounts.is_active` remains false until the second verification succeeds.
- The `accounts.is_email_verified` column is added by `migrations/004_account_email_verification_mysql.sql`. Existing organizations receive the default value `1` (already verified); new public registrations explicitly set it to `0`.
- Account users cannot access VoiceDocs until both email verifications are complete. OTP expiry, attempt limits, resend cooldown, and rate limits use the existing verification configuration.

For an existing MySQL database, back up the database and run this migration once before deploying the updated backend:

```bash
mysql -u YOUR_DB_USER -p YOUR_DATABASE < migrations/004_account_email_verification_mysql.sql
```

For a new database, the SQLAlchemy model creates the column through `Base.metadata.create_all()`; do not run this migration if the column already exists.


## Phase 3: Dedicated user settings and 2FA

The Logsbee User service owns account-level two-factor authentication. The setting is stored in the dedicated `user_settings` table; it is not stored in the VoiceDocs database.

For an existing MySQL database:

1. Back up the database.
2. Deploy the updated model/code only after the migration is ready.
3. Run the migration once:

```bash
mysql -u YOUR_DB_USER -p YOUR_DATABASE < migrations/005_user_settings_mysql.sql
```

The migration creates one settings row per existing user, copies the previous `users.is_two_factor_authenticated` value into `user_settings.two_factor_enabled`, and removes the old column. The application continues exposing `is_two_factor_authenticated` in the user profile response as a compatibility property backed by the settings table.

For a new database, `Base.metadata.create_all()` creates `user_settings` from the imported model.
