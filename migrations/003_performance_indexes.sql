-- Run once against the existing PostgreSQL database.
-- Run each statement outside a transaction (CONCURRENTLY permits normal writes).
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_transactions_date
    ON transactions (date);
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_transactions_user_date
    ON transactions (user_id, date);
