-- Phase 2: RBAC schema for MySQL
-- Back up the database before applying. Run after 001_account_multi_tenancy_mysql.sql.

CREATE TABLE IF NOT EXISTS permissions (
    id CHAR(32) NOT NULL PRIMARY KEY,
    code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id CHAR(32) NOT NULL,
    permission_id CHAR(32) NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permissions_role
        FOREIGN KEY (role_id) REFERENCES user_roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_role_permissions_permission
        FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE INDEX ix_permissions_code ON permissions(code);
