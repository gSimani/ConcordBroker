"""
Supabase Database Verification Script
Analyzes and verifies that all data systems are properly deployed
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from supabase import create_client, Client
import asyncio
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VerificationReport:
    """Complete database verification report"""
    timestamp: str
    database_status: Dict
    table_stats: Dict
    data_quality: Dict
    missing_components: List[str]
    recommendations: List[str]
    overall_health: str  # EXCELLENT, GOOD, NEEDS_ATTENTION, CRITICAL

class SupabaseVerifier:
    """Comprehensive Supabase database verification system"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        # Load environment variables
        load_dotenv('../../.env')  # Load from project root
        
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found. Please configure .env.supabase")
        
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        self.report = VerificationReport(
            timestamp=datetime.now().isoformat(),
            database_status={},
            table_stats={},
            data_quality={},
            missing_components=[],
            recommendations=[],
            overall_health="UNKNOWN"
        )
    
    async def verify_all_systems(self) -> VerificationReport:
        """Run complete verification of all data systems"""
        logger.info("=" * 60)
        logger.info("SUPABASE DATABASE VERIFICATION STARTED")
        logger.info("=" * 60)
        
        # 1. Check connection
        await self.verify_connection()
        
        # 2. Verify Florida Parcel Data System
        await self.verify_florida_parcels()
        
        # 3. Verify Sunbiz Business Entity System
        await self.verify_sunbiz_data()
        
        # 4. Verify Entity Matching System
        await self.verify_entity_matching()
        
        # 5. Verify Monitoring Agents
        await self.verify_monitoring_agents()
        
        # 6. Check Data Quality
        await self.check_data_quality()
        
        # 7. Verify Indexes and Performance
        await self.verify_indexes()
        
        # 8. Check Recent Updates
        await self.check_recent_updates()
        
        # 9. Generate Health Score
        self.calculate_health_score()
        
        # 10. Generate Recommendations
        self.generate_recommendations()
        
        return self.report
    
    async def verify_connection(self):
        """Test Supabase connection"""
        try:
            # Test with a simple query
            result = self.supabase.table('florida_parcels').select('count', count='exact', head=True).limit(1).execute()
            self.report.database_status['connection'] = 'CONNECTED'
            self.report.database_status['url'] = self.supabase_url[:30] + '...'
            logger.info("✓ Supabase connection successful")
        except Exception as e:
            self.report.database_status['connection'] = 'FAILED'
            self.report.database_status['error'] = str(e)
            logger.error(f"✗ Supabase connection failed: {e}")
            raise
    
    async def verify_florida_parcels(self):
        """Verify Florida parcel data system"""
        logger.info("\n--- FLORIDA PARCEL DATA VERIFICATION ---")
        
        required_tables = [
            'florida_parcels',
            'florida_condo_units',
            'data_source_monitor',
            'parcel_update_history',
            'monitoring_agents'
        ]
        
        for table in required_tables:
            try:
                result = self.supabase.table(table).select('count', count='exact', head=True).execute()
                count = result.count if hasattr(result, 'count') else 0
                
                self.report.table_stats[table] = {
                    'exists': True,
                    'record_count': count,
                    'status': 'OK' if count > 0 else 'EMPTY'
                }
                
                status_icon = "✓" if count > 0 else "⚠"
                logger.info(f"{status_icon} {table}: {count:,} records")
                
                if count == 0:
                    self.report.missing_components.append(f"No data in {table}")
                    
            except Exception as e:
                self.report.table_stats[table] = {
                    'exists': False,
                    'record_count': 0,
                    'status': 'MISSING',
                    'error': str(e)
                }
                self.report.missing_components.append(f"Table {table} missing or inaccessible")
                logger.error(f"✗ {table}: Missing or error - {e}")
        
        # Check specific counties
        try:
            counties = self.supabase.table('florida_parcels').select('county').execute()
            if counties.data:
                unique_counties = set(row['county'] for row in counties.data if row.get('county'))
                self.report.data_quality['counties_loaded'] = list(unique_counties)
                logger.info(f"Counties with data: {', '.join(unique_counties)}")
                
                # Check if Broward is loaded
                if 'BROWARD' not in unique_counties:
                    self.report.missing_components.append("Broward County data not loaded")
                    logger.warning("⚠ Broward County data not found")
        except:
            pass
    
    async def verify_sunbiz_data(self):
        """Verify Sunbiz business entity data"""
        logger.info("\n--- SUNBIZ DATA VERIFICATION ---")
        
        sunbiz_tables = [
            'sunbiz_corporate',
            'sunbiz_corporate_events',
            'sunbiz_fictitious',
            'sunbiz_fictitious_events',
            'sunbiz_liens',
            'sunbiz_lien_debtors',
            'sunbiz_lien_secured_parties',
            'sunbiz_partnerships',
            'sunbiz_partnership_events',
            'sunbiz_marks',
            'sunbiz_import_log',
            'sunbiz_processed_files'
        ]
        
        sunbiz_loaded = False
        for table in sunbiz_tables:
            try:
                result = self.supabase.table(table).select('count', count='exact', head=True).execute()
                count = result.count if hasattr(result, 'count') else 0
                
                self.report.table_stats[table] = {
                    'exists': True,
                    'record_count': count,
                    'status': 'OK' if count > 0 else 'EMPTY'
                }
                
                if count > 0:
                    sunbiz_loaded = True
                    logger.info(f"✓ {table}: {count:,} records")
                else:
                    logger.info(f"⚠ {table}: Empty (needs data load)")
                    
            except Exception as e:
                self.report.table_stats[table] = {
                    'exists': False,
                    'record_count': 0,
                    'status': 'MISSING'
                }
                logger.info(f"○ {table}: Not created yet")
        
        if not sunbiz_loaded:
            self.report.missing_components.append("Sunbiz data not loaded - run sunbiz_pipeline.py")
    
    async def verify_entity_matching(self):
        """Verify property-entity matching system"""
        logger.info("\n--- ENTITY MATCHING SYSTEM VERIFICATION ---")
        
        matching_tables = [
            'property_entity_matches',
            'entity_portfolio_summary',
            'entity_relationships',
            'property_ownership_history',
            'match_audit_log',
            'entity_search_cache'
        ]
        
        matching_system_ready = True
        for table in matching_tables:
            try:
                # Check if it's a view or table
                is_view = table == 'entity_portfolio_summary'
                
                if is_view:
                    # For materialized views, check differently
                    result = self.supabase.rpc('get_entity_portfolio', {'p_doc_number': 'TEST'}).execute()
                    self.report.table_stats[table] = {
                        'exists': True,
                        'type': 'MATERIALIZED_VIEW',
                        'status': 'OK'
                    }
                    logger.info(f"✓ {table}: Materialized view exists")
                else:
                    result = self.supabase.table(table).select('count', count='exact', head=True).execute()
                    count = result.count if hasattr(result, 'count') else 0
                    
                    self.report.table_stats[table] = {
                        'exists': True,
                        'record_count': count,
                        'status': 'OK' if count > 0 else 'READY'
                    }
                    
                    logger.info(f"✓ {table}: {count:,} matches" if count > 0 else f"○ {table}: Ready for matching")
                    
            except Exception as e:
                self.report.table_stats[table] = {
                    'exists': False,
                    'status': 'MISSING'
                }
                matching_system_ready = False
                logger.info(f"○ {table}: Not created yet")
        
        if not matching_system_ready:
            self.report.missing_components.append("Entity matching tables need creation")
    
    async def verify_monitoring_agents(self):
        """Check monitoring agents status"""
        logger.info("\n--- MONITORING AGENTS STATUS ---")
        
        try:
            # Check Florida parcel monitoring agents
            agents = self.supabase.table('monitoring_agents').select('*').execute()
            
            if agents.data:
                for agent in agents.data:
                    status = "ACTIVE" if agent['enabled'] else "DISABLED"
                    last_run = agent.get('last_run', 'Never')
                    logger.info(f"  {agent['agent_name']}: {status} (Last: {last_run})")
                    
                    self.report.data_quality[f"agent_{agent['agent_name']}"] = {
                        'status': status,
                        'last_run': last_run
                    }
            else:
                self.report.missing_components.append("No monitoring agents configured")
                logger.warning("⚠ No monitoring agents found")
                
        except:
            logger.info("○ Monitoring agents table not found")
        
        # Check Sunbiz agents
        try:
            sunbiz_agents = self.supabase.table('sunbiz_monitoring_agents').select('*').execute()
            
            if sunbiz_agents.data:
                for agent in sunbiz_agents.data:
                    status = "ACTIVE" if agent['enabled'] else "DISABLED"
                    logger.info(f"  {agent['agent_name']}: {status}")
        except:
            pass
    
    async def check_data_quality(self):
        """Analyze data quality metrics"""
        logger.info("\n--- DATA QUALITY ANALYSIS ---")
        
        quality_checks = {
            'parcels_with_geometry': 0,
            'parcels_with_owner': 0,
            'parcels_with_value': 0,
            'recent_sales': 0,
            'matched_entities': 0,
            'high_confidence_matches': 0
        }
        
        try:
            # Check parcels with complete data
            parcels = self.supabase.table('florida_parcels').select(
                'geometry,owner_name,taxable_value,sale_date'
            ).limit(1000).execute()
            
            if parcels.data:
                for parcel in parcels.data:
                    if parcel.get('geometry'):
                        quality_checks['parcels_with_geometry'] += 1
                    if parcel.get('owner_name'):
                        quality_checks['parcels_with_owner'] += 1
                    if parcel.get('taxable_value') and parcel['taxable_value'] > 0:
                        quality_checks['parcels_with_value'] += 1
                    if parcel.get('sale_date'):
                        sale_date = datetime.fromisoformat(parcel['sale_date'].replace('Z', '+00:00'))
                        if sale_date > datetime.now() - timedelta(days=365):
                            quality_checks['recent_sales'] += 1
                
                total = len(parcels.data)
                logger.info(f"  Geometry completeness: {quality_checks['parcels_with_geometry']}/{total}")
                logger.info(f"  Owner data: {quality_checks['parcels_with_owner']}/{total}")
                logger.info(f"  Value data: {quality_checks['parcels_with_value']}/{total}")
                logger.info(f"  Recent sales: {quality_checks['recent_sales']}")
                
                self.report.data_quality['completeness'] = quality_checks
                
        except Exception as e:
            logger.error(f"Data quality check failed: {e}")
    
    async def verify_indexes(self):
        """Check database indexes and performance"""
        logger.info("\n--- INDEX AND PERFORMANCE CHECK ---")
        
        # This would need direct database access
        # For now, we'll check query performance
        
        try:
            import time
            
            # Test query performance
            start = time.time()
            result = self.supabase.table('florida_parcels').select('parcel_id').eq(
                'county', 'BROWARD'
            ).limit(100).execute()
            query_time = time.time() - start
            
            if query_time < 1:
                logger.info(f"✓ Query performance: {query_time:.2f}s (GOOD)")
                self.report.data_quality['query_performance'] = 'GOOD'
            else:
                logger.warning(f"⚠ Query performance: {query_time:.2f}s (SLOW)")
                self.report.data_quality['query_performance'] = 'SLOW'
                self.report.recommendations.append("Consider adding indexes for better performance")
                
        except:
            pass
    
    async def check_recent_updates(self):
        """Check for recent data updates"""
        logger.info("\n--- RECENT DATA UPDATES ---")
        
        try:
            # Check parcel updates
            updates = self.supabase.table('parcel_update_history').select('*').order(
                'update_date', desc=True
            ).limit(5).execute()
            
            if updates.data:
                logger.info("Recent parcel updates:")
                for update in updates.data:
                    logger.info(f"  {update['county']}: {update['update_date']} ({update['records_added']} added)")
            else:
                logger.info("No recent parcel updates")
                self.report.recommendations.append("Run parcel data sync to get latest data")
                
        except:
            pass
        
        try:
            # Check Sunbiz updates
            sunbiz_updates = self.supabase.table('sunbiz_import_log').select('*').order(
                'import_date', desc=True
            ).limit(5).execute()
            
            if sunbiz_updates.data:
                logger.info("Recent Sunbiz updates:")
                for update in sunbiz_updates.data:
                    logger.info(f"  {update['file_type']}: {update['import_date']} ({update['records_imported']} imported)")
            else:
                logger.info("No Sunbiz data loaded yet")
                
        except:
            pass
    
    def calculate_health_score(self):
        """Calculate overall database health score"""
        score = 100
        issues = 0
        
        # Check for missing components
        if self.report.missing_components:
            score -= len(self.report.missing_components) * 10
            issues += len(self.report.missing_components)
        
        # Check table statistics
        empty_tables = sum(1 for table, stats in self.report.table_stats.items() 
                          if stats.get('status') == 'EMPTY')
        missing_tables = sum(1 for table, stats in self.report.table_stats.items() 
                            if stats.get('status') == 'MISSING')
        
        score -= empty_tables * 5
        score -= missing_tables * 15
        issues += empty_tables + missing_tables
        
        # Determine health level
        if score >= 90:
            self.report.overall_health = "EXCELLENT"
        elif score >= 70:
            self.report.overall_health = "GOOD"
        elif score >= 50:
            self.report.overall_health = "NEEDS_ATTENTION"
        else:
            self.report.overall_health = "CRITICAL"
        
        logger.info(f"\n--- OVERALL HEALTH: {self.report.overall_health} (Score: {score}/100) ---")
        if issues > 0:
            logger.info(f"Found {issues} issues that need attention")
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        
        # Check if Florida parcel data needs loading
        if 'florida_parcels' in self.report.table_stats:
            if self.report.table_stats['florida_parcels'].get('record_count', 0) == 0:
                self.report.recommendations.append(
                    "PRIORITY: Load Florida parcel data - Run: python run_parcel_sync.py download --county BROWARD"
                )
        
        # Check if Sunbiz data needs loading
        sunbiz_empty = all(
            self.report.table_stats.get(f'sunbiz_{t}', {}).get('record_count', 0) == 0
            for t in ['corporate', 'fictitious', 'liens']
        )
        if sunbiz_empty:
            self.report.recommendations.append(
                "Load Sunbiz data - Run: python sunbiz_pipeline.py"
            )
        
        # Check if entity matching is ready
        if self.report.table_stats.get('property_entity_matches', {}).get('record_count', 0) == 0:
            if not sunbiz_empty:  # Only if we have Sunbiz data
                self.report.recommendations.append(
                    "Run entity matching to link properties to businesses"
                )
        
        # Check monitoring agents
        if 'No monitoring agents configured' in self.report.missing_components:
            self.report.recommendations.append(
                "Configure monitoring agents for automated updates"
            )
        
        if self.report.recommendations:
            logger.info("\n--- RECOMMENDATIONS ---")
            for i, rec in enumerate(self.report.recommendations, 1):
                logger.info(f"{i}. {rec}")
    
    def generate_report(self) -> str:
        """Generate detailed text report"""
        report_lines = [
            "=" * 60,
            "SUPABASE DATABASE VERIFICATION REPORT",
            f"Generated: {self.report.timestamp}",
            "=" * 60,
            "",
            f"OVERALL HEALTH: {self.report.overall_health}",
            "",
            "TABLE STATISTICS:",
        ]
        
        for table, stats in self.report.table_stats.items():
            status = stats.get('status', 'UNKNOWN')
            count = stats.get('record_count', 0)
            report_lines.append(f"  {table}: {status} ({count:,} records)")
        
        if self.report.missing_components:
            report_lines.extend([
                "",
                "MISSING COMPONENTS:",
            ])
            for component in self.report.missing_components:
                report_lines.append(f"  - {component}")
        
        if self.report.recommendations:
            report_lines.extend([
                "",
                "RECOMMENDATIONS:",
            ])
            for i, rec in enumerate(self.report.recommendations, 1):
                report_lines.append(f"  {i}. {rec}")
        
        report_lines.extend([
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def save_report(self, filepath: str = "supabase_verification_report.txt"):
        """Save report to file"""
        with open(filepath, 'w') as f:
            f.write(self.generate_report())
        logger.info(f"\nReport saved to: {filepath}")


async def main():
    """Run complete Supabase verification"""
    verifier = SupabaseVerifier()
    
    try:
        report = await verifier.verify_all_systems()
        
        # Save report
        verifier.save_report()
        
        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION COMPLETE")
        print("=" * 60)
        print(f"Health Status: {report.overall_health}")
        print(f"Tables Checked: {len(report.table_stats)}")
        print(f"Issues Found: {len(report.missing_components)}")
        print(f"Recommendations: {len(report.recommendations)}")
        
        # Return exit code based on health
        if report.overall_health == "EXCELLENT":
            return 0
        elif report.overall_health == "GOOD":
            return 0
        elif report.overall_health == "NEEDS_ATTENTION":
            return 1
        else:  # CRITICAL
            return 2
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)