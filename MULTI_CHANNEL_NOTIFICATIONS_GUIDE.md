# 📢 Multi-Channel Notification System - Complete Guide

**Automated notifications from autonomous agents via Email, SMS, and Slack**

---

## 🎯 Overview

The Multi-Channel Notification System automatically sends alerts from your 11 autonomous agents through multiple channels based on severity levels.

### Notification Channels:
- 📧 **Email** (SMTP) - Professional HTML emails
- 📱 **SMS** (Twilio) - Instant text messages
- 💬 **Slack** (Webhooks) - Team collaboration alerts

### Smart Routing by Severity:
- **LOW**: No notifications (logged only)
- **MEDIUM**: Slack only
- **HIGH**: Email + Slack
- **CRITICAL**: Email + SMS + Slack (all channels)

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Slack Only (Easiest - FREE)

1. **Get Slack webhook URL** (2 minutes):
   - Go to https://api.slack.com/messaging/webhooks
   - Create app → "From scratch" → Name: "ConcordBroker Agents"
   - Enable "Incoming Webhooks"
   - Add webhook to #agent-alerts channel
   - Copy webhook URL

2. **Configure** (add to `.env.mcp`):
   ```bash
   NOTIFICATIONS_SLACK_ENABLED=true
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   SLACK_CHANNEL=#agent-alerts
   ```

3. **Test**:
   ```bash
   python local-agent-orchestrator/notification_service.py
   ```

4. **Done!** Your agents will now post to Slack automatically.

---

### Option 2: Email (Gmail - FREE)

1. **Enable 2-factor auth** on your Gmail account

2. **Generate app password**:
   - Go to https://myaccount.google.com/apppasswords
   - Create password for "ConcordBroker"
   - Copy 16-character password

3. **Configure** (add to `.env.mcp`):
   ```bash
   NOTIFICATIONS_EMAIL_ENABLED=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM=ConcordBroker Agents <your-email@gmail.com>
   NOTIFICATION_EMAIL_RECIPIENTS=admin@example.com
   ```

4. **Test**:
   ```bash
   python local-agent-orchestrator/notification_service.py
   ```

5. **Done!** Check your inbox for test email.

---

### Option 3: SMS (Twilio - $2/month)

1. **Sign up for Twilio**:
   - Go to https://www.twilio.com/try-twilio
   - Get $15 free trial credit
   - Get a phone number ($1.15/month)

2. **Get credentials**:
   - Copy Account SID from dashboard
   - Copy Auth Token from dashboard
   - Copy your Twilio phone number

3. **Configure** (add to `.env.mcp`):
   ```bash
   NOTIFICATIONS_SMS_ENABLED=true
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_FROM_NUMBER=+1234567890
   NOTIFICATION_SMS_RECIPIENTS=+1234567890
   ```

4. **Test**:
   ```bash
   python local-agent-orchestrator/notification_service.py
   ```

5. **Done!** Check your phone for test SMS.

---

## 📋 Complete Setup

### Step 1: Copy Environment Template

```bash
# Copy notification settings to your .env.mcp file
cat .env.notifications.example >> .env.mcp
```

Then edit `.env.mcp` with your actual credentials.

### Step 2: Enable Desired Channels

Set to `true` for each channel you want to use:

```bash
NOTIFICATIONS_EMAIL_ENABLED=true
NOTIFICATIONS_SMS_ENABLED=true
NOTIFICATIONS_SLACK_ENABLED=true
```

### Step 3: Configure Each Channel

See "Channel-Specific Setup" section below for detailed instructions.

### Step 4: Test Notifications

```bash
python local-agent-orchestrator/notification_service.py
```

This sends test notifications at MEDIUM, HIGH, and CRITICAL severities.

### Step 5: Restart Agents

Agents automatically use the notification service when they generate alerts:

```bash
# Restart all agents to pick up new configuration
python start_all_agents.py
```

---

## 🔧 Channel-Specific Setup

### 📧 Email (SMTP)

#### Gmail Setup:

1. **Enable 2-Factor Authentication**:
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Create App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "ConcordBroker"
   - Copy the 16-character password

3. **Configure**:
   ```bash
   NOTIFICATIONS_EMAIL_ENABLED=true
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # 16-char app password
   SMTP_FROM=ConcordBroker Agents <your-email@gmail.com>
   NOTIFICATION_EMAIL_RECIPIENTS=admin@example.com,alerts@example.com
   ```

#### Other SMTP Providers:

