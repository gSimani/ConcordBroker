-- Add password_hash column to admin_users table
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Add comment
COMMENT ON COLUMN admin_users.password_hash IS 'Bcrypt hashed password for authentication';
