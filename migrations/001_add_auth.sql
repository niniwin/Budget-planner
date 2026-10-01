ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS email VARCHAR(255),
    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user',
    ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(50),
    ADD COLUMN IF NOT EXISTS oauth_subject VARCHAR(255);

CREATE UNIQUE INDEX IF NOT EXISTS ix_user_email_unique
    ON "user" (email)
    WHERE email IS NOT NULL;

ALTER TABLE notes
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES "user"(id);

UPDATE "user"
SET role = 'admin'
WHERE id = (SELECT MIN(id) FROM "user")
  AND NOT EXISTS (SELECT 1 FROM "user" WHERE role = 'admin');
