-- Add the pending-registration state used by public organization signup.
-- Existing organizations are not pending and remain unchanged.
ALTER TABLE accounts
    ADD COLUMN is_registration_pending TINYINT(1) NOT NULL DEFAULT 0;
