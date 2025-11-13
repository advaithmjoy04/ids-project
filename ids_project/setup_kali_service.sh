#!/bin/bash
# Setup systemd service for IDS Dashboard on Kali Linux

set -e

echo "========================================"
echo "  IDS Dashboard - Systemd Service Setup"
echo "========================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/ids_project"

# Get current user (who ran sudo)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(eval echo ~$REAL_USER)

echo "Project directory: $PROJECT_DIR"
echo "User: $REAL_USER"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "❌ Virtual environment not found"
    echo "   Run install_kali.sh first"
    exit 1
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/ids-dashboard.service"

echo "Creating systemd service file..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=IDS Dashboard Server
After=network.target

[Service]
Type=simple
User=$REAL_USER
Group=$REAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/dashboard/start_server.py --server gunicorn --port 5000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created: $SERVICE_FILE"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Systemd daemon reloaded"
echo ""

# Enable service
echo "Enabling service..."
systemctl enable ids-dashboard.service
echo "✓ Service enabled (will start on boot)"
echo ""

echo "========================================"
echo "  Service Setup Complete!"
echo "========================================"
echo ""
echo "To start the service:"
echo "  sudo systemctl start ids-dashboard"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop ids-dashboard"
echo ""
echo "To check status:"
echo "  sudo systemctl status ids-dashboard"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u ids-dashboard -f"
echo ""
echo "To disable service:"
echo "  sudo systemctl disable ids-dashboard"
echo ""

