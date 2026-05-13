#!/bin/bash
# IoT Network Security Monitor — Installation & Setup Script
# Run as: bash setup.sh (with or without sudo)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "IoT Network Security Monitor — Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "✓ Checking Python version…"
python3 --version
if ! command -v python3 &> /dev/null || ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo "✗ Python 3.7+ is required"
    exit 1
fi

# Determine if we need sudo for later operations
NEEDS_SUDO=""
if [[ $EUID -ne 0 ]]; then
    echo "ℹ️  You are not running as root. Some operations may require sudo."
    NEEDS_SUDO="sudo"
fi

# Check if in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "✓ Virtual environment detected: $VIRTUAL_ENV"
    PIP_CMD="pip"
else
    echo "⚠️  Not running in a virtual environment."
    echo "   It's recommended to create one: python3 -m venv venv && source venv/bin/activate"
    echo "   For now, installing to system Python (requires sudo)…"
    PIP_CMD="sudo pip"
fi

# Install Python dependencies
echo ""
echo "✓ Installing Python dependencies…"
$PIP_CMD install -r requirements.txt --quiet && echo "  Done!"

# Create data directory
echo ""
echo "✓ Creating data directories…"
mkdir -p data logs

# Initialize database
echo ""
echo "✓ Initializing database…"
python3 -c "from database import Database; db = Database('data/monitor.db'); db.init_schema(); print('  Database ready!')" || {
    echo "  ✗ Failed to initialize database"
    echo "  Make sure all dependencies are installed: $PIP_CMD install -r requirements.txt"
    exit 1
}

# Create systemd service file (only if running with sudo)
if [[ -n "$NEEDS_SUDO" ]]; then
    echo ""
    echo "✓ Creating systemd service…"
    SERVICE_FILE="/etc/systemd/system/iot-monitor.service"
    
    # Determine Python path (in venv or system)
    if [[ -n "$VIRTUAL_ENV" ]]; then
        PYTHON_PATH="$VIRTUAL_ENV/bin/python3"
    else
        PYTHON_PATH="/usr/bin/python3"
    fi
    
    sudo bash -c "cat > '$SERVICE_FILE' << 'SERVICEOF'
[Unit]
Description=IoT Network Security Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON_PATH $SCRIPT_DIR/monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=iot-monitor

[Install]
WantedBy=multi-user.target
SERVICEOF"
    
    echo "  Created: $SERVICE_FILE"
    sudo systemctl daemon-reload
else
    echo ""
    echo "ℹ️  Skipping systemd service setup (run with sudo for this feature)"
fi

# Configure firewall (optional, requires sudo)
if command -v ufw &> /dev/null && [[ -n "$NEEDS_SUDO" ]]; then
    echo ""
    read -p "Do you want to allow web access on port 5000? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo ufw allow 5000/tcp
        echo "  Opened firewall for port 5000"
    fi
fi

# Summary
echo ""
echo "=================================================="
echo "✓ Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Edit configuration:"
echo "   nano config.yaml"
echo ""
echo "2. Test with demo data:"
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "   python3 monitor.py -d"
else
    echo "   sudo python3 monitor.py -d"
fi
echo ""
if [[ -n "$NEEDS_SUDO" ]]; then
    echo "3. Start the service:"
    echo "   sudo systemctl start iot-monitor"
    echo "   sudo systemctl enable iot-monitor  # Enable at boot"
    echo ""
    echo "4. Check status:"
    echo "   sudo systemctl status iot-monitor"
    echo "   sudo journalctl -u iot-monitor -f  # View logs"
else
    echo "3. For systemd service setup (requires sudo):"
    echo "   Run setup again with: sudo bash setup.sh"
fi
echo ""
echo "5. Access web dashboard:"
echo "   http://localhost:5000"
echo ""
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "📝 Recommendation:"
    echo "   Use a virtual environment for cleaner setup:"
    echo "   $ python3 -m venv venv"
    echo "   $ source venv/bin/activate"
    echo "   $ bash setup.sh"
    echo ""
fi
echo "=================================================="
echo ""
