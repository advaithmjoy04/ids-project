#!/bin/bash
# Installation script for IDS Dashboard on Kali Linux

set -e

echo "========================================"
echo "  IDS Dashboard - Kali Linux Installer"
echo "========================================"
echo ""

# Check if running on Kali
if ! grep -q "Kali" /etc/os-release 2>/dev/null; then
    echo "⚠️  Warning: This script is optimized for Kali Linux"
    echo "   Proceeding anyway..."
    echo ""
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "   Install with: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    echo "   Install with: sudo apt install python3-pip"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/ids_project"

cd "$PROJECT_DIR" || exit

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo "Installing Python packages..."
if [ -f "data/requirements.txt" ]; then
    pip install -r data/requirements.txt
else
    echo "❌ requirements.txt not found"
    exit 1
fi

echo ""
echo "✓ All packages installed successfully"
echo ""

# Check if model files exist
MODEL_DIR="data"
if [ ! -f "$MODEL_DIR/ids_model.pkl" ]; then
    echo "⚠️  Warning: Model files not found"
    echo "   You need to train the model first:"
    echo "   python models/train_model.py"
    echo ""
else
    echo "✓ Model files found"
fi

# Make scripts executable
chmod +x dashboard/start_server.sh
chmod +x dashboard/start_server.py

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env configuration file..."
    cat > .env << EOF
# IDS Dashboard Server Configuration
IDS_HOST=0.0.0.0
IDS_PORT=5000
IDS_DEBUG=False
IDS_WORKERS=4
IDS_SERVER_TYPE=gunicorn

# IDS Engine Configuration
IDS_MAX_HISTORY=1000
IDS_ALERT_THRESHOLD=0.7
IDS_STATS_CACHE_TTL=5

# Twilio Configuration (Optional)
# TWILIO_ACCOUNT_SID=your_account_sid_here
# TWILIO_AUTH_TOKEN=your_auth_token_here
# TWILIO_PHONE_NUMBER=your_twilio_phone_number
# ADMIN_PHONE_NUMBER=your_admin_phone_number
EOF
    echo "✓ .env file created"
    echo "   Edit .env to customize configuration"
fi

echo ""
echo "========================================"
echo "  Installation Complete!"
echo "========================================"
echo ""
echo "To start the server:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  ./dashboard/start_server.sh"
echo ""
echo "Or use the systemd service (see README_SERVER.md)"
echo ""

