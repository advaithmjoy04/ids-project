#!/bin/bash
# Script to generate test network traffic for IDS monitoring

echo "========================================"
echo "  Generating Test Network Traffic"
echo "========================================"
echo ""

echo "This script will generate various types of network traffic"
echo "to test the IDS monitor. Run this in a separate terminal"
echo "while the monitor is running."
echo ""
echo "Press Ctrl+C to stop generating traffic"
echo ""

# Function to generate traffic
generate_traffic() {
    echo "📡 Generating traffic..."
    
    # Ping tests
    echo "  → Pinging Google DNS..."
    ping -c 10 8.8.8.8 > /dev/null 2>&1
    
    echo "  → Pinging Cloudflare DNS..."
    ping -c 10 1.1.1.1 > /dev/null 2>&1
    
    # HTTP requests
    echo "  → Making HTTP requests..."
    curl -s http://www.google.com > /dev/null 2>&1
    curl -s http://www.example.com > /dev/null 2>&1
    curl -s http://www.github.com > /dev/null 2>&1
    
    # DNS queries
    echo "  → Making DNS queries..."
    nslookup google.com > /dev/null 2>&1
    nslookup github.com > /dev/null 2>&1
    
    echo "  ✓ Traffic generated!"
    echo ""
}

# Generate traffic in a loop
while true; do
    generate_traffic
    sleep 5
done

