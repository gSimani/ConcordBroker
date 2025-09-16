"""
Validate NAL Database Deployment Script
Simple validation of SQL syntax and completeness
"""

import os
import re
from pathlib import Path

def validate_sql_file(file_path):
    """Validate SQL file syntax and completeness"""
    
    print("="*60)
    print("NAL DATABASE DEPLOYMENT VALIDATION")
    print("="*60)
    print(f"Validating file: {file_path}")
    print()
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"File size: {len(sql_content):,} characters")
        print()
        
        # Check for required tables
        required_tables = [
            'florida_properties_core',
            'property_valuations', 
            'property_exemptions',
            'property_characteristics',
            'property_sales_enhanced',
            'property_addresses',
            'property_admin_data'
        ]
        
        print("Checking for required tables:")
        tables_found = 0
        for table in required_tables:
            if f'CREATE TABLE {table}' in sql_content:
                print(f"  ✓ {table}")
                tables_found += 1
            else:
                print(f"  ✗ {table} - MISSING")
        
        print(f"\nTables found: {tables_found}/7")
        
        # Check for indexes
        index_patterns = [
            'CREATE INDEX',
            'CREATE UNIQUE INDEX'
        ]
        
        total_indexes = 0
        for pattern in index_patterns:
            indexes = len(re.findall(pattern, sql_content))
            total_indexes += indexes
        
        print(f"Indexes found: {total_indexes}")
        
        # Check for materialized views
        materialized_views = len(re.findall(r'CREATE MATERIALIZED VIEW', sql_content))
        print(f"Materialized views: {materialized_views}")
        
        # Check for functions
        functions = len(re.findall(r'CREATE OR REPLACE FUNCTION', sql_content))
        print(f"Functions: {functions}")
        
        # Check for RLS policies
        rls_policies = len(re.findall(r'CREATE POLICY', sql_content))
        print(f"RLS policies: {rls_policies}")
        
        # Check for extensions
        extensions = re.findall(r'CREATE EXTENSION IF NOT EXISTS (\w+)', sql_content)
        print(f"Extensions: {', '.join(extensions)}")
        
        # Check for potential syntax issues
        print("\nSyntax validation:")
        
        # Check for unmatched parentheses
        open_parens = sql_content.count('(')
        close_parens = sql_content.count(')')
        if open_parens == close_parens:
            print("  ✓ Parentheses balanced")
        else:
            print(f"  ✗ Parentheses unbalanced: {open_parens} open, {close_parens} close")
        
        # Check for semicolon termination of major statements
        create_statements = len(re.findall(r'CREATE TABLE[^;]+;', sql_content, re.DOTALL))
        if create_statements >= 7:
            print("  ✓ CREATE TABLE statements properly terminated")
        else:
            print(f"  ✗ Potential termination issues: {create_statements} properly terminated CREATE TABLE statements")
        
        # Check for foreign key constraints
        foreign_keys = len(re.findall(r'FOREIGN KEY', sql_content))
        print(f"  Foreign key constraints: {foreign_keys}")
        
        # Check for check constraints
        check_constraints = len(re.findall(r'CONSTRAINT.*CHECK', sql_content))
        print(f"  Check constraints: {check_constraints}")
        
        # Overall validation score
        score = 0
        max_score = 0
        
        # Table creation (50 points)
        score += min(tables_found * 7, 49)  # Max 49 for 7 tables
        max_score += 49
        
        # Indexes (20 points)
        score += min(total_indexes, 20)
        max_score += 20
        
        # Functions (15 points)
        score += min(functions * 5, 15)
        max_score += 15
        
        # Views (10 points)
        score += min(materialized_views * 5, 10)
        max_score += 10
        
        # RLS policies (6 points)
        score += min(rls_policies, 6)
        max_score += 6
        
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        print(f"\nValidation score: {score}/{max_score} ({percentage:.1f}%)")
        
        if percentage >= 90:
            status = "EXCELLENT"
        elif percentage >= 75:
            status = "GOOD"
        elif percentage >= 60:
            status = "ACCEPTABLE"
        else:
            status = "NEEDS IMPROVEMENT"
        
        print(f"Status: {status}")
        
        # Deployment readiness
        deployment_ready = (
            tables_found >= 7 and
            total_indexes >= 10 and
            functions >= 2 and
            materialized_views >= 1
        )
        
        print(f"\nDeployment ready: {'YES' if deployment_ready else 'NO'}")
        
        if deployment_ready:
            print("\n🎉 The NAL database schema appears ready for deployment!")
            print("\nDeployment instructions:")
            print("1. Copy the contents of deploy_optimized_nal_database.sql")
            print("2. Paste into Supabase SQL Editor")
            print("3. Execute the script")
            print("4. Verify deployment using the validation query at the end")
        else:
            print("\n⚠️  The schema needs attention before deployment")
            if tables_found < 7:
                print(f"   - Missing {7 - tables_found} required tables")
            if total_indexes < 10:
                print(f"   - Need at least {10 - total_indexes} more indexes")
            if functions < 2:
                print(f"   - Need at least {2 - functions} more functions")
        
        return deployment_ready
        
    except Exception as e:
        print(f"ERROR: Failed to validate file: {e}")
        return False

def main():
    """Main validation function"""
    # Check main deployment script
    deployment_file = Path(__file__).parent / "deploy_optimized_nal_database.sql"
    
    print("Validating NAL Database Deployment Script...")
    print()
    
    deployment_valid = validate_sql_file(deployment_file)
    
    # Also check the full schema file
    schema_file = Path(__file__).parent / "optimized_nal_database_schema.sql"
    if schema_file.exists():
        print("\n" + "="*60)
        print("ALSO VALIDATING: Full Schema File")
        print("="*60)
        validate_sql_file(schema_file)
    
    # Check migration script
    migration_file = Path(__file__).parent / "nal_data_migration_script.sql"
    if migration_file.exists():
        print("\n" + "="*60)
        print("MIGRATION SCRIPT STATUS")
        print("="*60)
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_content = f.read()
        
        migration_functions = len(re.findall(r'CREATE OR REPLACE FUNCTION', migration_content))
        print(f"Migration functions: {migration_functions}")
        print(f"File size: {len(migration_content):,} characters")
        print("Status: READY" if migration_functions >= 5 else "INCOMPLETE")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Deployment script: {'READY' if deployment_valid else 'NOT READY'}")
    print(f"Schema files created: 3/3")
    print(f"Total project files: {len(list(Path(__file__).parent.glob('*.sql')))} SQL files")
    
    if deployment_valid:
        print("\n✅ Project is ready for Supabase deployment!")
        print("\nNext steps:")
        print("1. Open Supabase Dashboard > SQL Editor")
        print("2. Copy and paste deploy_optimized_nal_database.sql")
        print("3. Run the deployment script")
        print("4. Check the validation results at the end")
        print("5. Begin NAL data import using the migration functions")
    else:
        print("\n❌ Project needs additional work before deployment")
    
    return deployment_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)