**Outlook/Office 365**:
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
```

**Yahoo Mail**:
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
```

**SendGrid** (transactional email service):
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
```

**Mailgun**:
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
```

---

### 📱 SMS (Twilio)

#### Twilio Setup:

1. **Create Account**:
   - Go to https://www.twilio.com/try-twilio
   - Sign up (free trial with $15 credit)
   - Verify your email and phone number

2. **Get Phone Number**:
   - In Twilio Console, click "Get a Twilio phone number"
   - Choose a number (costs $1.15/month)
   - Note: Trial accounts can only send to verified numbers

3. **Get Credentials**:
   - Find "Account SID" on dashboard
   - Click "View" next to Auth Token to reveal it
   - Copy both values

4. **Configure**:
   ```bash
   NOTIFICATIONS_SMS_ENABLED=true
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_FROM_NUMBER=+1234567890  # Your Twilio number
   NOTIFICATION_SMS_RECIPIENTS=+1234567890,+0987654321  # E.164 format
   ```

5. **Verify Recipients** (trial accounts only):
   - Go to Console → Phone Numbers → Verified Caller IDs
   - Add each recipient phone number
   - Enter verification code sent via SMS

#### Pricing:
- **Phone number**: $1.15/month
- **SMS (USA)**: $0.0075 per message
- **SMS (International)**: Varies by country
- **Free trial**: $15 credit (enough for ~2,000 SMS)

---

### 💬 Slack (Webhooks)

#### Slack Setup:

1. **Create Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App"
   - Choose "From scratch"
   - Name: "ConcordBroker Agent System"
   - Select your workspace

