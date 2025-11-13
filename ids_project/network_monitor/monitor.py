"""
Network Traffic Monitor - Captures live network traffic
Processes packets and sends to IDS for analysis
"""

from scapy.all import sniff, IP, TCP, UDP, ICMP
from collections import defaultdict, deque
import time
from datetime import datetime
import threading
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Constants
PACKETS_PER_CONNECTION = 3  # Reduced from 5 to capture traffic faster
API_TIMEOUT = 5  # Increased timeout
API_URL = "http://localhost:5000/analyze"
CONNECTION_CLEANUP_INTERVAL = 300  # 5 minutes
MAX_CONNECTION_AGE = 600  # 10 minutes

# Debug mode - set to True to see all packet captures
DEBUG_MODE = False

class NetworkMonitor:
    def __init__(self, interface="eth0", queue_size=100):
        self.interface = interface
        # Verify interface exists
        self._verify_interface()
        self.queue_size = queue_size
        self.connection_states = defaultdict(lambda: {
            'packets': deque(maxlen=PACKETS_PER_CONNECTION * 2),  # Allow some overflow
            'start_time': time.time(),
            'last_update': time.time()
        })
        self.api_url = API_URL
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="IDS-API")
        self._lock = threading.Lock()
        self._running = True
        
        # Start cleanup thread
        cleanup_thread = threading.Thread(target=self._cleanup_old_connections, daemon=True)
        cleanup_thread.start()
    
    def _verify_interface(self):
        """Verify that the network interface exists and is up"""
        try:
            import subprocess
            # Check if interface exists
            result = subprocess.run(
                ['ip', 'link', 'show', self.interface],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                print(f"⚠️  Warning: Interface '{self.interface}' not found!")
                print(f"   Available interfaces:")
                # List available interfaces
                list_result = subprocess.run(
                    ['ip', 'link', 'show'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if list_result.returncode == 0:
                    # Extract interface names
                    interfaces = [line.split(':')[1].strip().split('@')[0] 
                                 for line in list_result.stdout.split('\n') 
                                 if ':' in line and 'state' not in line.lower()]
                    for iface in interfaces:
                        if iface:
                            print(f"     - {iface}")
                print(f"\n   Trying to use '{self.interface}' anyway...\n")
        except Exception as e:
            # If ip command fails, try ifconfig or just continue
            pass
        
    def extract_packet_features(self, packet):
        """Extract features from a single packet - optimized"""
        try:
            if not packet.haslayer(IP):
                return None
            
            ip_layer = packet[IP]
            timestamp = datetime.now().isoformat()
            timestamp_raw = time.time()
            
            # Base features
            features = {
                'timestamp': timestamp,
                'timestamp_raw': timestamp_raw,
                'src_ip': ip_layer.src,
                'dst_ip': ip_layer.dst,
                'protocol': ip_layer.proto,
                'packet_size': len(packet),
                'ttl': ip_layer.ttl,
            }
            
            # Protocol-specific features - use if/elif chain for efficiency
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                features.update({
                    'src_port': tcp_layer.sport,
                    'dst_port': tcp_layer.dport,
                    'tcp_flags': getattr(tcp_layer.flags, 'value', 0),
                    'window_size': tcp_layer.window,
                    'protocol_type': 'tcp'
                })
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                features.update({
                    'src_port': udp_layer.sport,
                    'dst_port': udp_layer.dport,
                    'protocol_type': 'udp'
                })
            elif packet.haslayer(ICMP):
                features.update({
                    'protocol_type': 'icmp',
                    'src_port': 0,
                    'dst_port': 0
                })
            else:
                features.update({
                    'protocol_type': 'other',
                    'src_port': 0,
                    'dst_port': 0
                })
            
            return features
            
        except Exception as e:
            # Silently skip malformed packets to avoid spam
            return None
    
    def compute_connection_features(self, packets):
        """Compute aggregated connection features from packet list - optimized"""
        if not packets:
            return None
        
        try:
            # Convert deque to list for indexing
            packet_list = list(packets)
            first_packet = packet_list[0]
            last_packet = packet_list[-1]
            
            # Basic stats - more efficient calculation
            duration = last_packet.get('timestamp_raw', 0) - first_packet.get('timestamp_raw', 0)
            src_ip = first_packet.get('src_ip')
            dst_ip = first_packet.get('dst_ip')
            
            # Calculate bytes more efficiently
            src_bytes = sum(p.get('packet_size', 0) for p in packet_list if p.get('src_ip') == src_ip)
            dst_bytes = sum(p.get('packet_size', 0) for p in packet_list if p.get('dst_ip') == dst_ip)
            
            # Service and protocol
            protocol_type = first_packet.get('protocol_type', 'tcp')
            dst_port = first_packet.get('dst_port', 0)
            
            # Map port to service
            service = self.map_port_to_service(dst_port)
            
            # Connection flags
            flag = 'SF'  # Default to normal connection
            
            features = {
                'duration': duration,
                'protocol_type': protocol_type,
                'service': service,
                'flag': flag,
                'src_bytes': src_bytes,
                'dst_bytes': dst_bytes,
                'land': 1 if packets[0].get('src_ip') == packets[0].get('dst_ip') else 0,
                'wrong_fragment': 0,
                'urgent': 0,
                'hot': 0,
                'num_failed_logins': 0,
                'logged_in': 0,
                'num_compromised': 0,
                'root_shell': 0,
                'su_attempted': 0,
                'num_root': 0,
                'num_file_creations': 0,
                'num_shells': 0,
                'num_access_files': 0,
                'num_outbound_cmds': 0,
                'is_host_login': 0,
                'is_guest_login': 0,
                'count': len(packets),
                'srv_count': len(packets),
                'serror_rate': 0.0,
                'srv_serror_rate': 0.0,
                'rerror_rate': 0.0,
                'srv_rerror_rate': 0.0,
                'same_srv_rate': 1.0,
                'diff_srv_rate': 0.0,
                'srv_diff_host_rate': 0.0,
                'dst_host_count': 1,
                'dst_host_srv_count': 1,
                'dst_host_same_srv_rate': 1.0,
                'dst_host_diff_srv_rate': 0.0,
                'dst_host_same_src_port_rate': 1.0,
                'dst_host_srv_diff_host_rate': 0.0,
                'dst_host_serror_rate': 0.0,
                'dst_host_srv_serror_rate': 0.0,
                'dst_host_rerror_rate': 0.0,
                'dst_host_srv_rerror_rate': 0.0,
            }
            
            # Add metadata
            features['src_ip'] = src_ip
            features['dst_ip'] = dst_ip
            features['timestamp'] = first_packet.get('timestamp')
            
            return features
            
        except Exception as e:
            # Log error but don't spam console
            return None
    
    # Class-level constant for port mapping
    PORT_SERVICE_MAP = {
        20: 'ftp_data', 21: 'ftp', 22: 'ssh', 23: 'telnet',
        25: 'smtp', 53: 'domain_u', 80: 'http', 110: 'pop_3',
        143: 'imap4', 443: 'https', 3306: 'mysql', 5432: 'postgres',
        6379: 'redis', 8080: 'http_8080', 8443: 'https_alt'
    }
    
    @classmethod
    def map_port_to_service(cls, port):
        """Map port number to service name - optimized with class constant"""
        return cls.PORT_SERVICE_MAP.get(port, 'other')
    
    def packet_handler(self, packet):
        """Handle each captured packet - optimized"""
        features = self.extract_packet_features(packet)
        
        if not features:
            return
        
        # Create connection key efficiently
        src_port = features.get('src_port', 0)
        dst_port = features.get('dst_port', 0)
        conn_key = f"{features['src_ip']}:{src_port}-{features['dst_ip']}:{dst_port}"
        
        packets_to_analyze = None
        
        # Thread-safe access to connection states
        with self._lock:
            conn_state = self.connection_states[conn_key]
            conn_state['packets'].append(features)
            conn_state['last_update'] = time.time()
            packet_count = len(conn_state['packets'])
            
            # Debug output
            if DEBUG_MODE:
                print(f"📦 Packet captured: {features['src_ip']}:{src_port} -> {features['dst_ip']}:{dst_port} ({packet_count}/{PACKETS_PER_CONNECTION})")
            
            # Check if we have enough packets for analysis
            if packet_count >= PACKETS_PER_CONNECTION:
                packets_to_analyze = list(conn_state['packets'])
                # Clear packets after copying
                conn_state['packets'].clear()
                if DEBUG_MODE:
                    print(f"✅ Ready to analyze: {conn_key} ({len(packets_to_analyze)} packets)")
        
        # Process outside lock to avoid blocking packet capture
        if packets_to_analyze:
            conn_features = self.compute_connection_features(packets_to_analyze)
            
            if conn_features:
                # Send to IDS asynchronously
                self.executor.submit(self.send_to_ids, conn_features)
    
    def send_to_ids(self, features):
        """Send features to IDS API for analysis - async"""
        try:
            response = requests.post(
                self.api_url,
                json=features,
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                # Check if response is JSON
                try:
                    result = response.json()
                    # Always print when data is sent successfully (for debugging)
                    print(f"✓ Analyzed: {features['src_ip']} -> {features['dst_ip']} (Confidence: {result.get('confidence', 0):.1%})")
                    
                    if result.get('threat_detected'):
                        confidence = result.get('confidence', 0)
                        print(f"\n⚠️  THREAT DETECTED!")
                        print(f"   Source: {features['src_ip']}")
                        print(f"   Destination: {features['dst_ip']}")
                        print(f"   Confidence: {confidence:.2%}")
                        print(f"   Time: {features['timestamp']}\n")
                except ValueError as json_error:
                    # Response is not JSON - might be HTML (login page) or error
                    print(f"❌ API returned non-JSON response (status {response.status_code})")
                    print(f"   Response preview: {response.text[:200]}")
                    print(f"   This might mean the /analyze endpoint requires authentication")
            else:
                print(f"⚠️  API returned status {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                    
        except requests.exceptions.Timeout:
            print("⚠️  API timeout - server might be overloaded")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to IDS API. Is the server running on http://localhost:5000?")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Request error: {e}")
        except ValueError as json_error:
            print(f"❌ JSON parsing error: {json_error}")
            print(f"   The API might be returning HTML instead of JSON")
        except Exception as e:
            print(f"❌ Unexpected error sending to IDS: {e}")
    
    def _cleanup_old_connections(self):
        """Periodically clean up old connection states"""
        while self._running:
            time.sleep(CONNECTION_CLEANUP_INTERVAL)
            current_time = time.time()
            
            with self._lock:
                # Remove connections older than MAX_CONNECTION_AGE
                keys_to_remove = [
                    key for key, state in self.connection_states.items()
                    if current_time - state['last_update'] > MAX_CONNECTION_AGE
                ]
                for key in keys_to_remove:
                    del self.connection_states[key]
                
                if keys_to_remove:
                    print(f"Cleaned up {len(keys_to_remove)} old connections")
    
    def start_monitoring(self):
        """Start capturing network traffic"""
        print(f"Starting network monitoring on interface: {self.interface}")
        print(f"📡 Capturing ALL network traffic from {self.interface}")
        print("   Press Ctrl+C to stop")
        print(f"   Waiting for {PACKETS_PER_CONNECTION} packets per connection before analysis...")
        print("\n💡 The monitor will automatically capture:")
        print("   - All incoming/outgoing network traffic")
        print("   - Web browsing, downloads, system updates")
        print("   - Any network activity on this interface")
        print("   No manual traffic generation needed!\n")
        
        # Test API connection before starting (use /analyze endpoint which doesn't require login)
        try:
            test_response = requests.post(
                "http://localhost:5000/analyze",
                json={'test': 'connection'},
                timeout=2
            )
            if test_response.status_code == 200:
                print("✓ IDS API is running and accessible\n")
            else:
                print(f"⚠️  IDS API returned status {test_response.status_code}\n")
        except requests.exceptions.ConnectionError:
            print("❌ WARNING: Cannot connect to IDS API at http://localhost:5000")
            print("   Please start the dashboard server first!\n")
        except Exception as e:
            print(f"⚠️  Could not verify API connection: {e}\n")
        
        # Show packet capture status
        print("📊 Monitoring started. Waiting for network traffic...")
        print("   (You should see '✓ Analyzed' messages when traffic is detected)\n")
        
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_handler,
                store=False
            )
        except KeyboardInterrupt:
            print("\nStopping network monitor...")
            self._running = False
            self.executor.shutdown(wait=True)
        except Exception as e:
            print(f"Error during packet capture: {e}")
            print("Make sure you have proper permissions (run with sudo)")
            self._running = False
            self.executor.shutdown(wait=True)

if __name__ == "__main__":
    import sys
    
    # Get interface from command line or use default
    interface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    
    print("=" * 60)
    print("Network Traffic Monitor for IDS")
    print("=" * 60)
    print(f"Interface: {interface}")
    print("Make sure the IDS API is running on http://localhost:5000")
    print("=" * 60 + "\n")
    
    monitor = NetworkMonitor(interface=interface)
    monitor.start_monitoring()