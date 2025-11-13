# IDS Lab - VirtualBox VM Setup Guide

## Network Configuration Overview

This guide sets up a complete IDS lab environment with:
- **Monitor VM** (Kali Linux) - Runs IDS dashboard and monitor
- **Attacker VM** (Kali Linux) - Simulates attacks
- **Victim1 & Victim2 VMs** (Kali Linux) - Target systems

## Network Setup

### Step 1: Create Internal Network in VirtualBox

1. Open VirtualBox
2. Go to **File → Host Network Manager**
3. Create a new network:
   - Name: `ids-network`
   - Type: Internal Network
   - Click **Create**

### Step 2: Configure Monitor VM (Kali)

**Adapter 1 (IDS Network):**
- ✅ Enable Network Adapter
- Attached to: **Internal Network**
- Name: **ids-network**
- Promiscuous Mode: **Allow All** (IMPORTANT for packet capture!)

**Adapter 2 (Internet via NAT):**
- ✅ Enable Network Adapter
- Attached to: **NAT**
- (For internet access to download packages)

**Why 2 Adapters?**
- Adapter 1: Captures traffic from the internal network
- Adapter 2: Provides internet access (WiFi/Cable/USB Tethering compatible)

### Step 3: Configure Attacker VM

**Adapter 1 ONLY:**
- ✅ Enable Network Adapter
- Attached to: **Internal Network**
- Name: **ids-network**
- Promiscuous Mode: **Deny**
- (No internet needed for attacker)

### Step 4: Configure Victim1 & Victim2 VMs

**Adapter 1 ONLY:**
- ✅ Enable Network Adapter
- Attached to: **Internal Network**
- Name: **ids-network**
- Promiscuous Mode: **Deny**
- (No internet needed for victims)

## VM Setup Commands

### Monitor VM Setup

```bash
# Update system
sudo apt update

# Install required packages
sudo apt install -y python3 python3-pip python3-venv git

# Clone/download IDS project
cd ~
git clone https://github.com/advaithmjoy04/ids-project.git
# OR copy project files to ~/ids-project

# Run installation
cd ids-project
chmod +x install_kali.sh
./install_kali.sh

# Train model (first time only)
cd ids_project
source venv/bin/activate
python models/train_model.py
```

### Victim1 & Victim2 VMs Setup

```bash
# Update packages
sudo apt update

# Install services
sudo apt install -y \
    apache2 \
    openssh-server \
    net-tools

# Start and enable services
sudo systemctl start apache2
sudo systemctl start ssh
sudo systemctl enable apache2
sudo systemctl enable ssh

# Check IP address
hostname -I
# Note this IP - you'll need it for attacks
```

### Attacker VM Setup

```bash
# Update packages
sudo apt update

# Install attack tools (optional)
sudo apt install -y \
    nmap \
    hping3 \
    metasploit-framework
```

## Finding Network Interfaces

On the **Monitor VM**, after starting, find which interface is connected to `ids-network`:

```bash
# List all interfaces
ip link show

# Check IP addresses
ip addr show

# The interface with IP in 192.168.x.x or 10.x.x.x range is likely ids-network
# Common names: eth0, eth1, ens33, ens34
```

## Starting the IDS System

### On Monitor VM:

**Terminal 1 - Start Dashboard:**
```bash
cd ~/ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh
```

**Terminal 2 - Start Monitor:**
```bash
cd ~/ids-project/ids_project
source venv/bin/activate

# Find the ids-network interface first
ip link show

# Start monitor on the correct interface (usually eth0 or eth1)
sudo python3 network_monitor/monitor.py eth0
# OR if ids-network is on eth1:
sudo python3 network_monitor/monitor.py eth1
```

**Terminal 3 - Access Dashboard:**
```bash
# Open browser
firefox http://localhost:5000
# Login: admin / admin
```

## Testing the Setup

### From Attacker VM:

```bash
# Ping victim
ping -c 10 <victim-ip>

# Port scan
nmap -sS <victim-ip>

# HTTP request
curl http://<victim-ip>

# SSH connection attempt
ssh user@<victim-ip>
```

All this traffic will be captured by the Monitor VM and analyzed by the IDS!

## Troubleshooting

### Monitor not capturing traffic?

1. **Check interface:**
   ```bash
   # On Monitor VM
   ip link show
   ip addr show
   ```

2. **Verify promiscuous mode:**
   - VirtualBox → Monitor VM Settings → Network → Adapter 1
   - Promiscuous Mode must be **Allow All**

3. **Check interface is up:**
   ```bash
   sudo ip link set eth0 up
   ```

4. **Test packet capture:**
   ```bash
   sudo tcpdump -i eth0 -c 10
   ```

### Can't access dashboard?

1. **Check firewall:**
   ```bash
   sudo ufw allow 5000/tcp
   ```

2. **Verify server is running:**
   ```bash
   ps aux | grep start_server
   ```

3. **Check logs:**
   ```bash
   # If running as service
   sudo journalctl -u ids-dashboard -f
   ```

## Network Diagram

```
┌─────────────────┐
│  Attacker VM    │
│  (Kali Linux)   │
│  eth0: ids-net  │
└────────┬────────┘
         │
         │ Internal Network
         │ "ids-network"
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Victim1│ │Victim2│
│  VM   │ │  VM   │
│eth0:  │ │eth0:  │
│ids-net│ │ids-net│
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
    ┌────▼──────────────┐
    │   Monitor VM      │
    │   (Kali Linux)    │
    │   eth0: ids-net   │ ← Captures all traffic
    │   eth1: NAT       │ ← Internet access
    │   (Promiscuous)    │
    └───────────────────┘
```

## Quick Reference

| VM | Adapters | Purpose |
|---|---|---|
| Monitor | eth0: ids-network (Promiscuous) | Capture traffic |
| Monitor | eth1: NAT | Internet access |
| Attacker | eth0: ids-network | Launch attacks |
| Victim1 | eth0: ids-network | Target system |
| Victim2 | eth0: ids-network | Target system |

## Next Steps

1. ✅ Configure all VMs as described
2. ✅ Start Monitor VM dashboard and monitor
3. ✅ Generate traffic from Attacker to Victims
4. ✅ Watch IDS detect threats in real-time!

