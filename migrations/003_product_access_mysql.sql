-- Phase 3: Product catalogue and account/user product entitlements.
-- Back up the database and run this migration exactly once after Phase 1 and 2.

CREATE TABLE products (
    id CHAR(32) NOT NULL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(120) NOT NULL,
    description TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NULL,
    UNIQUE KEY uq_products_code (code),
    KEY ix_products_code (code)
) ENGINE=InnoDB;

CREATE TABLE account_products (
    id CHAR(32) NOT NULL PRIMARY KEY,
    account_id CHAR(32) NOT NULL,
    product_id CHAR(32) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    enabled_at DATETIME NOT NULL,
    expires_at DATETIME NULL,
    created_by CHAR(32) NULL,
    CONSTRAINT uq_account_products_account_product UNIQUE (account_id, product_id),
    CONSTRAINT fk_account_products_account FOREIGN KEY (account_id)
        REFERENCES accounts(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_account_products_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT,
    KEY ix_account_products_account (account_id),
    KEY ix_account_products_product (product_id)
) ENGINE=InnoDB;

CREATE TABLE user_products (
    id CHAR(32) NOT NULL PRIMARY KEY,
    user_id CHAR(32) NOT NULL,
    product_id CHAR(32) NOT NULL,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    granted_at DATETIME NOT NULL,
    granted_by CHAR(32) NULL,
    CONSTRAINT uq_user_products_user_product UNIQUE (user_id, product_id),
    CONSTRAINT fk_user_products_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_products_product FOREIGN KEY (product_id)
        REFERENCES products(id) ON DELETE RESTRICT,
    KEY ix_user_products_user (user_id),
    KEY ix_user_products_product (product_id)
) ENGINE=InnoDB;
