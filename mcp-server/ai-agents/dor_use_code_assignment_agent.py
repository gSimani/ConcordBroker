"""
DOR Use Code Assignment Agent
Analyzes and assigns DOR use codes to all 9.1M Florida properties
"""

import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text, Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

Base = declarative_base()

class DORUseCode(Base):
    __tablename__ = 'dor_use_codes'

    use_code = Column(String(2), primary_key=True)
    use_description = Column(String(255))
    category = Column(String(100))
    subcategory = Column(String(100))
    is_residential = Column(Boolean)
    is_commercial = Column(Boolean)
    is_industrial = Column(Boolean)
    is_agricultural = Column(Boolean)
    is_institutional = Column(Boolean)

class FloridaParcel(Base):
    __tablename__ = 'florida_parcels'

    id = Column(Integer, primary_key=True)
    parcel_id = Column(String(50))
    county = Column(String(50))
    year = Column(Integer)
    dor_uc = Column(String(2))
    property_use = Column(String(100))
    property_use_category = Column(String(100))
    just_value = Column(Float)
    building_value = Column(Float)
    land_value = Column(Float)

class DORUseCodeAssignmentAgent:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise Exception("Missing Supabase credentials")

        # Build PostgreSQL connection string
        db_url = self.supabase_url.replace('https://', '')
        self.engine = create_engine(
            f"postgresql://postgres.{db_url.split('.')[1]}:{self.supabase_key}@{db_url}:5432/postgres",
            pool_size=10,
            max_overflow=20
        )
        self.Session = sessionmaker(bind=self.engine)

    def analyze_current_status(self):
        """Analyze current DOR use code assignment status"""
        print("[ANALYZE] Analyzing current DOR use code assignment status...")

        with self.engine.connect() as conn:
            # Total properties
            total_query = text("SELECT COUNT(*) as total FROM florida_parcels WHERE year = 2025")
            total_result = conn.execute(total_query).fetchone()
            total = total_result[0] if total_result else 0

            # Properties with DOR code
            with_code_query = text("""
                SELECT COUNT(*) as with_code
                FROM florida_parcels
                WHERE year = 2025 AND dor_uc IS NOT NULL AND dor_uc != ''
            """)
            with_code_result = conn.execute(with_code_query).fetchone()
            with_code = with_code_result[0] if with_code_result else 0

            # Properties without DOR code
            without_code = total - with_code

            # Use code distribution
            distribution_query = text("""
                SELECT
                    dor_uc,
                    COUNT(*) as count,
                    ROUND(COUNT(*)::numeric / :total * 100, 2) as percentage
                FROM florida_parcels
                WHERE year = 2025 AND dor_uc IS NOT NULL AND dor_uc != ''
                GROUP BY dor_uc
                ORDER BY count DESC
                LIMIT 20
            """)
            distribution = conn.execute(distribution_query, {"total": total}).fetchall()

            # Get DOR use codes from reference table
            dor_codes_query = text("""
                SELECT use_code, use_description, category
                FROM dor_use_codes
                ORDER BY use_code
            """)
            dor_codes = conn.execute(dor_codes_query).fetchall()

            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_properties": total,
                    "with_dor_code": with_code,
                    "without_dor_code": without_code,
                    "coverage_percentage": round((with_code / total * 100) if total > 0 else 0, 2)
                },
                "top_20_use_codes": [
                    {
                        "code": row[0],
                        "count": row[1],
                        "percentage": float(row[2])
                    }
                    for row in distribution
                ],
                "dor_use_codes_available": len(dor_codes)
            }

            return report

    def get_use_code_mapping(self):
        """Get DOR use code mapping with descriptions"""
        with self.engine.connect() as conn:
            query = text("""
                SELECT
                    use_code,
                    use_description,
                    category,
                    subcategory,
                    is_residential,
                    is_commercial,
                    is_industrial,
                    is_agricultural,
                    is_institutional
                FROM dor_use_codes
                ORDER BY use_code
            """)
            results = conn.execute(query).fetchall()

            mapping = {}
            for row in results:
                mapping[row[0]] = {
                    "description": row[1],
                    "category": row[2],
                    "subcategory": row[3],
                    "flags": {
                        "residential": row[4],
                        "commercial": row[5],
                        "industrial": row[6],
                        "agricultural": row[7],
                        "institutional": row[8]
                    }
                }

            return mapping

    def assign_missing_use_codes(self, batch_size=10000):
        """Assign DOR use codes to properties missing them"""
        print(f"[ASSIGN] Starting batch assignment (batch size: {batch_size})...")

        with self.engine.connect() as conn:
            # Count properties needing assignment
            count_query = text("""
                SELECT COUNT(*)
                FROM florida_parcels
                WHERE year = 2025 AND (dor_uc IS NULL OR dor_uc = '')
            """)
            total_to_assign = conn.execute(count_query).fetchone()[0]

            print(f"[INFO] Properties to assign: {total_to_assign:,}")

            if total_to_assign == 0:
                print("[SUCCESS] All properties already have DOR use codes assigned!")
                return {"assigned": 0, "total": 0}

            # Strategy: Use property characteristics to infer DOR code
            # This is a smart assignment based on property data
            update_query = text("""
                UPDATE florida_parcels
                SET dor_uc = CASE
                    -- Residential based on building characteristics
                    WHEN (just_value > 0 AND building_value > 0 AND land_value > 0) THEN '00'
                    -- Commercial if high value and specific characteristics
                    WHEN (just_value > 500000 AND building_value > 300000) THEN '17'
                    -- Agricultural if large land area
                    WHEN (land_value > building_value * 2 AND land_value > 100000) THEN '01'
                    -- Default to vacant residential
                    ELSE '10'
                END,
                property_use = CASE
                    WHEN (just_value > 0 AND building_value > 0 AND land_value > 0) THEN 'Single Family'
                    WHEN (just_value > 500000 AND building_value > 300000) THEN 'Commercial'
                    WHEN (land_value > building_value * 2 AND land_value > 100000) THEN 'Agricultural'
                    ELSE 'Vacant Residential'
                END
                WHERE year = 2025 AND (dor_uc IS NULL OR dor_uc = '')
            """)

            result = conn.execute(update_query)
            conn.commit()

            assigned = result.rowcount

            print(f"[SUCCESS] Assigned DOR codes to {assigned:,} properties")

            return {
                "assigned": assigned,
                "total": total_to_assign,
                "percentage": round((assigned / total_to_assign * 100) if total_to_assign > 0 else 0, 2)
            }

    def validate_assignments(self):
        """Validate DOR use code assignments"""
        print("[VALIDATE] Validating DOR use code assignments...")

        with self.engine.connect() as conn:
            # Check for invalid codes
            invalid_query = text("""
                SELECT COUNT(*)
                FROM florida_parcels fp
                WHERE year = 2025
                AND dor_uc IS NOT NULL
                AND dor_uc != ''
                AND NOT EXISTS (
                    SELECT 1 FROM dor_use_codes duc
                    WHERE duc.use_code = fp.dor_uc
                )
            """)
            invalid_count = conn.execute(invalid_query).fetchone()[0]

            # Get validation stats
            validation_query = text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as with_code,
                    COUNT(CASE WHEN dor_uc IS NULL OR dor_uc = '' THEN 1 END) as without_code
                FROM florida_parcels
                WHERE year = 2025
            """)
            stats = conn.execute(validation_query).fetchone()

            return {
                "total_properties": stats[0],
                "with_valid_code": stats[1] - invalid_count,
                "with_invalid_code": invalid_count,
                "without_code": stats[2],
                "validation_passed": invalid_count == 0 and stats[2] == 0
            }

def main():
    print("[AI AGENT] DOR Use Code Assignment Agent Starting...")
    print("=" * 60)

    try:
        agent = DORUseCodeAssignmentAgent()

        # Step 1: Analyze current status
        print("\n[PHASE 1] Current Status Analysis")
        status = agent.analyze_current_status()
        print(json.dumps(status, indent=2))

        # Save status report
        with open('dor_use_code_status_report.json', 'w') as f:
            json.dump(status, f, indent=2)

        # Step 2: Get use code mapping
        print("\n[PHASE 2] DOR Use Code Mapping")
        mapping = agent.get_use_code_mapping()
        print(f"[SUCCESS] Loaded {len(mapping)} DOR use codes")

        # Save mapping
        with open('dor_use_code_mapping.json', 'w') as f:
            json.dump(mapping, f, indent=2)

        # Step 3: Assign missing codes
        print("\n[PHASE 3] Assigning Missing Use Codes")
        assignment_result = agent.assign_missing_use_codes()
        print(json.dumps(assignment_result, indent=2))

        # Step 4: Validate assignments
        print("\n[PHASE 4] Validation")
        validation = agent.validate_assignments()
        print(json.dumps(validation, indent=2))

        # Final report
        print("\n" + "=" * 60)
        print("[COMPLETE] DOR Use Code Assignment Complete!")
        print(f"[SUCCESS] Total Properties: {validation['total_properties']:,}")
        print(f"[SUCCESS] With Valid Code: {validation['with_valid_code']:,}")
        print(f"[WARNING] With Invalid Code: {validation['with_invalid_code']:,}")
        print(f"[ERROR] Without Code: {validation['without_code']:,}")
        print(f"{'[PASS] VALIDATION PASSED' if validation['validation_passed'] else '[FAIL] VALIDATION FAILED'}")
        print("=" * 60)

        return validation['validation_passed']

    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)