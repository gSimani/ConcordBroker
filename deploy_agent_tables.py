import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv('DATABASE_URL')
if '&supa=' in db_url:
    db_url = db_url.split('&supa=')[0]
elif '?supa=' in db_url:
    db_url = db_url.split('?supa=')[0]

conn = psycopg2.connect(db_url)
conn.autocommit = True
cursor = conn.cursor()

print("[INFO] Creating additional agent tables...")

with open('create_agent_tables.sql', 'r') as f:
    sql = f.read()

cursor.execute(sql)
print("[SUCCESS] Agent tables created")

cursor.close()
conn.close()