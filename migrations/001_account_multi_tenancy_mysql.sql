-- MySQL migration: account ownership foundation
-- Run this ONCE against the existing database before starting the updated app.
-- Back up the database first. Existing non-Super-Admin users are assigned to
-- one "Migrated account" so their existing access is not silently lost.

CREATE TABLE accounts (
    account_id CHAR(32) NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NULL,
    contact VARCHAR(20) NULL,
    address TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    created_by CHAR(32) NULL,
    updated_at DATETIME NULL,
    deleted_at DATETIME NULL,
    PRIMARY KEY (account_id)
) ENGINE=InnoDB;

ALTER TABLE users
    ADD COLUMN account_id CHAR(32) NULL,
    ADD INDEX ix_users_account_id (account_id),
    ADD CONSTRAINT fk_users_account
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        ON DELETE RESTRICT;

ALTER TABLE user_roles
    ADD COLUMN account_id CHAR(32) NULL,
    ADD COLUMN is_system_role BOOLEAN NOT NULL DEFAULT FALSE,
    ADD INDEX ix_user_roles_account_id (account_id),
    ADD CONSTRAINT fk_user_roles_account
        FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        ON DELETE CASCADE;

-- The previous schema had a globally unique role name. Replace it with
-- account-scoped uniqueness so separate accounts can each have "Manager".
ALTER TABLE user_roles
    DROP INDEX name,
    ADD CONSTRAINT uq_user_roles_account_name UNIQUE (account_id, name);

-- Mark the three existing built-in roles as protected system roles.
UPDATE user_roles
SET is_system_role = TRUE,
    account_id = NULL
WHERE LOWER(name) IN ('super admin', 'admin', 'user');

-- Create a temporary account for existing tenant users. Replace its name and
-- details with the real organization information after deployment.
INSERT INTO accounts (
    account_id, name, is_active, is_deleted, created_at
)
VALUES (
    '11111111111141118111111111111111',
    'Migrated account - update organization name',
    TRUE,
    FALSE,
    UTC_TIMESTAMP()
);

-- Existing Super Admin remains platform-level (account_id NULL).
-- All other existing users are placed in the migrated account.
UPDATE users AS u
JOIN user_roles AS r ON r.id = u.user_role_id
SET u.account_id = '11111111111141118111111111111111'
WHERE LOWER(r.name) <> 'super admin';

-- Verify before starting the updated application:
-- SELECT id, email, account_id, user_role_id FROM users;
-- SELECT id, name, account_id, is_system_role FROM user_roles;
