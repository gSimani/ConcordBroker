# IMMEDIATE DATABASE SETUP INSTRUCTIONS

## Your Supabase Project Details
- **URL**: https://pmispwtdngkcmsrsjwbp.supabase.co
- **Dashboard**: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp

## Step-by-Step Instructions

### Step 1: Open Supabase Dashboard
1. Go to: https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp
2. Login if needed

### Step 2: Open SQL Editor
1. In the left sidebar, click on **SQL Editor** (icon looks like `</>`)
2. You'll see "Florida Parcel Count" - that's an existing query
3. Click the **"+ New query"** button at the top

### Step 3: Create Tables
1. In the new query window, DELETE any existing text
2. Copy ALL the content from the file `initialize_complete_database.sql`
3. Paste it into the SQL Editor
4. Click the **"RUN"** button (or press Ctrl+Enter)

### Step 4: Verify Success
After running, you should see:
- Multiple "CREATE TABLE" success messages
- "INSERT 0 5" messages (sample data inserted)
- Final message: "Database initialization complete!"

### Step 5: Check Tables
1. Go to **Table Editor** in the left sidebar
2. You should now see these tables:
   - florida_parcels (5 sample records)
   - properties
   - property_sales_history
   - nav_assessments
   - sunbiz_corporate
   - And 9 more tables

### If You Get Errors:

**Error: "relation already exists"**
- This means some tables were already created
- Solution: Add this to the beginning of the script:
```sql
-- Drop existing tables (BE CAREFUL - this deletes all data!)
DROP TABLE IF EXISTS florida_parcels CASCADE;
DROP TABLE IF EXISTS properties CASCADE;
DROP TABLE IF EXISTS property_sales_history CASCADE;
DROP TABLE IF EXISTS nav_assessments CASCADE;
DROP TABLE IF EXISTS sunbiz_corporate CASCADE;
-- Add other tables as needed
```

**Error: "permission denied"**
- Make sure you're using the service role key
- Check that RLS is not blocking the operation

### Quick Test Query
After setup, run this test query in SQL Editor:
```sql
-- Test if tables are created and have data
SELECT 
    'florida_parcels' as table_name, 
    COUNT(*) as row_count 
FROM florida_parcels
UNION ALL
SELECT 
    'property_sales_history', 
    COUNT(*) 
FROM property_sales_history
UNION ALL
SELECT 
    'nav_assessments', 
    COUNT(*) 
FROM nav_assessments
UNION ALL
SELECT 
    'sunbiz_corporate', 
    COUNT(*) 
FROM sunbiz_corporate;
```

Expected result:
```
table_name              | row_count
------------------------|----------
florida_parcels         | 5
property_sales_history  | 5
nav_assessments        | 3
sunbiz_corporate       | 3
```

### Test in Your App
1. Start your local server:
```bash
cd apps/web
npm run dev
```

2. Go to: http://localhost:5173/properties

3. Search for parcel: `064210010010`

4. You should see the INVERRARY HOLDINGS property!

## Alternative: Using Supabase CLI

If the SQL Editor doesn't work, use the CLI:

1. Install Supabase CLI:
```bash
npm install -g supabase
```

2. Login:
```bash
supabase login
```

3. Link to your project:
```bash
supabase link --project-ref pmispwtdngkcmsrsjwbp
```

4. Run the SQL file:
```bash
supabase db push initialize_complete_database.sql
```

## Need Help?
- Check Supabase logs: Dashboard → Logs → API Logs
- Check browser console for errors
- Verify .env has correct SUPABASE_URL