"""
Apply Sunbiz schema to Supabase database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Supabase with service role key for admin operations
supabase_url = os.getenv('SUPABASE_URL')
supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_service_key:
    logger.error("SUPABASE_SERVICE_ROLE_KEY not found")
    exit(1)

supabase: Client = create_client(supabase_url, supabase_service_key)

# Read the schema SQL
with open('sunbiz_complete_schema.sql', 'r') as f:
    schema_sql = f.read()

# Split into individual statements
statements = [s.strip() for s in schema_sql.split(';') if s.strip()]

logger.info(f"Executing {len(statements)} SQL statements...")

for i, statement in enumerate(statements, 1):
    try:
        # Execute each statement
        result = supabase.postgrest.rpc('exec_sql', {'query': statement + ';'}).execute()
        logger.info(f"✅ Statement {i} executed successfully")
    except Exception as e:
        # Try alternative approach - direct execution
        logger.warning(f"Statement {i} needs manual execution: {str(e)[:100]}")

logger.info("\n📋 Schema creation attempted. Please verify in Supabase dashboard.")
logger.info("If any statements failed, please run the SQL manually from 'sunbiz_complete_schema.sql'")