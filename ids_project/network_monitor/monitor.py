"""
Network Traffic Monitor - Captures live network traffic
Processes packets and sends to IDS for analysis
"""

from scapy.all import sniff, IP, TCP, UDP, ICMP
import pandas as pd
import numpy as np
from collections import defaultdict
import time
from datetime import datetime
import threading
import json
import requests

class NetworkMonitor:
    def __init__(self, interface="eth0", queue_size=100):
        self.interface = interface
        self.queue_size = queue_size
        self.connection_states = defaultdict(lambda: {
            'packets': [],
            'start_time': time.time(),
            'features': {}
        })
        self.feature_window = []
        self.api_url = "http://localhost:5000/analyze"
        
    def extract_packet_features(self, packet):
        """Extract features from a single packet"""
        try:
            if not packet.haslayer(IP):
                return None
            
            ip_layer = packet[IP]
            features = {
                'timestamp': datetime.now().isoformat(),
                'src_ip': ip_layer.src,
                'dst_ip': ip_layer.dst,
                'protocol': ip_layer.proto,
                'packet_size': len(packet),
                'ttl': ip_layer.ttl,
            }
            
            # TCP features
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                features.update({
                    'src_port': tcp_layer.sport,
                    'dst_port': tcp_layer.dport,
                    'tcp_flags': tcp_layer.flags.value if hasattr(tcp_layer.flags, 'value') else 0,
                    'window_size': tcp_layer.window,
                    'protocol_type': 'tcp'
                })
            # UDP features
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                features.update({
                    'src_port': udp_layer.sport,
                    'dst_port': udp_layer.dport,
                    'protocol_type': 'udp'
                })
            # ICMP features
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
            print(f"Error extracting features: {e}")
            return None
    
    def compute_connection_features(self, packets):
        """Compute aggregated connection features from packet list"""
        if not packets:
            return None
        
        try:
            # Basic stats
            duration = packets[-1]['timestamp_raw'] - packets[0]['timestamp_raw']
            src_bytes = sum(p.get('packet_size', 0) for p in packets if p.get('src_ip') == packets[0].get('src_ip'))
            dst_bytes = sum(p.get('packet_size', 0) for p in packets if p.get('dst_ip') == packets[0].get('src_ip'))
            
            # Service and protocol
            protocol_type = packets[0].get('protocol_type', 'tcp')
            dst_port = packets[0].get('dst_port', 0)
            
            # Map port to service (simplified)
            service = self.map_port_to_service(dst_port)
            
            # Connection flags (simplified)
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
            features['src_ip'] = packets[0].get('src_ip')
            features['dst_ip'] = packets[0].get('dst_ip')
            features['timestamp'] = packets[0].get('timestamp')
            
            return features
            
        except Exception as e:
            print(f"Error computing connection features: {e}")
            return None
    
    def map_port_to_service(self, port):
        """Map port number to service name"""
        port_map = {
            20: 'ftp_data', 21: 'ftp', 22: 'ssh', 23: 'telnet',
            25: 'smtp', 53: 'domain_u', 80: 'http', 110: 'pop_3',
            143: 'imap4', 443: 'https', 3306: 'mysql', 5432: 'postgres',
            6379: 'redis', 8080: 'http_8080', 8443: 'https_alt'
        }
        return port_map.get(port, 'other')
    
    def packet_handler(self, packet):
        """Handle each captured packet"""
        features = self.extract_packet_features(packet)
        
        if features:
            features['timestamp_raw'] = time.time()
            
            # Create connection key
            conn_key = f"{features['src_ip']}:{features.get('src_port', 0)}-{features['dst_ip']}:{features.get('dst_port', 0)}"
            
            # Add to connection state
            self.connection_states[conn_key]['packets'].append(features)
            
            # If we have enough packets, analyze the connection
            if len(self.connection_states[conn_key]['packets']) >= 5:
                conn_features = self.compute_connection_features(
                    self.connection_states[conn_key]['packets']
                )
                
                if conn_features:
                    # Send to IDS for analysis
                    self.send_to_ids(conn_features)
                    
                # Clear old packets
                self.connection_states[conn_key]['packets'] = []
    
    def send_to_ids(self, features):
        """Send features to IDS API for analysis"""
        try:
            response = requests.post(
                self.api_url,
                json=features,
                timeout=2
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('threat_detected'):
                    print(f"\n⚠️  THREAT DETECTED!")
                    print(f"   Source: {features['src_ip']}")
                    print(f"   Destination: {features['dst_ip']}")
                    print(f"   Confidence: {result.get('confidence', 0):.2%}")
                    print(f"   Time: {features['timestamp']}\n")
                    
        except requests.exceptions.RequestException as e:
            # API might not be running yet
            pass
        except Exception as e:
            print(f"Error sending to IDS: {e}")
    
    def start_monitoring(self):
        """Start capturing network traffic"""
        print(f"Starting network monitoring on interface: {self.interface}")
        print("Capturing packets... Press Ctrl+C to stop\n")
        
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_handler,
                store=False
            )
        except KeyboardInterrupt:
            print("\nStopping network monitor...")
        except Exception as e:
            print(f"Error during packet capture: {e}")
            print("Make sure you have proper permissions (run with sudo)")

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