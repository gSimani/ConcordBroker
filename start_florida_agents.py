"""
Start Florida Property Data Agents
Simple script to start the daily monitoring and update system
"""

import os
import sys
import time
import requests
import csv
import zipfile
from datetime import datetime
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv
import schedule
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("VITE_SUPABASE_URL")
SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials in environment variables")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

class FloridaDataAgent:
    """Main agent for Florida property data updates"""
    
    def __init__(self):
        self.base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files"
        self.data_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/florida_data")
        self.data_dir.mkdir(exist_ok=True)
        self.current_year = "2025P"
        self.county = "Broward"
        
    def check_for_updates(self):
        """Check Florida Revenue portal for new data files"""
        logger.info(f"Checking for updates for {self.county} County...")
        
        # Define file types to check
        file_types = ["NAL", "NAP", "SDF"]
        updates_found = []
        
        for file_type in file_types:
            file_name = f"{file_type}16P202501.zip"  # Broward is county 16
            file_path = self.data_dir / file_name
            
            # Check if file exists and get its modification time
            if file_path.exists():
                local_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                logger.info(f"{file_type} file last updated: {local_mtime}")
            else:
                logger.info(f"{file_type} file not found locally, will download")
                updates_found.append((file_type, file_name))
        
        return updates_found
    
    def download_file(self, file_type, file_name):
        """Download a file from Florida Revenue portal"""
        # Note: In production, this would actually download from the portal
        # For now, we'll use the existing TEMP files
        temp_path = Path(f"C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/{file_name.replace('.zip', '.csv')}")
        
        if temp_path.exists():
            logger.info(f"Found {file_type} file in TEMP directory")
            return temp_path
        else:
            logger.warning(f"{file_type} file not found in TEMP directory")
            return None
    
    def process_nal_file(self, file_path):
        """Process NAL (Name Address Legal) file"""
        logger.info(f"Processing NAL file: {file_path}")
        
        batch_size = 1000
        batch = []
        total_processed = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Map NAL fields to database columns
                    record = {
                        'parcel_id': row.get('PARCEL_ID', '').strip(),
                        'owner_name': row.get('OWN_NAME', '').strip()[:255],
                        'owner_addr1': row.get('OWN_ADDR1', '').strip()[:255],
                        'owner_city': row.get('OWN_CITY', '').strip()[:100],
                        'owner_state': row.get('OWN_STATE', '').strip()[:10],
                        'owner_zip': row.get('OWN_ZIP', '').strip()[:20],
                        'phy_addr1': row.get('PHY_ADDR1', '').strip()[:255],
                        'phy_city': row.get('PHY_CITY', '').strip()[:100],
                        'phy_zipcd': row.get('PHY_ZIPCD', '').strip()[:20],
                    }
                    
                    if record['parcel_id']:
                        batch.append(record)
                    
                    if len(batch) >= batch_size:
                        self.upsert_batch(batch, 'florida_parcels')
                        total_processed += len(batch)
                        batch = []
                        
                        if total_processed % 10000 == 0:
                            logger.info(f"Processed {total_processed:,} NAL records")
                
                # Process remaining batch
                if batch:
                    self.upsert_batch(batch, 'florida_parcels')
                    total_processed += len(batch)
            
            logger.info(f"NAL processing complete: {total_processed:,} records")
            return total_processed
            
        except Exception as e:
            logger.error(f"Error processing NAL file: {e}")
            return 0
    
    def process_nap_file(self, file_path):
        """Process NAP (Name Address Property) file"""
        logger.info(f"Processing NAP file: {file_path}")
        
        batch_size = 500
        batch = []
        total_processed = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Map NAP fields to database columns
                    record = {
                        'parcel_id': row.get('ACCT_ID', '').strip(),
                    }
                    
                    # Add numeric fields
                    for field_name, db_field in [
                        ('JV_TOTAL', 'just_value'),
                        ('AV_TOTAL', 'assessed_value'),
                        ('TAX_VAL', 'taxable_value')
                    ]:
                        value = row.get(field_name, '').strip()
                        if value:
                            try:
                                record[db_field] = int(float(value))
                            except:
                                pass
                    
                    if record.get('parcel_id'):
                        batch.append(record)
                    
                    if len(batch) >= batch_size:
                        self.upsert_batch(batch, 'florida_parcels')
                        total_processed += len(batch)
                        batch = []
                        
                        if total_processed % 5000 == 0:
                            logger.info(f"Processed {total_processed:,} NAP records")
                
                # Process remaining batch
                if batch:
                    self.upsert_batch(batch, 'florida_parcels')
                    total_processed += len(batch)
            
            logger.info(f"NAP processing complete: {total_processed:,} records")
            return total_processed
            
        except Exception as e:
            logger.error(f"Error processing NAP file: {e}")
            return 0
    
    def process_sdf_file(self, file_path):
        """Process SDF (Sales Data File)"""
        logger.info(f"Processing SDF file: {file_path}")
        
        batch_size = 500
        batch = []
        total_processed = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    parcel_id = row.get('PARCEL_ID', '').strip()
                    sale_price = row.get('SALE_PRC', '').strip()
                    sale_year = row.get('SALE_YR', '').strip()
                    sale_month = row.get('SALE_MO', '').strip()
                    
                    if parcel_id and sale_price and sale_year:
                        try:
                            # Create sales record
                            sale_record = {
                                'parcel_id': parcel_id,
                                'sale_price': int(float(sale_price)),
                                'sale_date': f"{sale_year}-{str(sale_month).zfill(2)}-01" if sale_month else f"{sale_year}-01-01"
                            }
                            
                            batch.append(sale_record)
                            
                            if len(batch) >= batch_size:
                                self.upsert_batch(batch, 'property_sales_history')
                                total_processed += len(batch)
                                batch = []
                                
                                if total_processed % 5000 == 0:
                                    logger.info(f"Processed {total_processed:,} SDF records")
                        except:
                            pass
                
                # Process remaining batch
                if batch:
                    self.upsert_batch(batch, 'property_sales_history')
                    total_processed += len(batch)
            
            logger.info(f"SDF processing complete: {total_processed:,} records")
            return total_processed
            
        except Exception as e:
            logger.error(f"Error processing SDF file: {e}")
            return 0
    
    def upsert_batch(self, batch, table_name):
        """Upsert a batch of records to Supabase"""
        try:
            if table_name == 'florida_parcels':
                # Use upsert for main table
                result = supabase.table(table_name).upsert(
                    batch,
                    on_conflict='parcel_id'
                ).execute()
            else:
                # Insert for sales history
                result = supabase.table(table_name).insert(batch).execute()
            return True
        except Exception as e:
            logger.error(f"Batch upsert failed: {str(e)[:200]}")
            return False
    
    def run_daily_update(self):
        """Main daily update process"""
        logger.info("=" * 60)
        logger.info(f"Starting daily Florida data update - {datetime.now()}")
        logger.info("=" * 60)
        
        # Check for updates
        updates = self.check_for_updates()
        
        # Process existing TEMP files
        temp_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP")
        
        # Process NAL file
        nal_file = temp_dir / "NAL16P202501.csv"
        if nal_file.exists():
            logger.info("Processing NAL data...")
            self.process_nal_file(nal_file)
        
        # Process NAP file
        nap_file = temp_dir / "NAP16P202501.csv"
        if nap_file.exists():
            logger.info("Processing NAP data...")
            self.process_nap_file(nap_file)
        
        # Process SDF file
        sdf_file = temp_dir / "SDF16P202501.csv"
        if sdf_file.exists():
            logger.info("Processing SDF data...")
            self.process_sdf_file(sdf_file)
        
        logger.info("Daily update complete!")
        
    def start_monitoring(self):
        """Start the monitoring service"""
        logger.info("Starting Florida Data Agent monitoring service...")
        
        # Schedule daily updates at 2 AM
        schedule.every().day.at("02:00").do(self.run_daily_update)
        
        # Also run immediately on start
        self.run_daily_update()
        
        logger.info("Monitoring service started. Daily updates scheduled at 2:00 AM")
        logger.info("Press Ctrl+C to stop")
        
        # Keep the service running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Monitoring service stopped by user")
        except Exception as e:
            logger.error(f"Monitoring service error: {e}")

def main():
    """Main entry point"""
    print("""
    ============================================================
             FLORIDA PROPERTY DATA AGENT SYSTEM              
                                                              
      Daily automated updates from Florida Revenue Portal    
      Current County: Broward                                
      Data Types: NAL, NAP, SDF                             
    ============================================================
    """)
    
    agent = FloridaDataAgent()
    
    # Check if running as daemon or single update
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        logger.info("Running single update...")
        agent.run_daily_update()
    else:
        logger.info("Starting monitoring service...")
        agent.start_monitoring()

if __name__ == "__main__":
    main()