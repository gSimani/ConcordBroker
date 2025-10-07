#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive ConcordBroker Audit Script
Analyzes database tables, API endpoints, UI components, and data flows
"""

import os
import sys
import json
import re
from datetime import datetime
from supabase import create_client, Client
from typing import Dict, List, Any

# Force UTF-8 encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase configuration with timeout
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Tables to audit - CORE TABLES ONLY
TABLES_TO_AUDIT = [
    "florida_parcels",
    "property_sales_history",
    "sunbiz_corporate",
    "florida_entities",
    "tax_certificates",
    "sdf_sales",
    "sales_data_view",
    "florida_sdf_sales",
    "owner_identities",
    "property_ownership",
    "entity_principals"
]

def audit_database_table(table_name: str) -> Dict[str, Any]:
    """Audit a single database table"""
    print(f"Auditing table: {table_name}")

    result = {
        "exists": False,
        "row_count": 0,
        "sample_data": [],
        "columns": [],
        "has_data": False,
        "error": None
    }

    try:
        # Get row count
        response = supabase.table(table_name).select("*", count="exact").limit(0).execute()
        result["row_count"] = response.count or 0
        result["exists"] = True
        result["has_data"] = result["row_count"] > 0

        # Get sample data (5 records)
        if result["row_count"] > 0:
            sample_response = supabase.table(table_name).select("*").limit(5).execute()
            result["sample_data"] = sample_response.data

            # Extract column names from first record
            if sample_response.data and len(sample_response.data) > 0:
                result["columns"] = list(sample_response.data[0].keys())

        print(f"  [OK] {table_name}: {result['row_count']:,} rows")

    except Exception as e:
        result["error"] = str(e)
        print(f"  [FAIL] {table_name}: {str(e)}")

    return result

def analyze_api_file(file_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Analyze API endpoints in a Python file"""
    endpoints = []

    if not os.path.exists(file_path):
        return {"endpoints": []}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find FastAPI route decorators
            route_patterns = [
                r'@router\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
                r'@app\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
            ]

            for pattern in route_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    method = match.group(1).upper()
                    route = match.group(2)

                    # Find table references in nearby code
                    tables = re.findall(r'supabase\.table\(["\']([^"\']+)["\']', content)

                    endpoints.append({
                        "method": method,
                        "route": route,
                        "file": os.path.basename(file_path),
                        "tables_referenced": list(set(tables)) if tables else []
                    })

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return {"endpoints": endpoints}

def analyze_ui_component(file_path: str) -> Dict[str, Any]:
    """Analyze a React component for data requirements"""
    component = {
        "file": os.path.basename(file_path),
        "full_path": file_path,
        "api_calls": [],
        "data_fields_used": [],
        "hooks_used": []
    }

    if not os.path.exists(file_path):
        return component

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find API calls
            api_patterns = [
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.(get|post|put|patch|delete)\(["\']([^"\']+)["\']',
                r'useQuery\(["\']([^"\']+)["\']',
                r'useSWR\(["\']([^"\']+)["\']',
            ]

            for pattern in api_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        component["api_calls"].append(match[-1])
                    else:
                        component["api_calls"].append(match)

            # Find data field references (property., data., etc.)
            field_pattern = r'(property|data|record)\.(\w+)'
            fields = re.findall(field_pattern, content)
            component["data_fields_used"] = list(set([f[1] for f in fields]))

            # Find React hooks
            hook_pattern = r'use(\w+)\('
            hooks = re.findall(hook_pattern, content)
            component["hooks_used"] = list(set(hooks))

    except Exception as e:
        print(f"Error analyzing component {file_path}: {e}")

    return component

def main():
    print("=" * 80)
    print("CONCORDBROKER COMPREHENSIVE AUDIT")
    print("=" * 80)
    print()

    audit_report = {
        "timestamp": datetime.now().isoformat(),
        "database_tables": {},
        "api_endpoints": {},
        "ui_components": {},
        "issues_found": []
    }

    # 1. DATABASE AUDIT
    print("\n[1/5] DATABASE AUDIT")
    print("-" * 80)
    for table in TABLES_TO_AUDIT:
        audit_report["database_tables"][table] = audit_database_table(table)

    # 2. API ENDPOINTS AUDIT
    print("\n[2/5] API ENDPOINTS AUDIT")
    print("-" * 80)

    api_files = [
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\api\\property_live_api.py",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\api\\routers\\properties.py",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\api\\production_property_api.py",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\api\\main.py",
    ]

    for api_file in api_files:
        if os.path.exists(api_file):
            print(f"Analyzing: {os.path.basename(api_file)}")
            result = analyze_api_file(api_file)
            audit_report["api_endpoints"][os.path.basename(api_file)] = result

    # 3. UI COMPONENTS AUDIT
    print("\n[3/5] UI COMPONENTS AUDIT")
    print("-" * 80)

    ui_components = [
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\components\\property\\MiniPropertyCard.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\components\\property\\tabs\\CorePropertyTab.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\components\\property\\tabs\\TaxesTab.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\components\\property\\tabs\\EnhancedSunbizTab.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\components\\property\\tabs\\SalesHistoryTab.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\pages\\properties\\PropertySearch.tsx",
        "C:\\Users\\gsima\\Documents\\MyProject\\ConcordBroker\\apps\\web\\src\\pages\\property\\EnhancedPropertyProfile.tsx",
    ]

    for component_file in ui_components:
        if os.path.exists(component_file):
            print(f"Analyzing: {os.path.basename(component_file)}")
            result = analyze_ui_component(component_file)
            audit_report["ui_components"][os.path.basename(component_file)] = result

    # 4. IDENTIFY ISSUES
    print("\n[4/5] IDENTIFYING ISSUES")
    print("-" * 80)

    # Check for tables with no data
    for table_name, table_info in audit_report["database_tables"].items():
        if table_info["exists"] and not table_info["has_data"]:
            audit_report["issues_found"].append({
                "type": "missing_data",
                "severity": "medium",
                "component": f"database.{table_name}",
                "description": f"Table '{table_name}' exists but has 0 rows",
                "fix_required": f"Populate {table_name} table with data or remove if unused"
            })

    # Check for tables that don't exist
    for table_name, table_info in audit_report["database_tables"].items():
        if not table_info["exists"]:
            audit_report["issues_found"].append({
                "type": "missing_table",
                "severity": "high",
                "component": f"database.{table_name}",
                "description": f"Table '{table_name}' does not exist in database",
                "fix_required": f"Create {table_name} table or remove references to it"
            })

    # 5. SAVE REPORT
    print("\n[5/5] GENERATING REPORT")
    print("-" * 80)

    report_file = "comprehensive_audit_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2, default=str)

    print(f"\n[SUCCESS] Audit complete! Report saved to: {report_file}")

    # Print summary
    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    tables_with_data = sum(1 for t in audit_report["database_tables"].values() if t["has_data"])
    tables_total = len(audit_report["database_tables"])

    print(f"\nDatabase Tables: {tables_with_data}/{tables_total} have data")
    print(f"Issues Found: {len(audit_report['issues_found'])}")

    if audit_report["issues_found"]:
        print("\nTop Issues:")
        for i, issue in enumerate(audit_report["issues_found"][:5], 1):
            print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")

    print("\n" + "=" * 80)

    return audit_report

if __name__ == "__main__":
    main()
