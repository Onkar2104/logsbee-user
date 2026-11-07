-- Existing organizations are treated as already verified.
-- New public registrations explicitly set accounts.is_email_verified = 0.
ALTER TABLE accounts
    ADD COLUMN is_email_verified TINYINT(1) NOT NULL DEFAULT 1;
