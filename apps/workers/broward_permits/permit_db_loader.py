"""
Broward County Permit Database Loader
Loads scraped permit data into Supabase database
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from dataclasses import dataclass

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from base_supabase_db import BaseSupabaseDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PermitRecord:
    """Standardized permit record structure"""
    permit_number: str
    permit_type: str
    description: str
    status: str
    applicant_name: Optional[str]
    contractor_name: Optional[str]
    property_address: str
    parcel_id: Optional[str]
    folio_number: Optional[str]
    issue_date: Optional[str]
    expiration_date: Optional[str]
    final_date: Optional[str]
    valuation: Optional[float]
    permit_fee: Optional[float]
    source_system: str
    source_url: Optional[str]
    jurisdiction: str
    raw_data: Dict[str, Any]
    scraped_at: str

class BrowardPermitDBLoader(BaseSupabaseDB):
    """Loads Broward County permit data into Supabase"""
    
    def __init__(self):
        """Initialize database loader"""
        super().__init__()
        
        self.data_dir = Path("data/broward_permits")
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing statistics
        self.stats = {
            'records_loaded': 0,
            'records_updated': 0,
            'records_failed': 0,
            'last_load': None
        }
    
    def create_permit_tables(self):
        """Create permit tables in Supabase"""
        logger.info("Creating permit tables")
        
        # Main permits table
        permits_sql = """
        CREATE TABLE IF NOT EXISTS broward_permits (
            id BIGSERIAL PRIMARY KEY,
            permit_number VARCHAR(100) UNIQUE NOT NULL,
            permit_type VARCHAR(100),
            description TEXT,
            status VARCHAR(50),
            applicant_name VARCHAR(255),
            contractor_name VARCHAR(255),
            property_address VARCHAR(500),
            parcel_id VARCHAR(50),
            folio_number VARCHAR(50),
            issue_date DATE,
            expiration_date DATE,
            final_date DATE,
            valuation DECIMAL(15,2),
            permit_fee DECIMAL(10,2),
            source_system VARCHAR(50) NOT NULL,
            source_url TEXT,
            jurisdiction VARCHAR(100),
            raw_data JSONB,
            scraped_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_broward_permits_permit_number ON broward_permits(permit_number);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_source_system ON broward_permits(source_system);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_jurisdiction ON broward_permits(jurisdiction);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_issue_date ON broward_permits(issue_date);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_parcel_id ON broward_permits(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_folio_number ON broward_permits(folio_number);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_permit_type ON broward_permits(permit_type);
        CREATE INDEX IF NOT EXISTS idx_broward_permits_status ON broward_permits(status);
        """
        
        # Permit processing log table
        log_sql = """
        CREATE TABLE IF NOT EXISTS broward_permit_processing_log (
            id BIGSERIAL PRIMARY KEY,
            source_system VARCHAR(50),
            processing_date DATE,
            records_processed INTEGER DEFAULT 0,
            records_loaded INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            records_failed INTEGER DEFAULT 0,
            processing_time_seconds INTEGER,
            error_details TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_broward_permit_log_source_system ON broward_permit_processing_log(source_system);
        CREATE INDEX IF NOT EXISTS idx_broward_permit_log_processing_date ON broward_permit_processing_log(processing_date);
        """
        
        # Execute table creation (guarded)
        try:
            if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
                logger.warning('SQL execution disabled; skip table creation. Run SQL via Supabase dashboard.')
                return False
            self.execute_sql(permits_sql)
            self.execute_sql(log_sql)
            logger.info("Permit tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create permit tables: {e}")
            return False
    
    def parse_permit_data(self, raw_data: Dict, source_system: str) -> Optional[PermitRecord]:
        """
        Parse raw permit data into standardized format
        
        Args:
            raw_data: Raw scraped permit data
            source_system: Source system (bcs, hollywood_accela, enviros)
            
        Returns:
            Standardized permit record or None if parsing fails
        """
        try:
            if source_system == "bcs":
                return self._parse_bcs_permit(raw_data)
            elif source_system == "hollywood_accela":
                return self._parse_hollywood_permit(raw_data)
            elif source_system == "enviros":
                return self._parse_enviros_permit(raw_data)
            else:
                logger.warning(f"Unknown source system: {source_system}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing permit data from {source_system}: {e}")
            return None
    
    def _parse_bcs_permit(self, data: Dict) -> PermitRecord:
        """Parse BCS permit data"""
        return PermitRecord(
            permit_number=data.get('permit_number', ''),
            permit_type=data.get('permit_type', ''),
            description=data.get('description', ''),
            status=data.get('status', ''),
            applicant_name=data.get('applicant', ''),
            contractor_name=data.get('contractor', ''),
            property_address=data.get('address', ''),
            parcel_id=data.get('parcel_id'),
            folio_number=data.get('folio'),
            issue_date=self._parse_date(data.get('issue_date')),
            expiration_date=self._parse_date(data.get('expiration_date')),
            final_date=self._parse_date(data.get('final_date')),
            valuation=self._parse_currency(data.get('valuation')),
            permit_fee=self._parse_currency(data.get('fee')),
            source_system="bcs",
            source_url=data.get('url'),
            jurisdiction="Unincorporated Broward",
            raw_data=data,
            scraped_at=data.get('scraped_at', datetime.now().isoformat())
        )
    
    def _parse_hollywood_permit(self, data: Dict) -> PermitRecord:
        """Parse Hollywood Accela permit data"""
        return PermitRecord(
            permit_number=data.get('permit_number', ''),
            permit_type=data.get('permit_type', ''),
            description=data.get('description', ''),
            status=data.get('status', ''),
            applicant_name=data.get('applicant', ''),
            contractor_name=data.get('contractor', ''),
            property_address=data.get('address', ''),
            parcel_id=data.get('parcel_id'),
            folio_number=data.get('folio'),
            issue_date=self._parse_date(data.get('issue_date')),
            expiration_date=self._parse_date(data.get('expiration_date')),
            final_date=self._parse_date(data.get('final_date')),
            valuation=self._parse_currency(data.get('valuation')),
            permit_fee=self._parse_currency(data.get('fee')),
            source_system="hollywood_accela",
            source_url=data.get('url'),
            jurisdiction="Hollywood",
            raw_data=data,
            scraped_at=data.get('scraped_at', datetime.now().isoformat())
        )
    
    def _parse_enviros_permit(self, data: Dict) -> PermitRecord:
        """Parse ENVIROS environmental permit data"""
        return PermitRecord(
            permit_number=data.get('permit_number', ''),
            permit_type=data.get('permit_type', 'Environmental'),
            description=data.get('description', ''),
            status=data.get('status', ''),
            applicant_name=data.get('applicant', ''),
            contractor_name=data.get('contractor', ''),
            property_address=data.get('address', ''),
            parcel_id=data.get('parcel_id'),
            folio_number=data.get('folio'),
            issue_date=self._parse_date(data.get('issue_date')),
            expiration_date=self._parse_date(data.get('expiration_date')),
            final_date=self._parse_date(data.get('final_date')),
            valuation=self._parse_currency(data.get('valuation')),
            permit_fee=self._parse_currency(data.get('fee')),
            source_system="enviros",
            source_url=data.get('url'),
            jurisdiction="Broward Environmental",
            raw_data=data,
            scraped_at=data.get('scraped_at', datetime.now().isoformat())
        )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse various date formats into ISO format"""
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%m/%d/%Y',
            '%m-%d-%Y', 
            '%Y-%m-%d',
            '%m/%d/%y',
            '%m-%d-%y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date().isoformat()
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_currency(self, value_str: Optional[str]) -> Optional[float]:
        """Parse currency values"""
        if not value_str:
            return None
        
        # Remove currency symbols and commas
        clean_value = str(value_str).replace('$', '').replace(',', '').strip()
        
        try:
            return float(clean_value)
        except ValueError:
            return None
    
    def load_permit_file(self, file_path: Path) -> Dict:
        """
        Load permits from a scraped data file
        
        Args:
            file_path: Path to JSON file containing permit data
            
        Returns:
            Loading results
        """
        logger.info(f"Loading permits from {file_path.name}")
        
        results = {
            'file': str(file_path),
            'records_processed': 0,
            'records_loaded': 0,
            'records_updated': 0,
            'records_failed': 0,
            'errors': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            source_system = data.get('source_system', '')
            permits = data.get('permits', [])
            
            results['records_processed'] = len(permits)
            
            for permit_data in permits:
                try:
                    # Parse permit into standard format
                    permit_record = self.parse_permit_data(permit_data, source_system)
                    
                    if not permit_record:
                        results['records_failed'] += 1
                        continue
                    
                    # Check if permit already exists
                    existing = self.fetch_data(
                        "broward_permits",
                        filters={"permit_number": permit_record.permit_number}
                    )
                    
                    if existing:
                        # Update existing record
                        update_data = {
                            'permit_type': permit_record.permit_type,
                            'description': permit_record.description,
                            'status': permit_record.status,
                            'applicant_name': permit_record.applicant_name,
                            'contractor_name': permit_record.contractor_name,
                            'property_address': permit_record.property_address,
                            'parcel_id': permit_record.parcel_id,
                            'folio_number': permit_record.folio_number,
                            'issue_date': permit_record.issue_date,
                            'expiration_date': permit_record.expiration_date,
                            'final_date': permit_record.final_date,
                            'valuation': permit_record.valuation,
                            'permit_fee': permit_record.permit_fee,
                            'source_url': permit_record.source_url,
                            'raw_data': permit_record.raw_data,
                            'scraped_at': permit_record.scraped_at,
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        self.update_data(
                            "broward_permits",
                            update_data,
                            {"permit_number": permit_record.permit_number}
                        )
                        
                        results['records_updated'] += 1
                    else:
                        # Insert new record
                        insert_data = {
                            'permit_number': permit_record.permit_number,
                            'permit_type': permit_record.permit_type,
                            'description': permit_record.description,
                            'status': permit_record.status,
                            'applicant_name': permit_record.applicant_name,
                            'contractor_name': permit_record.contractor_name,
                            'property_address': permit_record.property_address,
                            'parcel_id': permit_record.parcel_id,
                            'folio_number': permit_record.folio_number,
                            'issue_date': permit_record.issue_date,
                            'expiration_date': permit_record.expiration_date,
                            'final_date': permit_record.final_date,
                            'valuation': permit_record.valuation,
                            'permit_fee': permit_record.permit_fee,
                            'source_system': permit_record.source_system,
                            'source_url': permit_record.source_url,
                            'jurisdiction': permit_record.jurisdiction,
                            'raw_data': permit_record.raw_data,
                            'scraped_at': permit_record.scraped_at
                        }
                        
                        self.insert_data("broward_permits", insert_data)
                        results['records_loaded'] += 1
                
                except Exception as e:
                    logger.error(f"Error processing permit record: {e}")
                    results['records_failed'] += 1
                    results['errors'].append(str(e))
            
            # Update statistics
            self.stats['records_loaded'] += results['records_loaded']
            self.stats['records_updated'] += results['records_updated']
            self.stats['records_failed'] += results['records_failed']
            self.stats['last_load'] = datetime.now().isoformat()
            
            # Log processing results
            self._log_processing_results(source_system, results)
            
            # Move file to processed directory
            processed_path = self.processed_dir / file_path.name
            file_path.rename(processed_path)
            
            logger.info(f"Loaded {results['records_loaded']} new permits, updated {results['records_updated']}")
            
        except Exception as e:
            logger.error(f"Error loading permit file {file_path}: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _log_processing_results(self, source_system: str, results: Dict):
        """Log processing results to database"""
        try:
            log_data = {
                'source_system': source_system,
                'processing_date': datetime.now().date().isoformat(),
                'records_processed': results['records_processed'],
                'records_loaded': results['records_loaded'],
                'records_updated': results['records_updated'],
                'records_failed': results['records_failed'],
                'error_details': '; '.join(results['errors'][:10]) if results['errors'] else None
            }
            
            self.insert_data("broward_permit_processing_log", log_data)
            
        except Exception as e:
            logger.error(f"Error logging processing results: {e}")
    
    def load_all_permit_files(self) -> Dict:
        """Load all unprocessed permit files"""
        logger.info("Loading all permit files")
        
        results = {
            'files_processed': 0,
            'total_records_loaded': 0,
            'total_records_updated': 0,
            'total_records_failed': 0,
            'files': []
        }
        
        # Find all JSON files in data directory
        json_files = list(self.data_dir.glob("*.json"))
        
        for file_path in json_files:
            if file_path.name.startswith('permit_'):
                file_result = self.load_permit_file(file_path)
                
                results['files_processed'] += 1
                results['total_records_loaded'] += file_result['records_loaded']
                results['total_records_updated'] += file_result['records_updated']
                results['total_records_failed'] += file_result['records_failed']
                results['files'].append(file_result)
        
        logger.info(f"Loaded {results['files_processed']} files with {results['total_records_loaded']} new permits")
        
        return results
    
    def get_permit_statistics(self) -> Dict:
        """Get permit loading statistics"""
        try:
            # Total permits by source
            source_stats = self.fetch_data(
                "broward_permits",
                select="source_system, COUNT(*) as count",
                group_by="source_system"
            )
            
            # Total permits by status
            status_stats = self.fetch_data(
                "broward_permits", 
                select="status, COUNT(*) as count",
                group_by="status"
            )
            
            # Total permits by jurisdiction
            jurisdiction_stats = self.fetch_data(
                "broward_permits",
                select="jurisdiction, COUNT(*) as count", 
                group_by="jurisdiction"
            )
            
            # Recent processing activity
            recent_activity = self.fetch_data(
                "broward_permit_processing_log",
                order_by="created_at DESC",
                limit=10
            )
            
            return {
                'total_permits': sum(s.get('count', 0) for s in source_stats),
                'by_source': {s['source_system']: s['count'] for s in source_stats},
                'by_status': {s['status']: s['count'] for s in status_stats},
                'by_jurisdiction': {s['jurisdiction']: s['count'] for s in jurisdiction_stats},
                'recent_activity': recent_activity,
                'processing_stats': self.stats
            }
            
        except Exception as e:
            logger.error(f"Error getting permit statistics: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Broward Permit Database Loader')
    parser.add_argument('--create-tables', action='store_true',
                       help='Create permit tables')
    parser.add_argument('--load-files', action='store_true',
                       help='Load all permit files')
    parser.add_argument('--load-file', 
                       help='Load specific permit file')
    parser.add_argument('--stats', action='store_true',
                       help='Show permit statistics')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = BrowardPermitDBLoader()
    
    if args.create_tables:
        loader.create_permit_tables()
    
    elif args.load_files:
        results = loader.load_all_permit_files()
        print(f"Loaded {results['files_processed']} files")
        print(f"New permits: {results['total_records_loaded']}")
        print(f"Updated permits: {results['total_records_updated']}")
    
    elif args.load_file:
        file_path = Path(args.load_file)
        if file_path.exists():
            result = loader.load_permit_file(file_path)
            print(f"Loaded file: {result['file']}")
            print(f"New permits: {result['records_loaded']}")
            print(f"Updated permits: {result['records_updated']}")
        else:
            print(f"File not found: {args.load_file}")
    
    elif args.stats:
        stats = loader.get_permit_statistics()
        print("\nBroward Permit Statistics:")
        print(json.dumps(stats, indent=2, default=str))
    
    else:
        print("No action specified. Use --help for options.")
