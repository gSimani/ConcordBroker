"""
Generate batched SQL statements for DOR assignment
Creates individual UPDATE statements for ID ranges
"""

# Configuration
COUNTIES = [
    "DADE", "LEE", "ORANGE", "BROWARD", "HILLSBOROUGH",
    "MIAMI-DADE", "COLLIER", "PASCO", "CHARLOTTE", "BREVARD"
]

BATCH_SIZE = 100000  # Process 100k IDs at a time

# Base UPDATE template
UPDATE_TEMPLATE = """UPDATE florida_parcels
SET
    land_use_code = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
        WHEN (just_value > 500000 AND building_value > 200000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000 AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
        WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercia'
        WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
        WHEN (just_value BETWEEN 100000 AND 500000 AND building_value BETWEEN 50000 AND 300000) THEN 'Condo'
        WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
        WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
        ELSE 'SFR'
    END
WHERE year = 2025
    AND county = '{county}'
    AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
    AND id >= {start_id} AND id < {end_id};

"""

def generate_batches_for_county(county, min_id, max_id):
    """Generate batched UPDATE statements for a county"""

    batches = []
    current_start = min_id
    batch_num = 1

    while current_start <= max_id:
        current_end = min(current_start + BATCH_SIZE, max_id + 1)

        sql = f"-- {county} Batch {batch_num}: ID {current_start:,} to {current_end-1:,}\n"
        sql += UPDATE_TEMPLATE.format(
            county=county,
            start_id=current_start,
            end_id=current_end
        )

        batches.append(sql)
        current_start = current_end
        batch_num += 1

    return batches

def main():
    """Generate all batched SQL"""

    # You need to provide these from the Supabase query results
    # Run this query first for each county to get min/max IDs:
    # SELECT min(id), max(id) FROM florida_parcels WHERE year = 2025 AND county = 'COUNTY_NAME'

    county_ranges = {
        "DADE": (1119304, 23055434),           # Example - replace with actual
        "LEE": (1000000, 2000000),             # Replace with actual
        "ORANGE": (2000000, 3000000),          # Replace with actual
        "BROWARD": (3000000, 4000000),         # Replace with actual
        "HILLSBOROUGH": (4000000, 5000000),    # Replace with actual
        "MIAMI-DADE": (5000000, 6000000),      # Replace with actual
        "COLLIER": (6000000, 7000000),         # Replace with actual
        "PASCO": (7000000, 8000000),           # Replace with actual
        "CHARLOTTE": (8000000, 9000000),       # Replace with actual
        "BREVARD": (9000000, 10000000),        # Replace with actual
    }

    output_file = "GENERATED_BATCHED_DOR_ASSIGNMENT.sql"

    with open(output_file, 'w') as f:
        f.write("-- ============================================================================\n")
        f.write("-- AUTO-GENERATED BATCHED DOR ASSIGNMENT\n")
        f.write(f"-- Batch size: {BATCH_SIZE:,} IDs per statement\n")
        f.write("-- ============================================================================\n\n")

        f.write("-- Set timeouts\n")
        f.write("SET statement_timeout = '5min';\n")
        f.write("SET lock_timeout = '1min';\n\n")

        for county in COUNTIES:
            if county not in county_ranges:
                f.write(f"-- SKIPPING {county}: No ID range provided\n\n")
                continue

            min_id, max_id = county_ranges[county]

            f.write(f"-- ============================================================================\n")
            f.write(f"-- {county} COUNTY (ID range: {min_id:,} to {max_id:,})\n")
            f.write(f"-- ============================================================================\n\n")

            batches = generate_batches_for_county(county, min_id, max_id)

            for batch_sql in batches:
                f.write(batch_sql)
                f.write("\n")

            # Add progress check after each county
            f.write(f"-- Check {county} progress\n")
            f.write(f"SELECT '{county}' as county, ")
            f.write(f"COUNT(*) as total, ")
            f.write(f"COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code ")
            f.write(f"FROM florida_parcels ")
            f.write(f"WHERE year = 2025 AND county = '{county}';\n\n")

        # Final overall check
        f.write("-- ============================================================================\n")
        f.write("-- FINAL OVERALL CHECK\n")
        f.write("-- ============================================================================\n")
        f.write("SELECT COUNT(*) as total, ")
        f.write("COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code, ")
        f.write("ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage ")
        f.write("FROM florida_parcels WHERE year = 2025;\n")

    print(f"Generated {output_file}")
    print("\nIMPORTANT: Before using this file:")
    print("1. Run this query for each county to get actual ID ranges:")
    print("   SELECT min(id), max(id) FROM florida_parcels WHERE year = 2025 AND county = 'COUNTY_NAME';")
    print("2. Update the county_ranges dictionary in this script")
    print("3. Re-run this script to generate updated SQL")
    print("4. Then run the generated SQL file in Supabase")

if __name__ == "__main__":
    main()