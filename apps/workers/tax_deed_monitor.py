"""
Tax Deed Auction Monitor and Scheduler
=======================================
Monitors tax deed auctions and schedules regular scraping
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import os
import json
from dataclasses import asdict

from tax_deed_auction_scraper import TaxDeedAuctionScraper, Auction
from tax_deed_database import TaxDeedDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TaxDeedMonitor:
    """Monitor for tax deed auctions with scheduling and alerting"""
    
    def __init__(self):
        """Initialize the monitor"""
        self.db = TaxDeedDatabase()
        self.scraper = None
        self.alerts = []
        self.config = self.load_config()
        
    def load_config(self) -> Dict[str, Any]:
        """Load monitor configuration"""
        default_config = {
            'scrape_interval_hours': 6,  # Scrape every 6 hours
            'alert_thresholds': {
                'high_value_min': 100000,  # Alert for properties > $100k
                'homestead_alert': True,   # Alert for homestead properties
                'new_auction_alert': True,  # Alert for new auctions
                'canceled_threshold': 5    # Alert if > 5 properties canceled
            },
            'notification_channels': {
                'email': os.getenv('ALERT_EMAIL'),
                'webhook': os.getenv('ALERT_WEBHOOK_URL')
            }
        }
        
        # Try to load from file
        config_file = 'tax_deed_monitor_config.json'
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
                
        return default_config
        
    async def run_scraper(self) -> List[Auction]:
        """Run the scraper and return results"""
        try:
            async with TaxDeedAuctionScraper() as scraper:
                self.scraper = scraper
                auctions = await scraper.scrape_all_auctions()
                
                # Save to database
                save_results = await self.db.save_scraped_data(auctions)
                logger.info(f"Saved {save_results['auctions_saved']} auctions, "
                          f"{save_results['properties_saved']} properties")
                
                # Save to JSON backup
                scraper.save_to_json(auctions, 
                                   f'tax_deed_auctions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                
                return auctions
                
        except Exception as e:
            logger.error(f"Error running scraper: {e}")
            return []
            
    async def check_for_changes(self, new_auctions: List[Auction]) -> Dict[str, Any]:
        """Check for changes in auctions and properties"""
        changes = {
            'new_auctions': [],
            'new_properties': [],
            'canceled_properties': [],
            'status_changes': [],
            'bid_updates': [],
            'high_value_properties': [],
            'homestead_properties': []
        }
        
        try:
            for auction in new_auctions:
                # Check if auction is new
                existing_auction = await self.db.get_auction(auction.auction_id)
                
                if not existing_auction:
                    changes['new_auctions'].append({
                        'auction_id': auction.auction_id,
                        'description': auction.description,
                        'date': auction.auction_date.isoformat() if auction.auction_date else None,
                        'total_items': auction.total_items
                    })
                    
                # Check properties
                for prop in auction.properties:
                    # Check for high value properties
                    if prop.opening_bid >= self.config['alert_thresholds']['high_value_min']:
                        changes['high_value_properties'].append({
                            'auction': auction.description,
                            'tax_deed': prop.tax_deed_number,
                            'address': prop.situs_address,
                            'opening_bid': prop.opening_bid,
                            'parcel': prop.parcel_number
                        })
                        
                    # Check for homestead properties
                    if prop.homestead:
                        changes['homestead_properties'].append({
                            'auction': auction.description,
                            'tax_deed': prop.tax_deed_number,
                            'address': prop.situs_address,
                            'opening_bid': prop.opening_bid,
                            'parcel': prop.parcel_number
                        })
                        
                    # Check for status changes
                    if existing_auction:
                        existing_props = await self.db.get_auction_properties(auction.auction_id)
                        existing_prop = next((p for p in existing_props 
                                            if p['item_id'] == prop.item_id), None)
                        
                        if existing_prop:
                            # Check for status change
                            if existing_prop['status'] != prop.status.value:
                                changes['status_changes'].append({
                                    'auction': auction.description,
                                    'tax_deed': prop.tax_deed_number,
                                    'address': prop.situs_address,
                                    'old_status': existing_prop['status'],
                                    'new_status': prop.status.value
                                })
                                
                                if prop.status.value == 'Canceled':
                                    changes['canceled_properties'].append({
                                        'auction': auction.description,
                                        'tax_deed': prop.tax_deed_number,
                                        'address': prop.situs_address,
                                        'opening_bid': prop.opening_bid
                                    })
                                    
                            # Check for bid updates
                            if prop.best_bid and prop.best_bid != existing_prop.get('best_bid'):
                                changes['bid_updates'].append({
                                    'auction': auction.description,
                                    'tax_deed': prop.tax_deed_number,
                                    'address': prop.situs_address,
                                    'old_bid': existing_prop.get('best_bid'),
                                    'new_bid': prop.best_bid
                                })
                        else:
                            # New property
                            changes['new_properties'].append({
                                'auction': auction.description,
                                'tax_deed': prop.tax_deed_number,
                                'address': prop.situs_address,
                                'opening_bid': prop.opening_bid,
                                'parcel': prop.parcel_number
                            })
                            
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
            
        return changes
        
    async def send_alerts(self, changes: Dict[str, Any]):
        """Send alerts for significant changes"""
        alerts_to_send = []
        
        # New auctions alert
        if changes['new_auctions'] and self.config['alert_thresholds']['new_auction_alert']:
            for auction in changes['new_auctions']:
                alert = {
                    'type': 'NEW_AUCTION',
                    'priority': 'HIGH',
                    'title': f"New Tax Deed Auction: {auction['description']}",
                    'details': f"Date: {auction['date']}\nTotal Items: {auction['total_items']}"
                }
                alerts_to_send.append(alert)
                
        # High value properties alert
        if changes['high_value_properties']:
            for prop in changes['high_value_properties']:
                alert = {
                    'type': 'HIGH_VALUE_PROPERTY',
                    'priority': 'HIGH',
                    'title': f"High Value Property: ${prop['opening_bid']:,.2f}",
                    'details': f"Auction: {prop['auction']}\n"
                              f"Tax Deed: {prop['tax_deed']}\n"
                              f"Address: {prop['address']}\n"
                              f"Parcel: {prop['parcel']}"
                }
                alerts_to_send.append(alert)
                
        # Homestead properties alert
        if changes['homestead_properties'] and self.config['alert_thresholds']['homestead_alert']:
            for prop in changes['homestead_properties']:
                alert = {
                    'type': 'HOMESTEAD_PROPERTY',
                    'priority': 'MEDIUM',
                    'title': f"Homestead Property Available",
                    'details': f"Auction: {prop['auction']}\n"
                              f"Tax Deed: {prop['tax_deed']}\n"
                              f"Address: {prop['address']}\n"
                              f"Opening Bid: ${prop['opening_bid']:,.2f}"
                }
                alerts_to_send.append(alert)
                
        # Mass cancellation alert
        if len(changes['canceled_properties']) >= self.config['alert_thresholds']['canceled_threshold']:
            alert = {
                'type': 'MASS_CANCELLATION',
                'priority': 'HIGH',
                'title': f"{len(changes['canceled_properties'])} Properties Canceled",
                'details': "Multiple properties have been canceled. Check the system for details."
            }
            alerts_to_send.append(alert)
            
        # Send alerts
        for alert in alerts_to_send:
            await self.send_alert(alert)
            
    async def send_alert(self, alert: Dict[str, Any]):
        """Send individual alert through configured channels"""
        try:
            logger.info(f"Alert: {alert['title']}")
            
            # Add to alerts list
            alert['timestamp'] = datetime.now(timezone.utc).isoformat()
            self.alerts.append(alert)
            
            # Send to webhook if configured
            if self.config['notification_channels'].get('webhook'):
                # Would implement webhook sending here
                pass
                
            # Log alert to file
            with open('tax_deed_alerts.jsonl', 'a') as f:
                f.write(json.dumps(alert) + '\n')
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            
    async def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting tax deed auction monitor...")
        
        while True:
            try:
                logger.info("Running scheduled scrape...")
                
                # Run scraper
                auctions = await self.run_scraper()
                
                if auctions:
                    # Check for changes
                    changes = await self.check_for_changes(auctions)
                    
                    # Send alerts
                    await self.send_alerts(changes)
                    
                    # Generate report
                    await self.generate_report(auctions, changes)
                    
                # Wait for next interval
                interval_seconds = self.config['scrape_interval_hours'] * 3600
                logger.info(f"Next scrape in {self.config['scrape_interval_hours']} hours")
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes
                
    async def generate_report(self, auctions: List[Auction], changes: Dict[str, Any]):
        """Generate summary report"""
        try:
            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_auctions': len(auctions),
                    'total_properties': sum(len(a.properties) for a in auctions),
                    'upcoming_properties': sum(
                        len([p for p in a.properties if p.status.value == 'Upcoming']) 
                        for a in auctions
                    ),
                    'canceled_properties': sum(
                        len([p for p in a.properties if p.status.value == 'Canceled']) 
                        for a in auctions
                    )
                },
                'changes': {
                    'new_auctions': len(changes['new_auctions']),
                    'new_properties': len(changes['new_properties']),
                    'canceled_properties': len(changes['canceled_properties']),
                    'status_changes': len(changes['status_changes']),
                    'bid_updates': len(changes['bid_updates'])
                },
                'high_value_properties': changes['high_value_properties'],
                'homestead_properties': changes['homestead_properties']
            }
            
            # Save report
            report_file = f'tax_deed_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Report saved to {report_file}")
            
            # Also save latest report
            with open('tax_deed_latest_report.json', 'w') as f:
                json.dump(report, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            
    async def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        try:
            upcoming_auctions = await self.db.get_upcoming_auctions()
            
            stats = {
                'upcoming_auctions': len(upcoming_auctions),
                'total_upcoming_properties': 0,
                'high_value_properties': [],
                'homestead_properties': [],
                'recent_alerts': self.alerts[-10:]  # Last 10 alerts
            }
            
            for auction in upcoming_auctions:
                auction_stats = await self.db.get_auction_statistics(auction['auction_id'])
                stats['total_upcoming_properties'] += auction_stats.get('upcoming', 0)
                
            # Get high value and homestead properties
            stats['high_value_properties'] = await self.db.get_high_value_properties()
            stats['homestead_properties'] = await self.db.get_homestead_properties()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
            
async def main():
    """Main function"""
    monitor = TaxDeedMonitor()
    
    # Run initial scrape
    logger.info("Running initial scrape...")
    auctions = await monitor.run_scraper()
    
    if auctions:
        logger.info(f"Initial scrape completed: {len(auctions)} auctions found")
        
        # Check for interesting properties
        changes = await monitor.check_for_changes(auctions)
        await monitor.send_alerts(changes)
        await monitor.generate_report(auctions, changes)
        
        # Get statistics
        stats = await monitor.get_statistics()
        logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    # Start monitoring loop
    # await monitor.monitor_loop()
    
if __name__ == "__main__":
    asyncio.run(main())