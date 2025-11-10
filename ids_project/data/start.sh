#!/bin/bash

# Victim VM Setup Script
# Run this on VICTIM VMs (Kali VM 2 & 3)

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "================================================"
echo "  IDS Testing - Victim VM Setup"
echo "================================================"
echo -e "${NC}"

# Update system
echo -e "${YELLOW}Installing services...${NC}"

# Apache web server
if ! command -v apache2 &> /dev/null; then
    echo "Installing Apache..."
    sudo apt update
    sudo apt install -y apache2
fi

# FTP server
if ! command -v vsftpd &> /dev/null; then
    echo "Installing FTP server..."
    sudo apt install -y vsftpd
fi

# SSH (usually pre-installed on Kali)
if ! systemctl is-active --quiet ssh; then
    echo "Starting SSH service..."
    sudo systemctl start ssh
    sudo systemctl enable ssh
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"

sudo systemctl start apache2
sudo systemctl enable apache2

sudo systemctl start vsftpd
sudo systemctl enable vsftpd

# Create a simple web page
echo "<html><body><h1>IDS Test Victim Server</h1><p>This is a test server for IDS testing.</p></body></html>" | sudo tee /var/www/html/index.html > /dev/null

# Show status
echo ""
echo -e "${GREEN}✓ Victim VM setup complete!${NC}"
echo ""
echo "Services running:"
echo "- Apache Web Server on port 80"
echo "- FTP Server on port 21"
echo "- SSH Server on port 22"
echo ""

# Show IP
IP=$(hostname -I | awk '{print $1}')
echo -e "${YELLOW}This VM's IP: $IP${NC}"
echo ""
echo "From the attacker VM, target this IP:"
echo "  ./attacker.sh $IP"
echo ""

# Open ports info
echo "Open ports:"
sudo netstat -tlnp | grep -E ":(80|21|22) "