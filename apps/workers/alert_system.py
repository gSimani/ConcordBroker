"""
Alert and Notification System for Data Pipeline
Sends alerts when important data updates are detected
"""

import asyncio
import logging
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os

from rich.console import Console
from supabase_config import supabase_config

logger = logging.getLogger(__name__)
console = Console()

class AlertSystem:
    """Manages alerts and notifications for data updates"""
    
    def __init__(self):
        self.webhook_url = os.getenv('NOTIFICATION_WEBHOOK_URL')
        self.email_recipient = os.getenv('NOTIFICATION_EMAIL')
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.session = None
        self.alert_queue = []
        
    async def initialize(self):
        """Initialize alert system"""
        self.session = aiohttp.ClientSession()
        logger.info("Alert system initialized")
    
    async def send_alert(self, alert_type: str, title: str, message: str, 
                        data: Dict = None, priority: str = 'normal'):
        """Send an alert through configured channels"""
        
        alert = {
            'type': alert_type,
            'title': title,
            'message': message,
            'data': data or {},
            'priority': priority,
            'timestamp': datetime.now().isoformat()
        }
        
        # Add to queue
        self.alert_queue.append(alert)
        
        # Send based on priority
        if priority == 'high':
            await self.send_immediate(alert)
        else:
            # Batch low priority alerts
            if len(self.alert_queue) >= 10:
                await self.flush_alerts()
    
    async def send_immediate(self, alert: Dict):
        """Send alert immediately"""
        tasks = []
        
        if self.webhook_url:
            tasks.append(self.send_webhook(alert))
        
        if self.email_recipient:
            tasks.append(self.send_email(alert))
        
        await self.log_to_supabase(alert)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_webhook(self, alert: Dict):
        """Send alert to webhook (e.g., Slack)"""
        try:
            # Format for Slack
            payload = {
                'text': f"*{alert['title']}*",
                'attachments': [{
                    'color': self.get_alert_color(alert['priority']),
                    'fields': [
                        {'title': 'Type', 'value': alert['type'], 'short': True},
                        {'title': 'Priority', 'value': alert['priority'], 'short': True},
                        {'title': 'Message', 'value': alert['message']},
                        {'title': 'Time', 'value': alert['timestamp'], 'short': True}
                    ]
                }]
            }
            
            async with self.session.post(self.webhook_url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Webhook failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    async def send_email(self, alert: Dict):
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = self.email_recipient
            msg['Subject'] = f"[{alert['priority'].upper()}] {alert['title']}"
            
            body = f"""
            Alert Type: {alert['type']}
            Priority: {alert['priority']}
            Time: {alert['timestamp']}
            
            Message:
            {alert['message']}
            
            Data:
            {json.dumps(alert['data'], indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Email error: {e}")
    
    async def log_to_supabase(self, alert: Dict):
        """Log alert to Supabase for tracking"""
        try:
            pool = await supabase_config.get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO fl_alerts_log (
                        alert_type, title, message, priority,
                        data, sent_at, channels
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, alert['type'], alert['title'], alert['message'],
                    alert['priority'], json.dumps(alert['data']),
                    datetime.now(), ['webhook', 'email'])
                    
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
    
    def get_alert_color(self, priority: str) -> str:
        """Get color for alert based on priority"""
        colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'good',
            'normal': '#808080'
        }
        return colors.get(priority, '#808080')
    
    async def flush_alerts(self):
        """Send batched alerts"""
        if not self.alert_queue:
            return
        
        # Group alerts by type
        grouped = {}
        for alert in self.alert_queue:
            alert_type = alert['type']
            if alert_type not in grouped:
                grouped[alert_type] = []
            grouped[alert_type].append(alert)
        
        # Send grouped alerts
        for alert_type, alerts in grouped.items():
            summary = f"{len(alerts)} {alert_type} alerts"
            message = "\n".join([f"• {a['message']}" for a in alerts[:10]])
            
            await self.send_immediate({
                'type': 'batch',
                'title': summary,
                'message': message,
                'data': {'count': len(alerts)},
                'priority': 'normal',
                'timestamp': datetime.now().isoformat()
            })
        
        self.alert_queue.clear()
    
    async def close(self):
        """Close alert system"""
        await self.flush_alerts()
        if self.session:
            await self.session.close()

class DataUpdateAlerts:
    """Specific alerts for data pipeline updates"""
    
    def __init__(self, alert_system: AlertSystem):
        self.alerts = alert_system
    
    async def new_distressed_properties(self, properties: List[Dict]):
        """Alert on new distressed properties"""
        if not properties:
            return
        
        top_deals = properties[:5]
        message = f"Found {len(properties)} new distressed properties:\n"
        
        for prop in top_deals:
            message += f"• {prop['parcel_id']}: ${prop['sale_price']:,.0f} - {prop['qualification_description']}\n"
        
        await self.alerts.send_alert(
            alert_type='distressed_properties',
            title=f'🔥 {len(properties)} New Distressed Properties',
            message=message,
            data={'properties': top_deals},
            priority='high' if len(properties) > 10 else 'medium'
        )
    
    async def major_owner_activity(self, owner: str, activity: Dict):
        """Alert on major owner activity"""
        message = f"Major owner {owner} activity detected:\n"
        message += f"• Properties: {activity['property_count']}\n"
        message += f"• Total Value: ${activity['total_value']:,.0f}\n"
        
        if activity.get('new_acquisitions'):
            message += f"• New Acquisitions: {activity['new_acquisitions']}\n"
        
        await self.alerts.send_alert(
            alert_type='major_owner',
            title=f'👤 Major Owner Activity: {owner}',
            message=message,
            data=activity,
            priority='high' if activity['property_count'] > 100 else 'medium'
        )
    
    async def bank_sale_surge(self, stats: Dict):
        """Alert on surge in bank sales"""
        if stats['bank_sale_rate'] > 60:  # Over 60% bank sales
            message = f"Unusual bank sale activity detected:\n"
            message += f"• Bank Sale Rate: {stats['bank_sale_rate']:.1f}%\n"
            message += f"• Total Bank Sales: {stats['bank_sales']:,}\n"
            message += f"• Market Impact: Potential investment opportunities\n"
            
            await self.alerts.send_alert(
                alert_type='market_alert',
                title='🏦 Bank Sale Surge Detected',
                message=message,
                data=stats,
                priority='high'
            )
    
    async def flip_opportunity(self, flips: List[Dict]):
        """Alert on flip opportunities"""
        if not flips:
            return
        
        top_flips = sorted(flips, key=lambda x: x['roi_percent'], reverse=True)[:3]
        message = f"Found {len(flips)} potential flip opportunities:\n"
        
        for flip in top_flips:
            message += f"• {flip['parcel_id']}: ${flip['price_delta']:,.0f} profit ({flip['roi_percent']:.1f}% ROI) in {flip['days_held']} days\n"
        
        await self.alerts.send_alert(
            alert_type='flip_opportunity',
            title=f'💰 {len(flips)} Flip Opportunities Found',
            message=message,
            data={'flips': top_flips},
            priority='medium'
        )
    
    async def data_source_update(self, source: str, stats: Dict):
        """Alert on data source updates"""
        message = f"Data source {source} updated:\n"
        message += f"• New Records: {stats.get('new_records', 0):,}\n"
        message += f"• Updated Records: {stats.get('updated_records', 0):,}\n"
        message += f"• Total Processed: {stats.get('records_processed', 0):,}\n"
        
        await self.alerts.send_alert(
            alert_type='data_update',
            title=f'📊 {source} Data Updated',
            message=message,
            data=stats,
            priority='low'
        )
    
    async def agent_failure(self, agent_name: str, error: str):
        """Alert on agent failure"""
        await self.alerts.send_alert(
            alert_type='agent_failure',
            title=f'❌ Agent Failed: {agent_name}',
            message=f"Agent {agent_name} failed with error:\n{error}",
            data={'agent': agent_name, 'error': error},
            priority='high'
        )
    
    async def cdd_properties_found(self, properties: List[Dict]):
        """Alert on CDD properties"""
        if not properties:
            return
        
        message = f"Found {len(properties)} properties in CDDs:\n"
        total_assessment = sum(p.get('nav_assessment', 0) for p in properties)
        message += f"• Total NAV Assessment: ${total_assessment:,.0f}\n"
        message += f"• Average Assessment: ${total_assessment/len(properties):,.0f}\n"
        
        await self.alerts.send_alert(
            alert_type='cdd_properties',
            title=f'🏘️ {len(properties)} CDD Properties Found',
            message=message,
            data={'property_count': len(properties), 'total_assessment': total_assessment},
            priority='low'
        )