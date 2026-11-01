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

## Account creation API

Only an authenticated platform Super Admin can create an account and its initial Admin user. Both rows are committed in one transaction.

`POST /api/accounts/`

Example body:

```json
{
  "name": "Acme Technologies",
  "email": "admin@acme.example",
  "contact": "+911234567890",
  "address": "Pune, Maharashtra",
  "admin": {
    "first_name": "Aarav",
    "last_name": "Shah",
    "email": "aarav@acme.example",
    "password": "Use-a-strong-temporary-password",
    "contact": "+919876543210"
  }
}
```

The account's first user is assigned the protected system `admin` role and receives the new account's `account_id`. The account itself does not store a password; authentication remains user-based.

## Account user creation API

An authenticated Account Admin can create users only inside their own account:

`POST /api/users/`

Omit `user_role_id` to assign the default system `user` role. A supplied role must be the global system `user` role or a custom role belonging to the same account. Account Admins cannot assign the platform `Super admin` or system `admin` role.

## Important deployment note

`create_all()` does not alter existing tables. Do not deploy the updated app against an old database until the migration has completed successfully. Run the migration on a backup/staging copy first.
