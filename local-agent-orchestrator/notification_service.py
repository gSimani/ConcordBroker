#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Channel Notification Service
Sends agent alerts via Email, SMS, and Slack
"""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv('.env.mcp')

class NotificationService:
    """
    Multi-channel notification service for agent alerts
    Supports: Email (SMTP), SMS (Twilio), Slack (webhooks)
    """

    def __init__(self):
        # Email configuration (SMTP)
        self.email_enabled = os.getenv('NOTIFICATIONS_EMAIL_ENABLED', 'false').lower() == 'true'
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', self.smtp_user)
        self.email_recipients = os.getenv('NOTIFICATION_EMAIL_RECIPIENTS', '').split(',')

        # SMS configuration (Twilio)
        self.sms_enabled = os.getenv('NOTIFICATIONS_SMS_ENABLED', 'false').lower() == 'true'
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        self.sms_recipients = os.getenv('NOTIFICATION_SMS_RECIPIENTS', '').split(',')

        # Slack configuration (webhooks)
        self.slack_enabled = os.getenv('NOTIFICATIONS_SLACK_ENABLED', 'false').lower() == 'true'
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL', '')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#agent-alerts')

        # Notification routing by severity
        self.severity_channels = {
            'low': [],  # No notifications for low severity
            'medium': ['slack'],  # Slack only for medium
            'high': ['email', 'slack'],  # Email + Slack for high
            'critical': ['email', 'sms', 'slack']  # All channels for critical
        }

        print("\n" + "="*70)
        print("  📢 MULTI-CHANNEL NOTIFICATION SERVICE")
        print("="*70)
        print()
        print("  Channels configured:")
        print(f"    📧 Email: {'✅ Enabled' if self.email_enabled else '❌ Disabled'}")
        if self.email_enabled:
            print(f"       Recipients: {len([r for r in self.email_recipients if r])}")
        print(f"    📱 SMS: {'✅ Enabled' if self.sms_enabled else '❌ Disabled'}")
        if self.sms_enabled:
            print(f"       Recipients: {len([r for r in self.sms_recipients if r])}")
        print(f"    💬 Slack: {'✅ Enabled' if self.slack_enabled else '❌ Disabled'}")
        if self.slack_enabled:
            print(f"       Channel: {self.slack_channel}")
        print()
        print("  Routing rules:")
        print("    LOW → (no notifications)")
        print("    MEDIUM → Slack")
        print("    HIGH → Email + Slack")
        print("    CRITICAL → Email + SMS + Slack")
        print()
        print("="*70)
        print()

    def send_email(self, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email notification via SMTP"""
        if not self.email_enabled:
            return False

        if not self.smtp_user or not self.smtp_password:
            print("  ⚠️  Email credentials not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join([r for r in self.email_recipients if r])

            # Add plain text and HTML parts
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            print(f"  ✅ Email sent: {subject}")
            return True

        except Exception as e:
            print(f"  ❌ Email failed: {e}")
            return False

    def send_sms(self, message: str) -> bool:
        """Send SMS notification via Twilio"""
        if not self.sms_enabled:
            return False

        if not self.twilio_account_sid or not self.twilio_auth_token:
            print("  ⚠️  Twilio credentials not configured")
            return False

        try:
            # Twilio API endpoint
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"

            # Send to each recipient
            success_count = 0
            for recipient in [r for r in self.sms_recipients if r]:
                data = {
                    'From': self.twilio_from_number,
                    'To': recipient,
                    'Body': message[:160]  # SMS limit
                }

                response = requests.post(
                    url,
                    data=data,
                    auth=(self.twilio_account_sid, self.twilio_auth_token)
                )

                if response.status_code == 201:
                    success_count += 1

            if success_count > 0:
                print(f"  ✅ SMS sent to {success_count} recipient(s)")
                return True
            else:
                print("  ❌ SMS failed for all recipients")
                return False

        except Exception as e:
            print(f"  ❌ SMS failed: {e}")
            return False

    def send_slack(self, message: str, severity: str = 'info') -> bool:
        """Send Slack notification via webhook"""
        if not self.slack_enabled:
            return False

        if not self.slack_webhook_url:
            print("  ⚠️  Slack webhook URL not configured")
            return False

        try:
            # Color coding by severity
            colors = {
                'low': '#3498db',      # Blue
                'medium': '#f39c12',   # Yellow
                'high': '#e67e22',     # Orange
                'critical': '#e74c3c'  # Red
            }

            # Emoji by severity
            emojis = {
                'low': ':information_source:',
                'medium': ':warning:',
                'high': ':exclamation:',
                'critical': ':rotating_light:'
            }

            # Build Slack message
            payload = {
                'channel': self.slack_channel,
                'username': 'Agent System',
                'icon_emoji': ':robot_face:',
                'attachments': [{
                    'color': colors.get(severity, '#95a5a6'),
                    'title': f"{emojis.get(severity, ':bell:')} Agent Alert - {severity.upper()}",
                    'text': message,
                    'footer': 'ConcordBroker Autonomous Agent System',
                    'ts': int(datetime.now().timestamp())
                }]
            }

            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                print(f"  ✅ Slack message sent")
                return True
            else:
                print(f"  ❌ Slack failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"  ❌ Slack failed: {e}")
            return False

    def notify(self, alert: Dict) -> Dict[str, bool]:
        """
        Send notification via appropriate channels based on severity

        Args:
            alert: Dictionary with keys:
                - severity: 'low', 'medium', 'high', 'critical'
                - message: Alert message
                - agent_name: Name of agent that generated alert
                - alert_type: Type of alert
                - metadata: Optional additional data

        Returns:
            Dictionary with channel success status
        """
        severity = alert.get('severity', 'medium').lower()
        message = alert.get('message', 'Unknown alert')
        agent_name = alert.get('agent_name', 'Unknown Agent')
        alert_type = alert.get('alert_type', 'generic')

        print(f"\n  📢 Routing {severity.upper()} alert from {agent_name}")

        # Determine which channels to use
        channels = self.severity_channels.get(severity, [])

        if not channels:
            print(f"  ℹ️  No notifications for {severity} severity")
            return {}

        results = {}

        # Email
        if 'email' in channels and self.email_enabled:
            subject = f"[{severity.upper()}] Agent Alert: {alert_type}"

            # Plain text body
            body = f"""
ConcordBroker Agent System Alert

Severity: {severity.upper()}
Agent: {agent_name}
Type: {alert_type}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

---
This is an automated notification from the ConcordBroker autonomous agent system.
View live dashboard: http://localhost:5191/agents
"""

            # HTML body
            html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ padding: 20px; border-left: 4px solid {'#e74c3c' if severity == 'critical' else '#e67e22' if severity == 'high' else '#f39c12'}; background: #f9f9f9; }}
        .header {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
        .details {{ margin: 10px 0; }}
        .footer {{ margin-top: 20px; font-size: 12px; color: #7f8c8d; }}
    </style>
</head>
<body>
    <div class="alert">
        <div class="header">🤖 ConcordBroker Agent Alert</div>
        <div class="details">
            <p><strong>Severity:</strong> <span style="color: {'#e74c3c' if severity == 'critical' else '#e67e22' if severity == 'high' else '#f39c12'};">{severity.upper()}</span></p>
            <p><strong>Agent:</strong> {agent_name}</p>
            <p><strong>Type:</strong> {alert_type}</p>
            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 4px;">
            <strong>Message:</strong><br/>
            {message}
        </div>
        <div class="footer">
            This is an automated notification from the ConcordBroker autonomous agent system.<br/>
            <a href="http://localhost:5191/agents">View Live Dashboard</a>
        </div>
    </div>
</body>
</html>
"""

            results['email'] = self.send_email(subject, body, html_body)

        # SMS
        if 'sms' in channels and self.sms_enabled:
            sms_message = f"CONCORDBROKER [{severity.upper()}]: {agent_name} - {message[:100]}"
            results['sms'] = self.send_sms(sms_message)

        # Slack
        if 'slack' in channels and self.slack_enabled:
            slack_message = f"*{agent_name}* - {alert_type}\n{message}\n_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            results['slack'] = self.send_slack(slack_message, severity)

        return results

    def notify_agent_alert(self, agent_id: str, agent_name: str, alert_type: str,
                          severity: str, message: str, metadata: Optional[Dict] = None) -> Dict[str, bool]:
        """
        Convenient method to send agent alert notification

        Args:
            agent_id: Agent's unique ID
            agent_name: Agent's display name
            alert_type: Type of alert
            severity: Alert severity (low/medium/high/critical)
            message: Alert message
            metadata: Optional additional data

        Returns:
            Dictionary with channel success status
        """
        alert = {
            'agent_id': agent_id,
            'agent_name': agent_name,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'metadata': metadata or {}
        }

        return self.notify(alert)


def test_notification_service():
    """Test all notification channels"""
    print("\n" + "="*70)
    print("  🧪 TESTING NOTIFICATION SERVICE")
    print("="*70)
    print()

    service = NotificationService()

    # Test alerts of different severities
    test_alerts = [
        {
            'agent_name': 'Market Analysis Agent',
            'alert_type': 'market_weak',
            'severity': 'medium',
            'message': 'Market health score dropped below 40 in BROWARD county'
        },
        {
            'agent_name': 'Foreclosure Monitor',
            'alert_type': 'high_value_opportunity',
            'severity': 'high',
            'message': 'Found 5 high-value foreclosure opportunities totaling $2.3M'
        },
        {
            'agent_name': 'Property Data Monitor',
            'alert_type': 'data_stale',
            'severity': 'critical',
            'message': 'Property data is 60 days old. Immediate update required!'
        }
    ]

    for alert in test_alerts:
        print(f"\n  Testing {alert['severity'].upper()} alert...")
        results = service.notify(alert)

        if results:
            print(f"  Results:")
            for channel, success in results.items():
                print(f"    {channel}: {'✅ Success' if success else '❌ Failed'}")
        else:
            print("  ℹ️  No channels configured for this severity")

    print("\n" + "="*70)
    print("  ✅ Notification service test complete")
    print("="*70)
    print()


if __name__ == "__main__":
    # Test the notification service
    test_notification_service()
