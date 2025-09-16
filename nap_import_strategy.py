#!/usr/bin/env python3
"""
NAP Data Import Strategy for Broward County 2025
- Analyzes NAP CSV structure 
- Maps fields to existing florida_parcels table
- Creates optimized import plan
"""

import pandas as pd
import csv
from supabase import create_client, Client

def analyze_nap_structure():
    """Analyze NAP CSV file structure"""
    nap_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAP16P202501.csv"
    
    print("=== NAP CSV FILE ANALYSIS ===")
    
    # Read first few rows to understand structure
    with open(nap_file, 'r', encoding='latin1') as f:
        reader = csv.reader(f)
        headers = next(reader)
        sample_rows = [next(reader) for _ in range(3)]
    
    print(f"NAP File: {nap_file}")
    print(f"Total columns: {len(headers)}")
    print(f"Total records: ~90,508 (from wc -l)")
    
    print(f"\n=== NAP COLUMN MAPPING ===")
    nap_columns = {
        'CO_NO': 'County Number',
        'ACCT_ID': 'Account ID (Parcel ID)',
        'FILE_T': 'File Type',
        'ASMNT_YR': 'Assessment Year',
        'TAX_AUTH_CD': 'Tax Authority Code',
        'NAICS_CD': 'NAICS Code',
        'JV_F_F_E': 'Just Value',
        'JV_LESE_IMP': 'Just Value Leasehold Improvement',
        'JV_TOTAL': 'Total Just Value',
        'AV_TOTAL': 'Total Assessed Value',
        'JV_POL_CONTRL': 'Just Value Policy Control',
        'AV_POL_CONTRL': 'Assessed Value Policy Control',
        'EXMPT_VAL': 'Exempt Value',
        'TAX_VAL': 'Taxable Value',
        'PEN_RATE': 'Penalty Rate',
        'OWN_NAM': 'Owner Name',
        'OWN_ADDR': 'Owner Address',
        'OWN_CITY': 'Owner City',
        'OWN_STATE': 'Owner State',
        'OWN_ZIPCD': 'Owner Zip Code',
        'OWN_STATE_DOM': 'Owner State Domicile',
        'FIDU_NAME': 'Fiduciary Name',
        'FIDU_ADDR': 'Fiduciary Address',
        'FIDU_CITY': 'Fiduciary City',
        'FIDU_STATE': 'Fiduciary State',
        'FIDU_ZIPCD': 'Fiduciary Zip',
        'FIDU_CD': 'Fiduciary Code',
        'PHY_ADDR': 'Physical Address',
        'PHY_CITY': 'Physical City',
        'PHY_ZIPCD': 'Physical Zip Code',
        'FIL': 'File Indicator',
        'ALT_KEY': 'Alternate Key',
        'EXMPT': 'Exemption Code',
        'ACCT_ID_CNG': 'Account ID Change',
        'SEQ_NO': 'Sequence Number',
        'TS_ID': 'Timestamp ID'
    }
    
    for i, (col, desc) in enumerate(nap_columns.items()):
        sample_value = sample_rows[0][i] if i < len(sample_rows[0]) else "N/A"
        print(f"{i+1:2d}. {col:<15} - {desc:<35} | Sample: {sample_value}")
    
    return headers, sample_rows

