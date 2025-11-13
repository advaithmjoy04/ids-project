#!/bin/bash
# Script to find which interface is connected to ids-network

echo "================================================"
echo "  Finding IDS Network Interface"
echo "================================================"
echo ""

# List all interfaces
echo "All network interfaces:"
ip link show | grep -E "^[0-9]+:" | while read line; do
    iface=$(echo $line | awk '{print $2}' | sed 's/://')
    state=$(ip link show $iface | grep -oP 'state \K\w+')
    echo "  - $iface (state: $state)"
done

echo ""
echo "Interface IP addresses:"
ip addr show | grep -E "^[0-9]+:|inet " | while read line; do
    if [[ $line =~ ^[0-9]+: ]]; then
        iface=$(echo $line | awk '{print $2}' | sed 's/://')
        echo ""
        echo "  $iface:"
    elif [[ $line =~ inet ]]; then
        ip=$(echo $line | awk '{print $2}' | cut -d'/' -f1)
        echo "    IP: $ip"
    fi
done

echo ""
echo "================================================"
echo "  Recommendation:"
echo "================================================"
echo ""
echo "The ids-network interface is usually:"
echo "  - eth0 or eth1 (if using standard naming)"
echo "  - ens33 or ens34 (if using predictable naming)"
echo ""
echo "Look for an interface with:"
echo "  - An IP address (usually 192.168.x.x or 10.x.x.x)"
echo "  - State: UP"
echo ""
echo "To test which interface has traffic:"
echo "  sudo tcpdump -i eth0 -c 5"
echo "  sudo tcpdump -i eth1 -c 5"
echo ""
echo "Then use the correct interface:"
echo "  sudo python3 network_monitor/monitor.py <interface>"
echo ""

