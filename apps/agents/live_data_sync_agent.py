"""
Live Data Sync Agent
Monitors and synchronizes data between Supabase and the website in real-time
"""

import os
import json
import asyncio
import websocket
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
import queue
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv('apps/web/.env')

class LiveDataSyncAgent:
    """
    Agent responsible for real-time data synchronization
    """
    
    def __init__(self):
        self.supabase = self._init_supabase()
        self.sync_queue = queue.Queue()
        self.active_subscriptions = {}
        self.sync_status = {}
        self.last_sync_times = {}
        self.error_log = []
        self.api_base_url = "http://localhost:8000"
        self.websocket_url = None
        self.is_running = False
        
    def _init_supabase(self):
        """Initialize Supabase connection"""
        url = os.getenv("VITE_SUPABASE_URL")
        key = os.getenv("VITE_SUPABASE_ANON_KEY")
        if url and key:
            self.websocket_url = url.replace('https://', 'wss://') + '/realtime/v1/websocket'
            return create_client(url, key)
        return None
    
    def start_monitoring(self, tables: List[str] = None) -> None:
        """
        Start monitoring specified tables for changes
        """
        if not tables:
            tables = ['florida_parcels', 'property_sales_history', 'nav_assessments']
        
        self.is_running = True
        print(f"[Live Data Sync Agent] Starting monitoring for tables: {tables}")
        
        # Start sync threads
        sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        sync_thread.start()
        
        # Start monitoring threads for each table
        for table in tables:
            monitor_thread = threading.Thread(
                target=self._monitor_table,
                args=(table,),
                daemon=True
            )
            monitor_thread.start()
            self.active_subscriptions[table] = {
                'started': datetime.now(),
                'status': 'active',
                'changes_detected': 0
            }
        
        print(f"[Live Data Sync Agent] Monitoring started for {len(tables)} tables")
    
    def _monitor_table(self, table: str) -> None:
        """
        Monitor a specific table for changes
        """
        poll_interval = 5  # seconds
        last_check_time = datetime.now()
        
        while self.is_running:
            try:
                # Check for changes since last check
                changes = self._detect_changes(table, last_check_time)
                
                if changes:
                    print(f"[Live Data Sync Agent] Detected {len(changes)} changes in {table}")
                    
                    for change in changes:
                        self.sync_queue.put({
                            'table': table,
                            'operation': change['operation'],
                            'data': change['data'],
                            'timestamp': datetime.now()
                        })
                    
                    self.active_subscriptions[table]['changes_detected'] += len(changes)
                
                last_check_time = datetime.now()
                
            except Exception as e:
                self._log_error(table, str(e))
            
            # Wait before next check
            asyncio.run(asyncio.sleep(poll_interval))
    
    def _detect_changes(self, table: str, since: datetime) -> List[Dict]:
        """
        Detect changes in a table since a given time
        """
        changes = []
        
        try:
            # For demo purposes, we'll check for recently updated records
            # In production, you'd use Supabase Realtime or track update timestamps
            
            # Check if table has updated_at or similar field
            result = self.supabase.table(table).select('*').limit(10).execute()
            
            if result.data:
                # Simulate change detection
                for row in result.data[:2]:  # Check first 2 rows
                    if 'updated_at' in row:
                        updated = datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00'))
                        if updated > since:
                            changes.append({
                                'operation': 'UPDATE',
                                'data': row
                            })
                    else:
                        # Randomly simulate changes for demo
                        import random
                        if random.random() < 0.1:  # 10% chance
                            changes.append({
                                'operation': 'UPDATE',
                                'data': row
                            })
        
        except Exception as e:
            self._log_error(table, f"Error detecting changes: {str(e)}")
        
        return changes
    
    def _sync_worker(self) -> None:
        """
        Worker thread that processes sync queue
        """
        while self.is_running:
            try:
                if not self.sync_queue.empty():
                    sync_item = self.sync_queue.get(timeout=1)
                    self._process_sync(sync_item)
                else:
                    threading.Event().wait(0.1)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[Live Data Sync Agent] Sync error: {e}")
    
    def _process_sync(self, sync_item: Dict) -> None:
        """
        Process a sync item and update the website
        """
        table = sync_item['table']
        operation = sync_item['operation']
        data = sync_item['data']
        
        print(f"[Live Data Sync Agent] Processing {operation} for {table}")
        
        try:
            # Determine affected UI elements
            affected_elements = self._get_affected_elements(table, data)
            
            # Prepare update payload
            update_payload = self._prepare_update_payload(data, affected_elements)
            
            # Send updates to frontend via API
            self._send_updates_to_frontend(update_payload)
            
            # Update sync status
            self.sync_status[table] = {
                'last_sync': datetime.now().isoformat(),
                'operation': operation,
                'success': True
            }
            
        except Exception as e:
            self._log_error(table, f"Sync failed: {str(e)}")
            self.sync_status[table] = {
                'last_sync': datetime.now().isoformat(),
                'operation': operation,
                'success': False,
                'error': str(e)
            }
    
    def _get_affected_elements(self, table: str, data: Dict) -> List[str]:
        """
        Determine which UI elements are affected by the data change
        """
        affected = []
        
        # Map tables to UI elements
        table_element_map = {
            'florida_parcels': [
                f"property-card-{data.get('parcel_id', '')}-*",
                f"property-profile-*",
                f"overview-*",
                f"core-*",
                f"tax-*"
            ],
            'property_sales_history': [
                f"sales-*",
                f"property-card-{data.get('parcel_id', '')}-sale-*"
            ],
            'nav_assessments': [
                f"tax-nav-*",
                f"nav-assessment-*"
            ]
        }
        
        if table in table_element_map:
            affected.extend(table_element_map[table])
        
        return affected
    
    def _prepare_update_payload(self, data: Dict, affected_elements: List[str]) -> Dict:
        """
        Prepare the update payload for frontend
        """
        # Import the mapping agent to transform values
        from data_mapping_agent import DataMappingAgent
        mapper = DataMappingAgent()
        mapper.create_field_mappings()
        
        updates = {}
        
        for element_pattern in affected_elements:
            # Get the field name from element pattern
            field_mappings = {
                'address': 'phy_addr1',
                'city': 'phy_city',
                'owner': 'owner_name',
                'just-value': 'just_value',
                'taxable-value': 'taxable_value',
                'land-value': 'land_value',
                'building-sqft': 'total_living_area',
                'year-built': 'year_built',
                'sale-price': 'sale_price',
                'sale-date': 'sale_date'
            }
            
            for ui_field, db_field in field_mappings.items():
                if ui_field in element_pattern and db_field in data:
                    # Transform the value
                    transformed_value = mapper.transform_value(
                        ui_field.replace('-', '_'),
                        data[db_field]
                    )
                    
                    element_id = element_pattern.replace('*', ui_field)
                    updates[element_id] = {
                        'value': transformed_value,
                        'raw_value': data[db_field],
                        'field': db_field
                    }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'updates': updates,
            'source': 'LiveDataSyncAgent'
        }
    
    def _send_updates_to_frontend(self, payload: Dict) -> None:
        """
        Send updates to the frontend via API or WebSocket
        """
        try:
            # Send via API endpoint
            response = requests.post(
                f"{self.api_base_url}/api/live-updates",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"[Live Data Sync Agent] Sent {len(payload['updates'])} updates to frontend")
            else:
                print(f"[Live Data Sync Agent] Failed to send updates: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            # API might not have the live-updates endpoint yet
            # Store updates for later or use alternative method
            self._store_pending_updates(payload)
        except Exception as e:
            self._log_error('frontend_sync', str(e))
    
    def _store_pending_updates(self, payload: Dict) -> None:
        """
        Store updates that couldn't be sent immediately
        """
        pending_file = 'pending_updates.json'
        
        try:
            if os.path.exists(pending_file):
                with open(pending_file, 'r') as f:
                    pending = json.load(f)
            else:
                pending = []
            
            pending.append(payload)
            
            # Keep only last 100 updates
            if len(pending) > 100:
                pending = pending[-100:]
            
            with open(pending_file, 'w') as f:
                json.dump(pending, f, indent=2)
                
        except Exception as e:
            self._log_error('pending_updates', str(e))
    
    def force_sync(self, table: str, parcel_ids: List[str] = None) -> Dict:
        """
        Force synchronization for specific records
        """
        print(f"[Live Data Sync Agent] Force sync initiated for {table}")
        
        sync_results = {
            'table': table,
            'started': datetime.now().isoformat(),
            'records_synced': 0,
            'errors': []
        }
        
        try:
            # Build query
            query = self.supabase.table(table).select('*')
            
            if parcel_ids:
                query = query.in_('parcel_id', parcel_ids)
            else:
                query = query.limit(100)
            
            result = query.execute()
            
            if result.data:
                for record in result.data:
                    try:
                        # Add to sync queue
                        self.sync_queue.put({
                            'table': table,
                            'operation': 'FORCE_SYNC',
                            'data': record,
                            'timestamp': datetime.now()
                        })
                        sync_results['records_synced'] += 1
                        
                    except Exception as e:
                        sync_results['errors'].append({
                            'record': record.get('parcel_id', 'unknown'),
                            'error': str(e)
                        })
            
            sync_results['completed'] = datetime.now().isoformat()
            
        except Exception as e:
            sync_results['errors'].append({
                'general_error': str(e)
            })
        
        return sync_results
    
    def get_sync_status(self) -> Dict:
        """
        Get current sync status for all monitored tables
        """
        status = {
            'agent_status': 'running' if self.is_running else 'stopped',
            'monitored_tables': list(self.active_subscriptions.keys()),
            'subscriptions': self.active_subscriptions,
            'recent_syncs': self.sync_status,
            'queue_size': self.sync_queue.qsize(),
            'error_count': len(self.error_log),
            'recent_errors': self.error_log[-10:]  # Last 10 errors
        }
        
        return status
    
    def _log_error(self, context: str, error: str) -> None:
        """
        Log an error
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'error': error
        }
        
        self.error_log.append(error_entry)
        
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]
        
        print(f"[Live Data Sync Agent] Error in {context}: {error}")
    
    def stop_monitoring(self) -> None:
        """
        Stop all monitoring activities
        """
        self.is_running = False
        print("[Live Data Sync Agent] Stopping monitoring...")
        
        # Clear queue
        while not self.sync_queue.empty():
            try:
                self.sync_queue.get_nowait()
            except:
                break
        
        # Update subscription status
        for table in self.active_subscriptions:
            self.active_subscriptions[table]['status'] = 'stopped'
        
        print("[Live Data Sync Agent] Monitoring stopped")
    
    def save_sync_report(self, output_path: str = "sync_status_report.json") -> None:
        """
        Save sync status report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_sync_status(),
            'sync_history': self.sync_status,
            'error_log': self.error_log
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[Live Data Sync Agent] Report saved to {output_path}")


def main():
    """
    Run the Live Data Sync Agent
    """
    agent = LiveDataSyncAgent()
    
    print("[Live Data Sync Agent] Initializing...")
    
    # Start monitoring
    agent.start_monitoring(['florida_parcels', 'property_sales_history'])
    
    # Run for a short demo period
    import time
    demo_duration = 10  # seconds
    
    print(f"[Live Data Sync Agent] Running for {demo_duration} seconds...")
    time.sleep(demo_duration)
    
    # Force sync some data
    print("\n[Live Data Sync Agent] Testing force sync...")
    sync_result = agent.force_sync('florida_parcels', ['504232100001', '504232100002'])
    print(f"  Synced {sync_result['records_synced']} records")
    
    # Get status
    status = agent.get_sync_status()
    print(f"\n[Live Data Sync Agent] Status:")
    print(f"  - Monitored tables: {len(status['monitored_tables'])}")
    print(f"  - Queue size: {status['queue_size']}")
    print(f"  - Errors: {status['error_count']}")
    
    # Save report
    agent.save_sync_report()
    
    # Stop monitoring
    agent.stop_monitoring()


if __name__ == "__main__":
    main()