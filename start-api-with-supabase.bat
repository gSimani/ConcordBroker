@echo off
cd /d "C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api"
set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A
set SUPABASE_URL=https://pmispwtdngkcmsrsjwbp.supabase.co
echo Starting API server with Supabase connection...
uvicorn main_simple:app --host 0.0.0.0 --port 8001