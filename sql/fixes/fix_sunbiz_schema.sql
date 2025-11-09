-- Fix Sunbiz table schema issues
-- ================================

-- 1. Increase doc_number column size in sunbiz_corporate
ALTER TABLE sunbiz_corporate 
ALTER COLUMN doc_number TYPE VARCHAR(50);

-- 2. Increase doc_number column size in sunbiz_corporate_events
ALTER TABLE sunbiz_corporate_events 
ALTER COLUMN doc_number TYPE VARCHAR(50);

-- 3. Increase doc_number column size in sunbiz_fictitious
ALTER TABLE sunbiz_fictitious 
ALTER COLUMN doc_number TYPE VARCHAR(50);

-- 4. Disable RLS on Sunbiz tables temporarily to allow inserts
ALTER TABLE sunbiz_corporate DISABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_corporate_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE sunbiz_fictitious DISABLE ROW LEVEL SECURITY;

-- 5. Create RLS policies that allow all operations (if needed later)
-- DROP POLICY IF EXISTS "Enable all access for authenticated users" ON sunbiz_corporate;
-- CREATE POLICY "Enable all access for authenticated users" ON sunbiz_corporate
--     FOR ALL USING (true) WITH CHECK (true);

-- DROP POLICY IF EXISTS "Enable all access for authenticated users" ON sunbiz_corporate_events;
-- CREATE POLICY "Enable all access for authenticated users" ON sunbiz_corporate_events
--     FOR ALL USING (true) WITH CHECK (true);

-- DROP POLICY IF EXISTS "Enable all access for authenticated users" ON sunbiz_fictitious;
-- CREATE POLICY "Enable all access for authenticated users" ON sunbiz_fictitious
--     FOR ALL USING (true) WITH CHECK (true);