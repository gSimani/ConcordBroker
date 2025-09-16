"""
Florida Business Data Uploader to Supabase
Processes fixed-width records and uploads to structured database
"""

import os
import re
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_data_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FloridaDataUploader:
    def __init__(self):
        """Initialize the uploader with Supabase connection"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for bulk operations
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.database_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'records_processed': 0,
            'entities_created': 0,
            'contacts_created': 0,
            'errors': 0
        }
        
    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890, 123.456.7890, 1234567890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (123) 456-7890
            r'\b\d{3}\s+\d{3}\s+\d{4}\b',     # 123 456 7890
        ]
        
        phones = set()
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                clean_phone = re.sub(r'[^\d]', '', match)
                if len(clean_phone) == 10 or (len(clean_phone) == 11 and clean_phone.startswith('1')):
                    phones.add(match.strip())
        return list(phones)

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return list(set(email.strip().lower() for email in emails))

    def parse_fixed_width_record(self, line: str, record_type: str) -> Dict:
        """Parse fixed-width record based on type"""
        record = {}
        
        if record_type == 'corporation':
            # Parse corporation record (from 2011 format)
            if len(line) > 10:
                record.update({
                    'record_type': line[0:1].strip(),
                    'entity_id': line[1:12].strip(),
                    'business_name': line[12:132].strip(),
                    'entity_status': line[132:137].strip(),
                    'address_line1': line[137:217].strip(),
                    'city': line[217:247].strip(),
                    'state': line[247:249].strip(),
                    'zip_code': line[249:254].strip(),
                    'county': line[254:284].strip() if len(line) > 284 else '',
                })
        
        elif record_type == 'fictitious':
            # Parse fictitious name record (from 2014 format)  
            if len(line) > 10:
                record.update({
                    'record_type': 'G',
                    'entity_id': line[1:12].strip(),
                    'business_name': line[12:132].strip(),
                    'county': line[132:144].strip(),
                    'address_line1': line[144:224].strip(),
                    'city': line[224:264].strip(),
                    'state': line[264:266].strip(),
                    'zip_code': line[266:276].strip(),
                })
        
        return record

    def extract_entity_data(self, line: str, file_path: Path) -> Optional[Dict]:
        """Extract entity data from a record line"""
        try:
            # Determine record type based on file path
            if '/cor/' in str(file_path):
                record_type = 'corporation'
            elif '/fic/' in str(file_path):
                record_type = 'fictitious'
            else:
                record_type = 'general'
            
            # Parse the record
            record = self.parse_fixed_width_record(line, record_type)
            
            if not record.get('entity_id') or not record.get('business_name'):
                return None
            
            # Extract contact information from the full line
            phones = self.extract_phone_numbers(line)
            emails = self.extract_emails(line)
            
            entity_data = {
                'entity_id': record['entity_id'],
                'entity_type': record.get('record_type', 'U'),
                'business_name': record['business_name'][:255],  # Truncate if too long
                'entity_status': 'ACTIVE',  # Default assumption
                'business_address_line1': record.get('address_line1', '')[:255],
                'business_city': record.get('city', '')[:100],
                'business_state': record.get('state', 'FL'),
                'business_zip': record.get('zip_code', '')[:10],
                'business_county': record.get('county', '')[:50],
                'source_file': str(file_path.name),
                'registration_date': self._extract_date_from_filename(file_path.name),
            }
            
            # Extract contact data
            contacts = []
            for i, phone in enumerate(phones[:5]):  # Limit to 5 phones per entity
                contacts.append({
                    'entity_id': record['entity_id'],
                    'contact_type': 'PHONE',
                    'phone': phone,
                    'source_file': str(file_path.name),
                    'is_primary_contact': i == 0
                })
            
            for i, email in enumerate(emails[:5]):  # Limit to 5 emails per entity
                contacts.append({
                    'entity_id': record['entity_id'],
                    'contact_type': 'EMAIL',
                    'email': email,
                    'source_file': str(file_path.name),
                    'is_primary_contact': i == 0
                })
            
            return {
                'entity': entity_data,
                'contacts': contacts,
                'raw_content': line
            }
            
        except Exception as e:
            logger.error(f"Error parsing record from {file_path}: {e}")
            return None

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from filename like '20140102f.txt'"""
        try:
            # Extract date from filename pattern YYYYMMDD
            date_match = re.search(r'(\d{8})', filename)
            if date_match:
                date_str = date_match.group(1)
                # Convert to YYYY-MM-DD format
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            pass
        return None

    async def upload_batch(self, entities: List[Dict], contacts: List[Dict], raw_records: List[Dict]) -> bool:
        """Upload a batch of data to Supabase"""
        try:
            # Upload entities
            if entities:
                result = self.supabase.table('florida_entities').upsert(
                    entities,
                    on_conflict='entity_id'
                ).execute()
                
                if result.data:
                    self.stats['entities_created'] += len(result.data)
                    logger.info(f"Uploaded {len(result.data)} entities")

            # Upload contacts
            if contacts:
                result = self.supabase.table('florida_contacts').insert(contacts).execute()
                if result.data:
                    self.stats['contacts_created'] += len(result.data)
                    logger.info(f"Uploaded {len(result.data)} contacts")

            # Upload raw records for RAG
            if raw_records:
                result = self.supabase.table('florida_raw_records').insert(raw_records).execute()
                if result.data:
                    logger.info(f"Uploaded {len(result.data)} raw records")

            return True
            
        except Exception as e:
            logger.error(f"Error uploading batch: {e}")
            self.stats['errors'] += 1
            return False

    async def process_file(self, file_path: Path) -> bool:
        """Process a single file and upload its data"""
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Check if file already processed
            existing = self.supabase.table('florida_processing_log').select('*').eq('file_path', str(file_path)).execute()
            if existing.data and existing.data[0].get('processing_status') == 'COMPLETED':
                logger.info(f"File already processed: {file_path}")
                return True

            # Log processing start
            self.supabase.table('florida_processing_log').upsert({
                'file_path': str(file_path),
                'file_size': file_path.stat().st_size,
                'processing_status': 'PROCESSING',
                'started_at': datetime.now().isoformat()
            }, on_conflict='file_path').execute()

            entities_batch = []
            contacts_batch = []
            raw_records_batch = []
            batch_size = 100
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Extract data from line
                    data = self.extract_entity_data(line, file_path)
                    if not data:
                        continue
                    
                    entities_batch.append(data['entity'])
                    contacts_batch.extend(data['contacts'])
                    
                    # Add raw record for RAG
                    raw_records_batch.append({
                        'entity_id': data['entity']['entity_id'],
                        'raw_content': data['raw_content'],
                        'record_type': 'ENTITY',
                        'file_source': str(file_path.name)
                    })
                    
                    self.stats['records_processed'] += 1
                    
                    # Upload in batches
                    if len(entities_batch) >= batch_size:
                        success = await self.upload_batch(entities_batch, contacts_batch, raw_records_batch)
                        if not success:
                            break
                        
                        entities_batch = []
                        contacts_batch = []
                        raw_records_batch = []
                        
                        # Progress update
                        if line_num % 500 == 0:
                            logger.info(f"Processed {line_num} lines from {file_path.name}")

            # Upload remaining records
            if entities_batch:
                await self.upload_batch(entities_batch, contacts_batch, raw_records_batch)

            # Update processing log
            self.supabase.table('florida_processing_log').update({
                'processing_status': 'COMPLETED',
                'records_processed': line_num,
                'records_successful': line_num,
                'completed_at': datetime.now().isoformat()
            }).eq('file_path', str(file_path)).execute()

            self.stats['files_processed'] += 1
            logger.info(f"Completed processing: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            
            # Update processing log with error
            self.supabase.table('florida_processing_log').update({
                'processing_status': 'FAILED',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            }).eq('file_path', str(file_path)).execute()
            
            self.stats['errors'] += 1
            return False

    async def run(self, max_files: Optional[int] = None):
        """Main execution - process all files"""
        logger.info("Starting Florida data upload to Supabase")
        
        # Find all text files
        txt_files = list(self.database_path.rglob("*.txt"))
        logger.info(f"Found {len(txt_files)} total files")
        
        if max_files:
            txt_files = txt_files[:max_files]
            logger.info(f"Processing first {max_files} files")

        # Process files
        successful = 0
        for file_path in txt_files:
            try:
                success = await self.process_file(file_path)
                if success:
                    successful += 1
                    
                # Progress report every 10 files
                if self.stats['files_processed'] % 10 == 0:
                    logger.info(f"Progress: {self.stats['files_processed']}/{len(txt_files)} files processed")
                    self._print_stats()
                    
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        logger.info("Upload completed!")
        self._print_final_stats(len(txt_files), successful)

    def _print_stats(self):
        """Print current statistics"""
        logger.info(f"Stats: {json.dumps(self.stats, indent=2)}")

    def _print_final_stats(self, total_files: int, successful_files: int):
        """Print final statistics"""
        logger.info("=" * 60)
        logger.info("UPLOAD COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total files found: {total_files}")
        logger.info(f"Files processed successfully: {successful_files}")
        logger.info(f"Files failed: {total_files - successful_files}")
        logger.info(f"Records processed: {self.stats['records_processed']:,}")
        logger.info(f"Entities created: {self.stats['entities_created']:,}")
        logger.info(f"Contacts created: {self.stats['contacts_created']:,}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info("=" * 60)


async def main():
    """Main entry point"""
    uploader = FloridaDataUploader()
    
    # For testing, start with a small batch
    await uploader.run(max_files=50)  # Start with 50 files
    
    # To process all files, use:
    # await uploader.run()


if __name__ == "__main__":
    asyncio.run(main())