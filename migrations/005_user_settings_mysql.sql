-- Logsbee User: create account-level settings table.
-- Run once on existing MySQL databases after backing up the database.
CREATE TABLE user_settings (
    id CHAR(32) NOT NULL,
    user_id CHAR(32) NOT NULL,
    two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_user_settings_user_id (user_id),
    CONSTRAINT fk_user_settings_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Preserve the current 2FA state during migration.
INSERT INTO user_settings (id, user_id, two_factor_enabled, created_at, updated_at)
SELECT REPLACE(UUID(), '-', ''), id, is_two_factor_authenticated, UTC_TIMESTAMP(), UTC_TIMESTAMP()
FROM users;