def create_field_mapping():
    """Create mapping between NAP fields and florida_parcels fields"""
    
    print(f"\n=== FIELD MAPPING STRATEGY ===")
    
    # Define field mappings
    field_mapping = {
        # Core identification
        'ACCT_ID': 'parcel_id',
        'ASMNT_YR': 'year',
        
        # Owner information
        'OWN_NAM': 'owner_name',
        'OWN_ADDR': 'owner_addr1', 
        'OWN_CITY': 'owner_city',
        'OWN_STATE': 'owner_state',
        'OWN_ZIPCD': 'owner_zip',
        
        # Physical address
        'PHY_ADDR': 'phy_addr1',
        'PHY_CITY': 'phy_city',
        'PHY_ZIPCD': 'phy_zipcd',
        
        # Valuation data  
        'JV_TOTAL': 'just_value',
        'AV_TOTAL': 'assessed_value',
        'TAX_VAL': 'taxable_value',
        
        # Additional NAP-specific fields to add
        'TAX_AUTH_CD': 'tax_authority_code',
        'NAICS_CD': 'naics_code',
        'EXMPT_VAL': 'exempt_value',
        'FIDU_NAME': 'fiduciary_name',
        'FIDU_ADDR': 'fiduciary_addr',
        'ALT_KEY': 'alt_key',
        'EXMPT': 'exemption_code'
    }
    
    print("NAP Field -> florida_parcels Field Mapping:")
    for nap_field, db_field in field_mapping.items():
        print(f"  {nap_field:<15} -> {db_field}")
    
    return field_mapping

def create_import_plan():
    """Create detailed import execution plan"""
    
    print(f"\n=== NAP IMPORT EXECUTION PLAN ===")
    
    plan = {
        "strategy": "UPDATE_EXISTING_TABLE",
        "approach": "BATCH_UPSERT", 
        "batch_size": 1000,
        "total_records": 90508,
        "estimated_batches": 91,
        "table_modifications": [
            "ADD COLUMN tax_authority_code VARCHAR(20)",
            "ADD COLUMN naics_code VARCHAR(20)", 
            "ADD COLUMN exempt_value DECIMAL(15,2)",
            "ADD COLUMN fiduciary_name VARCHAR(255)",
            "ADD COLUMN fiduciary_addr VARCHAR(255)",
            "ADD COLUMN alt_key VARCHAR(100)",
            "ADD COLUMN exemption_code VARCHAR(100)"
        ],
        "indexes_to_create": [
            "CREATE INDEX idx_florida_parcels_parcel_id ON florida_parcels(parcel_id)",
            "CREATE INDEX idx_florida_parcels_owner_name ON florida_parcels(owner_name)",
            "CREATE INDEX idx_florida_parcels_phy_addr ON florida_parcels(phy_addr1)",
            "CREATE INDEX idx_florida_parcels_phy_city ON florida_parcels(phy_city)",
            "CREATE INDEX idx_florida_parcels_taxable_value ON florida_parcels(taxable_value)",
            "CREATE INDEX idx_florida_parcels_just_value ON florida_parcels(just_value)"
        ]
    }
    
    print(f"Strategy: {plan['strategy']}")
    print(f"Approach: {plan['approach']}")
    print(f"Batch Size: {plan['batch_size']:,} records")
    print(f"Total Records: {plan['total_records']:,}")
    print(f"Estimated Batches: {plan['estimated_batches']}")
    
    print(f"\nTable Modifications Required:")
    for mod in plan['table_modifications']:
        print(f"  - {mod}")
        
    print(f"\nPerformance Indexes to Create:")
    for idx in plan['indexes_to_create']:
        print(f"  - {idx}")
    
    return plan

def main():
    print("=== NAP DATA IMPORT STRATEGY ANALYSIS ===")
    print("This script analyzes the NAP CSV and creates an import plan")
    print("for integrating Broward County 2025 NAP data into Supabase.\n")
    
    # Step 1: Analyze NAP file structure
    headers, sample_rows = analyze_nap_structure()
    
    # Step 2: Create field mapping
    field_mapping = create_field_mapping()
    
    # Step 3: Create import plan
    import_plan = create_import_plan()
    
    print(f"\n=== NEXT STEPS ===")
    print("1. ✓ NAP file analysis complete")
    print("2. ✓ Field mapping defined") 
    print("3. ✓ Import strategy planned")
    print("4. → Execute table modifications")
    print("5. → Implement batch import script")
    print("6. → Create performance indexes")
    print("7. → Verify data integrity")
    
    return headers, field_mapping, import_plan

if __name__ == "__main__":
    main()