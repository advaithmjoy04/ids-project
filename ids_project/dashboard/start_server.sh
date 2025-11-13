#!/bin/bash
# Kali Linux startup script for IDS Dashboard Server

echo "========================================"
echo "  IDS Dashboard Server Startup"
echo "  Kali Linux Optimized"
echo "========================================"
echo ""

# Check if running as root (not recommended for production)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Warning: Running as root is not recommended"
    echo "   Consider running as a regular user"
    echo ""
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
elif [ -d "../venv" ]; then
    echo "✓ Activating virtual environment (parent directory)..."
    source ../venv/bin/activate
else
    echo "❌ No virtual environment found!"
    echo "   Please run: ./install_kali.sh"
    echo "   Or create venv manually: python3 -m venv venv && source venv/bin/activate && pip install -r data/requirements.txt"
    exit 1
fi

# Verify Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not found in virtual environment. Installing requirements..."
    pip install -r data/requirements.txt
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Set default environment variables for Kali
export IDS_HOST=${IDS_HOST:-0.0.0.0}
export IDS_PORT=${IDS_PORT:-5000}
export IDS_SERVER_TYPE=${IDS_SERVER_TYPE:-gunicorn}  # Gunicorn for Linux
export IDS_WORKERS=${IDS_WORKERS:-4}

# Check if required packages are installed
if ! python3 -c "import gunicorn" 2>/dev/null; then
    echo "⚠️  Gunicorn not found. Installing..."
    pip3 install gunicorn eventlet
fi

if ! python3 -c "import eventlet" 2>/dev/null; then
    echo "⚠️  Eventlet not found. Installing..."
    pip3 install eventlet
fi

echo "Starting server..."
echo "  Host: $IDS_HOST"
echo "  Port: $IDS_PORT"
echo "  Server Type: $IDS_SERVER_TYPE"
echo "  Workers: $IDS_WORKERS"
echo ""
echo "Dashboard will be available at:"
echo "  http://localhost:$IDS_PORT"
echo "  http://$(hostname -I | awk '{print $1}'):$IDS_PORT"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start the server
cd "$(dirname "$0")/.." || exit
python3 dashboard/start_server.py \
    --host "$IDS_HOST" \
    --port "$IDS_PORT" \
    --server "$IDS_SERVER_TYPE" \
    --workers "$IDS_WORKERS"

