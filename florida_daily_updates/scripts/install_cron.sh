#!/bin/bash
# Florida Daily Updates - Linux/Unix Cron Setup Script
# Sets up cron jobs for automated Florida property data updates

set -e

echo "========================================"
echo "Florida Daily Updates - Cron Setup"
echo "========================================"
echo

# Get script directory and base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$BASE_DIR/scripts/run_daily_update.py"

echo "Script Directory: $SCRIPT_DIR"
echo "Base Directory: $BASE_DIR" 
echo "Python Script: $PYTHON_SCRIPT"
echo

# Check if Python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "ERROR: Python script not found: $PYTHON_SCRIPT"
    exit 1
fi

# Detect Python executable
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python not found in PATH"
    exit 1
fi

echo "Using Python: $PYTHON_CMD"
echo

# Check if user wants to proceed
read -p "Install cron jobs for Florida Daily Updates? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 0
fi

echo "Installing cron jobs..."

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing crontab (excluding Florida updates)
(crontab -l 2>/dev/null || true) | grep -v "Florida Daily Updates" > "$TEMP_CRON"

# Add Florida Daily Updates cron jobs
cat >> "$TEMP_CRON" << EOF

# Florida Daily Updates - Automated Property Data Updates
# Daily full update at 2:00 AM
0 2 * * * cd "$BASE_DIR" && $PYTHON_CMD "$PYTHON_SCRIPT" --mode full >/dev/null 2>&1 # Florida Daily Updates

# Monitor for new files every 6 hours
0 */6 * * * cd "$BASE_DIR" && $PYTHON_CMD "$PYTHON_SCRIPT" --mode monitor >/dev/null 2>&1 # Florida Daily Updates

# Weekly maintenance on Sunday at 3:00 AM  
0 3 * * 0 cd "$BASE_DIR" && $PYTHON_CMD "$PYTHON_SCRIPT" --mode maintenance >/dev/null 2>&1 # Florida Daily Updates

EOF

# Install the new crontab
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo "✓ Cron jobs installed successfully"
echo

echo "Installed schedules:"
echo "  Daily Update:    0 2 * * *   (2:00 AM daily)"
echo "  Monitor Check:   0 */6 * * * (every 6 hours)"
echo "  Maintenance:     0 3 * * 0   (Sunday 3:00 AM)"
echo

echo "========================================"
echo "Cron Management Commands:"
echo "========================================"
echo "  View cron jobs:     crontab -l"
echo "  Edit cron jobs:     crontab -e"
echo "  Remove cron jobs:   crontab -r"
echo "  View cron logs:     grep CRON /var/log/syslog"
echo

echo "Manual execution commands:"
echo "  Full update:        $PYTHON_CMD $PYTHON_SCRIPT --mode full"
echo "  Monitor only:       $PYTHON_CMD $PYTHON_SCRIPT --mode monitor"
echo "  Maintenance:        $PYTHON_CMD $PYTHON_SCRIPT --mode maintenance"
echo "  Test run:           $PYTHON_CMD $PYTHON_SCRIPT --mode test"
echo

echo "Log files location:"
echo "  $BASE_DIR/logs/"
echo

# Test cron job syntax
echo "Testing cron job installation..."
if crontab -l | grep -q "Florida Daily Updates"; then
    echo "✓ Cron jobs successfully installed"
    
    # Show next run times
    echo
    echo "Next scheduled runs:"
    
    # Calculate next 2 AM
    NEXT_2AM=$(date -d "tomorrow 02:00" "+%Y-%m-%d %H:%M:%S")
    echo "  Daily Update: $NEXT_2AM"
    
    # Calculate next 6-hour interval
    CURRENT_HOUR=$(date +%H)
    NEXT_6H_OFFSET=$(( (6 - CURRENT_HOUR % 6) % 6 ))
    if [ $NEXT_6H_OFFSET -eq 0 ]; then
        NEXT_6H_OFFSET=6
    fi
    NEXT_6H=$(date -d "+${NEXT_6H_OFFSET} hours" "+%Y-%m-%d %H:00:00")
    echo "  Monitor Check: $NEXT_6H"
    
    # Calculate next Sunday 3 AM
    CURRENT_DOW=$(date +%u)  # 1=Monday, 7=Sunday
    DAYS_TO_SUNDAY=$(( (7 - CURRENT_DOW) % 7 ))
    if [ $DAYS_TO_SUNDAY -eq 0 ]; then
        DAYS_TO_SUNDAY=7
    fi
    NEXT_SUNDAY=$(date -d "+${DAYS_TO_SUNDAY} days 03:00" "+%Y-%m-%d %H:%M:%S")
    echo "  Maintenance: $NEXT_SUNDAY"
    
else
    echo "✗ ERROR: Cron jobs not found after installation"
    exit 1
fi

echo
echo "Setup completed successfully!"
echo
echo "To verify the system is working:"
echo "1. Check logs in $BASE_DIR/logs/"
echo "2. Run a test: $PYTHON_CMD $PYTHON_SCRIPT --mode test"
echo "3. Monitor cron execution: tail -f /var/log/syslog | grep CRON"
echo

# Optional: Create systemd service for more advanced users
read -p "Would you also like to create a systemd service? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    create_systemd_service
fi

echo "Done!"

create_systemd_service() {
    echo
    echo "Creating systemd service..."
    
    # Create service file content
    SERVICE_FILE="/etc/systemd/system/florida-daily-updates.service"
    TIMER_FILE="/etc/systemd/system/florida-daily-updates.timer"
    
    # Check if we can write to systemd directory
    if [ ! -w /etc/systemd/system/ ] && [ "$EUID" -ne 0 ]; then
        echo "Note: Creating service files in current directory (need sudo for system installation)"
        SERVICE_FILE="./florida-daily-updates.service"
        TIMER_FILE="./florida-daily-updates.timer"
    fi
    
    # Create service file
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Florida Daily Property Data Updates
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$BASE_DIR
ExecStart=$PYTHON_CMD $PYTHON_SCRIPT --mode full
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Create timer file
    cat > "$TIMER_FILE" << EOF
[Unit]
Description=Run Florida Daily Updates daily at 2 AM
Requires=florida-daily-updates.service

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    echo "✓ Service files created:"
    echo "  Service: $SERVICE_FILE"
    echo "  Timer:   $TIMER_FILE"
    echo
    
    if [ "$SERVICE_FILE" != "/etc/systemd/system/florida-daily-updates.service" ]; then
        echo "To install the systemd service, run as root:"
        echo "  sudo cp florida-daily-updates.service /etc/systemd/system/"
        echo "  sudo cp florida-daily-updates.timer /etc/systemd/system/"
        echo "  sudo systemctl daemon-reload"
        echo "  sudo systemctl enable florida-daily-updates.timer"
        echo "  sudo systemctl start florida-daily-updates.timer"
    else
        # Try to install and enable
        systemctl daemon-reload
        systemctl enable florida-daily-updates.timer
        systemctl start florida-daily-updates.timer
        echo "✓ Systemd service enabled and started"
    fi
}