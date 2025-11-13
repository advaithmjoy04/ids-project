#!/bin/bash
# Setup script for Victim VMs in IDS Lab

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "================================================"
echo "  IDS Lab - Victim VM Setup"
echo "================================================"
echo -e "${NC}"

# Update system
echo -e "${YELLOW}Updating package lists...${NC}"
sudo apt update

# Install services
echo -e "${YELLOW}Installing services...${NC}"
sudo apt install -y \
    apache2 \
    openssh-server \
    net-tools

# Start and enable services
echo -e "${YELLOW}Starting services...${NC}"
sudo systemctl start apache2
sudo systemctl start ssh
sudo systemctl enable apache2
sudo systemctl enable ssh

# Create a simple web page
echo -e "${YELLOW}Creating test web page...${NC}"
echo "<html><body><h1>IDS Test Victim Server</h1><p>This is a test server for IDS testing.</p><p>VM: $(hostname)</p></body></html>" | sudo tee /var/www/html/index.html > /dev/null

# Show status
echo ""
echo -e "${GREEN}✓ Victim VM setup complete!${NC}"
echo ""
echo "Services running:"
echo "  - Apache Web Server on port 80"
echo "  - SSH Server on port 22"
echo ""

# Show IP
IP=$(hostname -I | awk '{print $1}')
echo -e "${YELLOW}This VM's IP: $IP${NC}"
echo ""
echo "From the attacker VM, target this IP:"
echo "  ping $IP"
echo "  nmap $IP"
echo "  curl http://$IP"
echo ""

# Show network info
echo "Network interfaces:"
ip link show | grep -E "^[0-9]+:" | awk '{print "  - " $2}'
echo ""

# Show open ports
echo "Open ports:"
sudo netstat -tlnp | grep -E ":(80|22) " || echo "  (Checking...)"

