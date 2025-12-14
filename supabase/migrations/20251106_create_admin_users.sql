-- Create admin_users table for managing administrative access
-- This table stores information about admin users who can manage the system

CREATE TABLE IF NOT EXISTS admin_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('super_admin', 'admin', 'manager')),
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login TIMESTAMPTZ,
  metadata JSONB DEFAULT '{}'::jsonb
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);

-- Create index on status for filtering active users
CREATE INDEX IF NOT EXISTS idx_admin_users_status ON admin_users(status);

-- Create index on role for role-based queries
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);

-- Add trigger to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_admin_users_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_admin_users_updated_at
  BEFORE UPDATE ON admin_users
  FOR EACH ROW
  EXECUTE FUNCTION update_admin_users_updated_at();

-- Grant table-level permissions to anon and authenticated roles
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_users TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON admin_users TO authenticated;

-- Add RLS (Row Level Security) policies
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Policy: Allow reading all users (public access for checking if users exist)
CREATE POLICY "Allow public read access to admin_users"
  ON admin_users
  FOR SELECT
  USING (true);

-- Policy: Allow inserting first user when table is empty
CREATE POLICY "Allow inserting first admin user"
  ON admin_users
  FOR INSERT
  WITH CHECK (
    (SELECT COUNT(*) FROM admin_users) = 0
  );

-- Policy: Allow authenticated users to insert new users
CREATE POLICY "Allow authenticated insert of admin_users"
  ON admin_users
  FOR INSERT
  WITH CHECK (
    auth.role() = 'authenticated' OR
    auth.jwt() ->> 'role' = 'service_role'
  );

-- Policy: Allow users to update their own record
CREATE POLICY "Allow users to update own record"
  ON admin_users
  FOR UPDATE
  USING (
    auth.uid()::text = id::text OR
    auth.role() = 'service_role'
  );

-- Policy: Allow super_admin to delete users
CREATE POLICY "Allow super_admin to delete users"
  ON admin_users
  FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM admin_users
      WHERE id::text = auth.uid()::text
      AND role = 'super_admin'
    ) OR
    auth.role() = 'service_role'
  );

-- Add helpful comments
COMMENT ON TABLE admin_users IS 'Stores administrative users who can manage the ConcordBroker system';
COMMENT ON COLUMN admin_users.id IS 'Unique identifier for the admin user';
COMMENT ON COLUMN admin_users.email IS 'Email address - used for login';
COMMENT ON COLUMN admin_users.phone IS 'Optional phone number';
COMMENT ON COLUMN admin_users.name IS 'Full name of the admin user';
COMMENT ON COLUMN admin_users.role IS 'Role: super_admin, admin, or manager';
COMMENT ON COLUMN admin_users.status IS 'Account status: active or inactive';
COMMENT ON COLUMN admin_users.last_login IS 'Timestamp of last successful login';
COMMENT ON COLUMN admin_users.metadata IS 'Additional user metadata in JSON format';
