# Troubleshooting: Network Monitor Not Capturing Data

## Common Issues and Solutions

### Issue 1: Using Loopback Interface (lo)
**Problem:** Loopback interface (`lo`) only captures localhost traffic, which is usually minimal.

**Solution:** Use a real network interface:
```bash
# List available interfaces
ip link show
# or
ifconfig

# Use a real interface (e.g., eth0, wlan0, ens33)
python3 network_monitor/monitor.py eth0
# or
python3 network_monitor/monitor.py wlan0
```

### Issue 2: IDS API Not Running
**Problem:** Monitor can't send data if the dashboard server isn't running.

**Solution:** Start the dashboard server first:
```bash
# Terminal 1: Start dashboard
cd ~/ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh

# Terminal 2: Start monitor
cd ~/ids-project/ids_project
source venv/bin/activate
sudo python3 network_monitor/monitor.py eth0
```

### Issue 3: Need 5 Packets Per Connection
**Problem:** Monitor waits for 5 packets from the same connection before analyzing.

**Solution:** Generate network traffic:
```bash
# Generate some traffic to test
ping -c 10 google.com
curl http://google.com
# Or browse the web
```

### Issue 4: Permission Issues
**Problem:** Packet capture requires root/sudo privileges.

**Solution:** Run with sudo:
```bash
sudo python3 network_monitor/monitor.py eth0
```

### Issue 5: No Traffic on Interface
**Problem:** Interface might be down or have no traffic.

**Solution:** Check interface status:
```bash
# Check if interface is up
ip link show eth0

# Bring interface up if needed
sudo ip link set eth0 up

# Check for traffic
sudo tcpdump -i eth0 -c 10
```

## Quick Diagnostic Steps

### Step 1: Verify API is Running
```bash
curl http://localhost:5000/stats
```
Should return JSON data. If not, start the server.

### Step 2: Check Interface
```bash
# List interfaces
ip link show

# Check if interface has traffic
sudo tcpdump -i eth0 -c 5
```

### Step 3: Test Monitor with Verbose Output
The updated monitor now shows:
- ✓ When packets are analyzed
- ❌ Connection errors
- ⚠️ Warnings

### Step 4: Generate Test Traffic
```bash
# In another terminal, generate traffic
ping -c 20 8.8.8.8
curl http://www.google.com
wget http://www.example.com
```

## Expected Output

When working correctly, you should see:
```
✓ Analyzed: 192.168.1.100 -> 8.8.8.8 (Confidence: 15.2%)
✓ Analyzed: 192.168.1.100 -> 192.168.1.1 (Confidence: 8.5%)
```

If threats are detected:
```
⚠️  THREAT DETECTED!
   Source: 192.168.1.100
   Destination: 192.168.1.1
   Confidence: 85.3%
   Time: 2025-01-XX...
```

## Complete Setup Example

```bash
# Terminal 1: Start Dashboard
cd ~/ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh

# Terminal 2: Start Monitor (with real interface)
cd ~/ids-project/ids_project
source venv/bin/activate
sudo python3 network_monitor/monitor.py eth0

# Terminal 3: Generate Traffic
ping -c 50 google.com
# Or browse websites
```

## Finding Your Network Interface

```bash
# Method 1: ip command
ip link show

# Method 2: ifconfig
ifconfig

# Method 3: List all interfaces
ls /sys/class/net/

# Common interface names:
# - eth0, eth1 (Ethernet)
# - wlan0, wlan1 (Wireless)
# - ens33, ens34 (VMware/VirtualBox)
# - lo (Loopback - avoid for monitoring)
```

## Still Not Working?

1. **Check monitor output** - Look for error messages
2. **Verify API connection** - `curl http://localhost:5000/stats`
3. **Check firewall** - `sudo ufw status`
4. **Verify interface** - `sudo tcpdump -i eth0 -c 5`
5. **Check logs** - Look at dashboard server logs

