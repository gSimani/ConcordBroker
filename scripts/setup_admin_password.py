#!/usr/bin/env python3
"""
Setup Admin Password
Adds password_hash column and sets initial admin password
"""

import os
import sys
import psycopg2
import bcrypt
from urllib.parse import quote_plus

# Database connection parameters
SUPABASE_HOST = os.getenv('SUPABASE_HOST', 'aws-1-us-east-1.pooler.supabase.com')
SUPABASE_USER = os.getenv('SUPABASE_USER', 'postgres.pmispwtdngkcmsrsjwbp')
SUPABASE_PASSWORD = os.getenv('SUPABASE_PASSWORD', 'West@Boca613!')
SUPABASE_DB = os.getenv('SUPABASE_DB', 'postgres')
SUPABASE_PORT = os.getenv('SUPABASE_PORT', '5432')

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def main():
    # Encode password for connection string
    encoded_password = quote_plus(SUPABASE_PASSWORD)

    print("=" * 60)
    print("Admin Password Setup")
    print("=" * 60)

    try:
        # Connect to database
        print(f"\nConnecting to {SUPABASE_HOST}...")
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            database=SUPABASE_DB
        )
        conn.autocommit = True
        cursor = conn.cursor()
        print("[OK] Connected successfully")

        # Read and execute migration
        migration_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'supabase',
            'migrations',
            '20251106_add_password_to_admin_users.sql'
        )

        print(f"\nExecuting migration: {migration_path}")
        with open(migration_path, 'r') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)
        print("[OK] Migration executed successfully")

        # Hash the password
        default_password = "Admin123!"
        print(f"\nHashing default password: {default_password}")
        password_hash = hash_password(default_password)
        print("[OK] Password hashed successfully")

        # Update admin user with hashed password
        print("\nUpdating admin user with password...")
        cursor.execute("""
            UPDATE admin_users
            SET password_hash = %s
            WHERE email = 'admin@concordbroker.com'
            RETURNING id, email, name, role;
        """, (password_hash,))

        result = cursor.fetchone()
        if result:
            print("[OK] Admin user updated successfully")
            print(f"\n  ID: {result[0]}")
            print(f"  Email: {result[1]}")
            print(f"  Name: {result[2]}")
            print(f"  Role: {result[3]}")
            print(f"\n  Login Credentials:")
            print(f"  Email: {result[1]}")
            print(f"  Password: {default_password}")
        else:
            print("[ERROR] No admin user found to update")
            return 1

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("Setup completed successfully!")
        print("=" * 60)
        print(f"\nYou can now login at: http://localhost:5191/admin/login")
        print(f"Email: admin@concordbroker.com")
        print(f"Password: {default_password}")
        print("\n[WARNING] IMPORTANT: Change this password after first login!")

        return 0

    except Exception as e:
        print(f"\n[ERROR] Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