2. **Enable Incoming Webhooks**:
   - In app settings, click "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to ON
   - Click "Add New Webhook to Workspace"
   - Select channel (create #agent-alerts if needed)
   - Click "Allow"

3. **Copy Webhook URL**:
   - Copy the webhook URL (starts with `https://hooks.slack.com/services/...`)

4. **Configure**:
   ```bash
   NOTIFICATIONS_SLACK_ENABLED=true
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
   SLACK_CHANNEL=#agent-alerts
   ```

5. **Customize** (optional):
   - Change channel name in configuration
   - Create separate channels for different severities
   - Add app icon/emoji in Slack app settings

#### Pricing:
- **Free tier**: 10,000 messages/month (plenty for agent alerts)
- **Paid plans**: Not required for this use case

---

## 🎨 Notification Examples

### Email Notification (HTML):

![Email Example](https://via.placeholder.com/600x300.png?text=Agent+Email+Notification)

**Subject**: `[HIGH] Agent Alert: high_value_opportunity`

**Body** (HTML formatted):
- Header with robot emoji
- Color-coded severity badge (red/orange/yellow/blue)
- Agent name and alert type
- Timestamp
- Full message in white box
- Link to live dashboard
- Professional footer

---

### SMS Notification (Plain Text):

```
CONCORDBROKER [CRITICAL]: Property Data Monitor - Property data is 60 days old. Immediate update required!
```

- **Limited to 160 characters**
- Prefix: `CONCORDBROKER [SEVERITY]`
- Agent name
- Truncated message if too long

---

### Slack Notification (Rich Message):

```
🤖 Agent System

⚠️ Agent Alert - HIGH

Market Analysis Agent - market_weak
Market health score dropped below 40 in BROWARD county

ConcordBroker Autonomous Agent System • 2025-11-01 18:30:45
```

- **Color-coded** left border (red/orange/yellow/blue)
- **Emoji** indicator (🚨/‼️/⚠️/ℹ️)
- Agent name and alert type
- Full message
- Footer with timestamp

---

## 📊 Routing Rules

### Severity Matrix:

| Severity | Email | SMS | Slack | Use Case |
|----------|-------|-----|-------|----------|
| **LOW** | ❌ | ❌ | ❌ | Informational only (logged) |
| **MEDIUM** | ❌ | ❌ | ✅ | Team awareness (non-urgent) |
| **HIGH** | ✅ | ❌ | ✅ | Important alerts (review soon) |
| **CRITICAL** | ✅ | ✅ | ✅ | Urgent issues (immediate action) |

### Routing Logic:

```python
severity_channels = {
    'low': [],                      # No notifications
    'medium': ['slack'],            # Slack only
    'high': ['email', 'slack'],     # Email + Slack
    'critical': ['email', 'sms', 'slack']  # All channels
}
```

### Customizing Routes:

Edit `notification_service.py` to change routing:

```python
# Example: Send email for MEDIUM alerts too
severity_channels = {
    'low': [],
    'medium': ['email', 'slack'],   # Added email
    'high': ['email', 'slack'],
    'critical': ['email', 'sms', 'slack']
}
```

---

## 🤖 Agent Integration

### Automatic Notifications:

Agents automatically send notifications when they generate high-priority alerts:

```python
# Inside any agent (e.g., market_analysis_agent.py)
from notification_service import NotificationService

notification_service = NotificationService()

# Agent detects issue
if market_health < 40:
    # Store alert in database
    self.send_alert('market_weak', 'high',
        f'Market health score dropped below 40 in {county} county')

    # ALSO send notification
    notification_service.notify_agent_alert(
        agent_id=self.agent_id,
        agent_name=self.agent_name,
        alert_type='market_weak',
        severity='high',
        message=f'Market health score dropped below 40 in {county} county'
    )
```

### Manual Notifications:

Send custom notifications from any Python script:

```python
from notification_service import NotificationService

service = NotificationService()

service.notify({
    'agent_name': 'Custom Script',
    'alert_type': 'custom_alert',
    'severity': 'critical',
    'message': 'Something important happened!'
})
```

---

## 🔍 Testing

### Test Script:

The notification service includes a built-in test:

```bash
python local-agent-orchestrator/notification_service.py
```

**What it does**:
1. Initializes notification service
2. Displays configuration status
3. Sends 3 test notifications:
   - MEDIUM severity (Slack only)
   - HIGH severity (Email + Slack)
   - CRITICAL severity (Email + SMS + Slack)
4. Shows success/failure for each channel

**Expected output**:
```
======================================================================
  📢 MULTI-CHANNEL NOTIFICATION SERVICE
======================================================================

  Channels configured:
    📧 Email: ✅ Enabled
       Recipients: 2
    📱 SMS: ✅ Enabled
       Recipients: 1
    💬 Slack: ✅ Enabled
       Channel: #agent-alerts

  Routing rules:
    LOW → (no notifications)
    MEDIUM → Slack
    HIGH → Email + Slack
    CRITICAL → Email + SMS + Slack

======================================================================

======================================================================
  🧪 TESTING NOTIFICATION SERVICE
======================================================================

  Testing MEDIUM alert...
  📢 Routing MEDIUM alert from Market Analysis Agent
  ✅ Slack message sent
  Results:
    slack: ✅ Success

  Testing HIGH alert...
  📢 Routing HIGH alert from Foreclosure Monitor
  ✅ Email sent: [HIGH] Agent Alert: high_value_opportunity
  ✅ Slack message sent
  Results:
    email: ✅ Success
    slack: ✅ Success

  Testing CRITICAL alert...
  📢 Routing CRITICAL alert from Property Data Monitor
  ✅ Email sent: [CRITICAL] Agent Alert: data_stale
  ✅ SMS sent to 1 recipient(s)
  ✅ Slack message sent
  Results:
    email: ✅ Success
    sms: ✅ Success
    slack: ✅ Success

======================================================================
  ✅ Notification service test complete
======================================================================
```

---

## 🐛 Troubleshooting

### Email Issues:

**Error**: `SMTPAuthenticationError: Username and Password not accepted`

**Cause**: Using regular password instead of app password

**Fix**:
1. Enable 2-factor auth on Gmail
2. Generate app-specific password
3. Use 16-character app password, not your Gmail password

---

**Error**: `SMTPException: STARTTLS extension not supported`

**Cause**: Wrong SMTP port or host

**Fix**:
```bash
# Gmail uses port 587 (TLS)
SMTP_PORT=587

# Not port 465 (SSL) or 25 (unencrypted)
```

---

### SMS Issues:

**Error**: `HTTP 403: Forbidden`

**Cause**: Trial account trying to send to unverified number

**Fix**:
1. Go to Twilio Console → Phone Numbers → Verified Caller IDs
2. Add recipient phone number
3. Verify with code sent via SMS
4. Try again

---

**Error**: `HTTP 400: Invalid 'To' phone number`

**Cause**: Phone number not in E.164 format

**Fix**:
```bash
# WRONG
NOTIFICATION_SMS_RECIPIENTS=1234567890

# CORRECT (E.164 format with country code)
NOTIFICATION_SMS_RECIPIENTS=+1234567890
```

---

### Slack Issues:

**Error**: `HTTP 404: Not Found`

**Cause**: Invalid webhook URL

**Fix**:
1. Regenerate webhook in Slack app settings
2. Copy full URL including `/services/...` path
3. URL should start with `https://hooks.slack.com/services/`

---

**Error**: `HTTP 410: Gone`

**Cause**: Webhook was deleted or app uninstalled

**Fix**:
1. Reinstall Slack app to workspace
2. Recreate webhook
3. Update `SLACK_WEBHOOK_URL` in `.env.mcp`

---

### General Issues:

**Issue**: No notifications received

**Check**:
1. Channel is enabled: `NOTIFICATIONS_*_ENABLED=true`
2. Severity triggers that channel (see routing matrix)
3. Test script passes: `python notification_service.py`
4. Agents are running: `python check_agent_activity.py`
5. Check agent logs for notification errors

---

**Issue**: Notifications sent multiple times

**Cause**: Multiple agent instances running

**Fix**:
```bash
# On Windows: Kill all Python processes
taskkill /F /IM python.exe

# Restart agents once
python start_all_agents.py
```

---

## 💰 Cost Breakdown

### Free Options:
- **Email (Gmail)**: $0/month
- **Slack**: $0/month (within free tier)

### Paid Options:
- **SMS (Twilio)**:
  - Phone number: $1.15/month
  - SMS (USA): $0.0075 per message
  - Example: 100 SMS/month = $1.90/month total

### Monthly Cost Estimate:

**Scenario 1: Slack Only** (Recommended for most users)
- Cost: **$0/month**
- Channels: Slack only
- Severities covered: MEDIUM, HIGH, CRITICAL

**Scenario 2: Email + Slack** (Recommended for professional use)
- Cost: **$0/month**
- Channels: Email + Slack
- Severities covered: MEDIUM (Slack), HIGH (Email+Slack), CRITICAL (Email+Slack)

**Scenario 3: All Channels** (Enterprise/critical systems)
- Cost: **~$2-5/month**
- Channels: Email + SMS + Slack
- Severities covered: All
- Breakdown:
  - Email: $0
  - Slack: $0
  - Twilio phone: $1.15
  - SMS (10 critical/month): $0.08
  - **Total: ~$1.23/month**

---

## 🔒 Security Best Practices

### Credentials:
- ✅ Store in `.env.mcp` (already in `.gitignore`)
- ✅ Use app-specific passwords (not main passwords)
- ✅ Rotate API keys every 90 days
- ❌ Never commit credentials to git
- ❌ Never share `.env.mcp` file

### Access Control:
- Limit email recipients to authorized personnel
- Use dedicated Slack channel (not #general)
- Verify SMS recipients before adding
- Review notification logs periodically

### Monitoring:
- Check notification success rates
- Alert on repeated failures
- Review suspicious activity
- Audit credential usage

---

## 📚 Related Documentation

- **Agent System**: `SPECIALIZED_AGENTS_COMPLETE.md`
- **Agent Dashboard**: `AGENT_DASHBOARD_UI_GUIDE.md`
- **Deployment**: `QUICK_DEPLOYMENT_GUIDE.md`
- **Implementation**: `COMPREHENSIVE_IMPLEMENTATION_PLAN.md`

---

## 🎊 Success Checklist

After setup, you should have:

- [ ] At least one channel enabled and tested
- [ ] Test notifications received successfully
- [ ] Credentials stored securely in `.env.mcp`
- [ ] Agents restarted to use notification service
- [ ] Test script passes without errors
- [ ] Appropriate severity levels configured
- [ ] Recipients verified (for SMS trial accounts)
- [ ] Slack webhook posts to correct channel

---

## 💡 Tips & Best Practices

### Channel Selection:
- **Start with Slack** - Easiest setup, free, team collaboration
- **Add Email** - Professional, creates paper trail, free
- **Add SMS last** - Costs money, use only for critical alerts

### Severity Tuning:
- Start conservative (only CRITICAL triggers SMS)
- Adjust based on alert frequency
- Use Slack for everything, Email for important, SMS for critical only

### Testing:
- Run test script after any configuration change
- Test each channel individually
- Verify recipients receive notifications
- Check spam folders for emails

### Monitoring:
- Watch Slack channel for alert patterns
- Review email inbox weekly
- Check Twilio usage dashboard
- Monitor notification success rates in agent logs

---

**🎉 Your Multi-Channel Notification System is ready!**

Agents will now automatically notify you via Email, SMS, and Slack based on alert severity!
