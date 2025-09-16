"""
FLORIDA CLOUD UPDATER - Serverless/Container Ready
==================================================
Cloud-native version for automated daily updates.
Can be deployed as AWS Lambda, Google Cloud Function, or containerized service.
"""

import os
import io
import json
import logging
import psycopg2
import paramiko
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse
from io import StringIO
import boto3  # For AWS SNS notifications (optional)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class FloridaCloudUpdater:
    """Cloud-optimized daily updater"""
    
    def __init__(self):
        # Get config from environment variables (for cloud deployment)
        self.sftp_host = os.getenv('SFTP_HOST', 'sftp.floridados.gov')
        self.sftp_user = os.getenv('SFTP_USER', 'Public')
        self.sftp_pass = os.getenv('SFTP_PASS', 'PubAccess1845!')
        self.db_url = os.getenv('DATABASE_URL')
        
        # Notification settings (optional)
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
        self.webhook_url = os.getenv('WEBHOOK_URL')
        
        self.stats = {
            'files_processed': 0,
            'entities_created': 0,
            'entities_updated': 0,
            'errors': []
        }
    
    def get_db_connection(self):
        """Get database connection"""
        parsed = urlparse(self.db_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password.replace('%40', '@') if parsed.password else None,
            sslmode='require'
        )
    
    def process_daily_updates(self, event=None, context=None):
        """
        Main handler function - compatible with AWS Lambda
        
        Args:
            event: Lambda event object (optional)
            context: Lambda context object (optional)
        
        Returns:
            Dict with processing results
        """
        start_time = datetime.now()
        
        try:
            # Determine how many days back to check
            days_back = 1  # Default to yesterday's files
            if event and 'days_back' in event:
                days_back = int(event['days_back'])
            
            logger.info(f"Starting daily update for last {days_back} days")
            
            # Connect to SFTP
            transport = paramiko.Transport((self.sftp_host, 22))
            transport.connect(username=self.sftp_user, password=self.sftp_pass)
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Get and process daily files
            daily_files = self.find_daily_files(sftp, days_back)
            
            for file_info in daily_files:
                try:
                    self.process_file(sftp, file_info)
                except Exception as e:
                    self.stats['errors'].append({
                        'file': file_info['name'],
                        'error': str(e)
                    })
                    logger.error(f"Failed to process {file_info['name']}: {e}")
            
            # Cleanup
            sftp.close()
            transport.close()
            
            # Send notifications
            self.send_notifications()
            
            # Return results
            elapsed = (datetime.now() - start_time).total_seconds()
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'success': True,
                    'files_processed': self.stats['files_processed'],
                    'entities_created': self.stats['entities_created'],
                    'entities_updated': self.stats['entities_updated'],
                    'errors': len(self.stats['errors']),
                    'runtime_seconds': elapsed
                })
            }
            
        except Exception as e:
            logger.error(f"Critical error in daily update: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }
    
    def find_daily_files(self, sftp, days_back: int) -> List[Dict]:
        """Find daily files to process"""
        files_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Check standard directories
        directories = {
            '/Corporate_Data/Daily': 'corporate',
            '/Fictitious_Name_Data/Daily': 'fictitious',
            '/General_Partnership_Data/Daily': 'partnership',
            '/Federal_Tax_Lien_Data/Daily': 'lien',
            '/Mark_Data/Daily': 'mark'
        }
        
        conn = self.get_db_connection()
        
        for dir_path, data_type in directories.items():
            try:
                sftp.chdir(dir_path)
                files = sftp.listdir()
                
                for file_name in files:
                    if not file_name.endswith('.txt'):
                        continue
                    
                    # Parse date from filename
                    try:
                        file_date = datetime.strptime(file_name[:8], '%Y%m%d')
                        
                        if file_date >= cutoff_date:
                            # Check if already processed
                            with conn.cursor() as cur:
                                cur.execute("""
                                    SELECT EXISTS(
                                        SELECT 1 FROM florida_daily_processed_files 
                                        WHERE file_name = %s AND status = 'completed'
                                    )
                                """, (file_name,))
                                
                                if not cur.fetchone()[0]:
                                    files_to_process.append({
                                        'name': file_name,
                                        'path': f"{dir_path}/{file_name}",
                                        'type': data_type,
                                        'date': file_date
                                    })
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"Could not access {dir_path}: {e}")
        
        conn.close()
        return files_to_process
    
    def process_file(self, sftp, file_info: Dict):
        """Process a single file"""
        logger.info(f"Processing {file_info['name']}")
        
        # Read file into memory
        file_obj = io.BytesIO()
        sftp.getfo(file_info['path'], file_obj)
        file_obj.seek(0)
        
        # Parse and insert records
        conn = self.get_db_connection()
        records = []
        lines = file_obj.read().decode('utf-8', errors='ignore').splitlines()
        
        for line_num, line in enumerate(lines, 1):
            if len(line) < 100:
                continue
            
            record = self.parse_record_optimized(line, line_num, file_info)
            if record:
                records.append(record)
            
            # Batch insert
            if len(records) >= 1000:
                self.batch_upsert(conn, records)
                records = []
        
        # Final batch
        if records:
            self.batch_upsert(conn, records)
        
        # Mark as processed
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO florida_daily_processed_files 
                (file_name, file_type, file_date, records_processed, status)
                VALUES (%s, %s, %s, %s, 'completed')
            """, (file_info['name'], file_info['type'], file_info['date'], len(lines)))
            conn.commit()
        
        conn.close()
        self.stats['files_processed'] += 1
        logger.info(f"Completed {file_info['name']}: {len(lines)} records")
    
    def parse_record_optimized(self, line: str, line_num: int, file_info: Dict) -> Optional[Dict]:
        """Optimized parsing for cloud performance"""
        try:
            # Minimal parsing for speed
            entity_id = f"D{file_info['date'].strftime('%Y%m%d')}_{line[0:12].strip()}_{line_num}"[:50]
            business_name = line[12:212].strip()[:255]
            
            if not business_name:
                return None
            
            return {
                'entity_id': entity_id,
                'entity_type': line[218:219] if len(line) > 218 else 'C',
                'business_name': business_name,
                'entity_status': line[212:218].strip()[:50] if len(line) > 212 else 'ACTIVE',
                'business_city': line[338:388].strip()[:100] if len(line) > 338 else '',
                'business_state': line[388:390].strip()[:2] if len(line) > 388 else 'FL',
                'source_file': file_info['name']
            }
        except:
            return None
    
    def batch_upsert(self, conn, records: List[Dict]):
        """Efficient batch upsert"""
        if not records:
            return
        
        # Deduplicate
        seen = set()
        unique_records = []
        for r in records:
            if r['entity_id'] not in seen:
                seen.add(r['entity_id'])
                unique_records.append(r)
        
        # Use COPY for speed
        output = StringIO()
        for r in unique_records:
            row = [
                r['entity_id'],
                r.get('entity_type', 'C'),
                r['business_name'],
                r.get('entity_status', 'ACTIVE'),
                r.get('business_city', ''),
                r.get('business_state', 'FL'),
                r['source_file']
            ]
            output.write('\t'.join(str(v) for v in row) + '\n')
        
        output.seek(0)
        
        with conn.cursor() as cur:
            # Create temp table
            cur.execute("""
                CREATE TEMP TABLE IF NOT EXISTS temp_updates (
                    entity_id VARCHAR(50),
                    entity_type VARCHAR(10),
                    business_name VARCHAR(255),
                    entity_status VARCHAR(50),
                    business_city VARCHAR(100),
                    business_state VARCHAR(2),
                    source_file VARCHAR(255)
                )
            """)
            
            # Load data
            cur.copy_from(output, 'temp_updates', columns=(
                'entity_id', 'entity_type', 'business_name', 
                'entity_status', 'business_city', 'business_state', 'source_file'
            ))
            
            # Upsert
            cur.execute("""
                INSERT INTO florida_entities 
                (entity_id, entity_type, business_name, entity_status, 
                 business_city, business_state, source_file)
                SELECT * FROM temp_updates
                ON CONFLICT (entity_id) DO UPDATE SET
                    business_name = EXCLUDED.business_name,
                    entity_status = EXCLUDED.entity_status,
                    last_update_date = NOW()
            """)
            
            self.stats['entities_created'] += cur.rowcount
            
            # Clear temp table
            cur.execute("TRUNCATE temp_updates")
            conn.commit()
    
    def send_notifications(self):
        """Send completion notifications"""
        message = f"""
Florida Daily Update Complete:
- Files Processed: {self.stats['files_processed']}
- Entities Created: {self.stats['entities_created']}
- Entities Updated: {self.stats['entities_updated']}
- Errors: {len(self.stats['errors'])}
        """
        
        # AWS SNS notification
        if self.sns_topic_arn:
            try:
                sns = boto3.client('sns')
                sns.publish(
                    TopicArn=self.sns_topic_arn,
                    Subject='Florida Daily Update',
                    Message=message
                )
            except:
                pass
        
        # Webhook notification
        if self.webhook_url:
            try:
                import requests
                requests.post(self.webhook_url, json={
                    'text': message,
                    'stats': self.stats
                })
            except:
                pass

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda entry point"""
    updater = FloridaCloudUpdater()
    return updater.process_daily_updates(event, context)

# Google Cloud Function handler
def cloud_function_handler(request):
    """Google Cloud Function entry point"""
    updater = FloridaCloudUpdater()
    event = request.get_json() if request else {}
    return updater.process_daily_updates(event)

# Direct execution
if __name__ == "__main__":
    updater = FloridaCloudUpdater()
    result = updater.process_daily_updates()
    print(json.dumps(result, indent=2))