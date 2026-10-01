-- Assign records created before user ownership existed to the first admin.
-- This only updates records that do not already belong to a user.
UPDATE transactions
SET user_id = (
    SELECT id
    FROM "user"
    WHERE role = 'admin'
    ORDER BY id
    LIMIT 1
)
WHERE user_id IS NULL
  AND EXISTS (SELECT 1 FROM "user" WHERE role = 'admin');

UPDATE notes
SET user_id = (
    SELECT id
    FROM "user"
    WHERE role = 'admin'
    ORDER BY id
    LIMIT 1
)
WHERE user_id IS NULL
  AND EXISTS (SELECT 1 FROM "user" WHERE role = 'admin');
