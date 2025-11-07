#!/usr/bin/env python3
"""
Verify Admin Login Configuration
Tests that the admin user and password are properly configured
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

def test_password(password_hash: str, test_password: str) -> bool:
    """Test if a password matches the hash"""
    return bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8'))

def main():
    print("=" * 60)
    print("Admin Login Verification")
    print("=" * 60)

    try:
        # Connect to database
        print(f"\n[TEST] Connecting to database...")
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            port=SUPABASE_PORT,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            database=SUPABASE_DB
        )
        cursor = conn.cursor()
        print("[PASS] Database connection successful")

        # Check if admin user exists
        print("\n[TEST] Checking if admin user exists...")
        cursor.execute("""
            SELECT id, email, name, role, status, password_hash
            FROM admin_users
            WHERE email = 'admin@concordbroker.com' AND status = 'active';
        """)
        user = cursor.fetchone()

        if not user:
            print("[FAIL] Admin user not found or not active")
            return 1

        print("[PASS] Admin user exists")
        print(f"  Email: {user[1]}")
        print(f"  Name: {user[2]}")
        print(f"  Role: {user[3]}")
        print(f"  Status: {user[4]}")

        # Check if password hash exists
        print("\n[TEST] Checking if password is configured...")
        if not user[5]:
            print("[FAIL] Password hash is not set")
            return 1

        print("[PASS] Password hash exists")
        print(f"  Hash (first 20 chars): {user[5][:20]}...")

        # Test correct password
        print("\n[TEST] Testing correct password (Admin123!)...")
        if not test_password(user[5], "Admin123!"):
            print("[FAIL] Correct password does not match hash")
            return 1

        print("[PASS] Correct password validates successfully")

        # Test incorrect password
        print("\n[TEST] Testing incorrect password (wrongpass)...")
        if test_password(user[5], "wrongpass"):
            print("[FAIL] Incorrect password was accepted (security issue!)")
            return 1

        print("[PASS] Incorrect password correctly rejected")

        # Test password field is required
        print("\n[TEST] Checking password_hash column exists...")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'admin_users' AND column_name = 'password_hash';
        """)
        col = cursor.fetchone()

        if not col:
            print("[FAIL] password_hash column does not exist")
            return 1

        print("[PASS] password_hash column exists")
        print(f"  Type: {col[1]}")

        cursor.close()
        conn.close()

        # Summary
        print("\n" + "=" * 60)
        print("All Tests Passed!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("  URL: http://localhost:5191/admin/login")
        print("  Email: admin@concordbroker.com")
        print("  Password: Admin123!")
        print("\nThe login system is properly configured and ready to use.")

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
