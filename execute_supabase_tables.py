#!/usr/bin/env python3
"""Execute SQL script to create property_notes and property_contacts tables in Supabase"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in environment variables")
        return

    # Create Supabase client with service role key for admin operations
    supabase: Client = create_client(supabase_url, supabase_key)

    # Read SQL file
    sql_file = 'supabase/create_property_notes_contacts.sql'
    with open(sql_file, 'r') as f:
        sql_content = f.read()

    print("Creating property_notes and property_contacts tables...")

    # Split SQL commands and execute them
    sql_commands = sql_content.split(';')

    for command in sql_commands:
        command = command.strip()
        if command:
            try:
                # Note: Supabase Python client doesn't have direct SQL execution
                # We'll need to use the REST API or create tables through Supabase dashboard
                print(f"Command to execute: {command[:50]}...")
            except Exception as e:
                print(f"Error executing command: {e}")

    print("\nIMPORTANT: Please execute the SQL file directly in Supabase SQL Editor:")
    print("1. Go to https://app.supabase.com/project/{your-project}/sql/new")
    print("2. Copy the contents of supabase/create_property_notes_contacts.sql")
    print("3. Paste and execute in the SQL editor")
    print("\nAlternatively, tables will be created automatically when the app first tries to save notes/contacts.")

if __name__ == "__main__":
    main()