"""
IDS API - Analyzes network traffic and sends alerts via Twilio
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import queue
import os
from twilio.rest import Client

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class IDSEngine:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.label_encoders = None
        self.threat_queue = queue.Queue()
        self.threat_history = []
        self.alert_threshold = 0.7  # Confidence threshold for alerts
        
        # Twilio configuration
        self.twilio_enabled = False
        self.setup_twilio()
        
        # Load model
        self.load_model()
        
    def setup_twilio(self):
        """Setup Twilio client"""
        try:
            # Get credentials from environment variables
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
            self.twilio_from = os.environ.get('TWILIO_PHONE_NUMBER', '')
            self.admin_phone = os.environ.get('ADMIN_PHONE_NUMBER', '')
            
            if account_sid and auth_token and self.twilio_from and self.admin_phone:
                self.twilio_client = Client(account_sid, auth_token)
                self.twilio_enabled = True
                print("✓ Twilio integration enabled")
            else:
                print("⚠ Twilio credentials not found. SMS alerts disabled.")
                print("  Set environment variables:")
                print("    - TWILIO_ACCOUNT_SID")
                print("    - TWILIO_AUTH_TOKEN")
                print("    - TWILIO_PHONE_NUMBER")
                print("    - ADMIN_PHONE_NUMBER")
        except Exception as e:
            print(f"⚠ Twilio setup failed: {e}")
            self.twilio_enabled = False
    
    def load_model(self):
        """Load trained model and preprocessing objects"""
        try:
            model_dir = '../data'
            self.model = joblib.load(f'{model_dir}/ids_model.pkl')
            self.scaler = joblib.load(f'{model_dir}/scaler.pkl')
            self.feature_names = joblib.load(f'{model_dir}/feature_names.pkl')
            self.label_encoders = joblib.load(f'{model_dir}/label_encoders.pkl')
            print("✓ Model loaded successfully")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            print("  Please train the model first using: python models/train_model.py")
    
    def preprocess_features(self, features):
        """Preprocess features for prediction"""
        try:
            # Create DataFrame
            df = pd.DataFrame([features])
            
            # Remove metadata fields
            metadata_fields = ['src_ip', 'dst_ip', 'timestamp', 'timestamp_raw']
            metadata = {k: features.get(k) for k in metadata_fields if k in features}
            for field in metadata_fields:
                if field in df.columns:
                    df = df.drop([field], axis=1)
            
            # Encode categorical features
            for col, encoder in self.label_encoders.items():
                if col in df.columns:
                    df[col] = df[col].astype(str).apply(
                        lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
                    )
            
            # Ensure all features are present
            for feature in self.feature_names:
                if feature not in df.columns:
                    df[feature] = 0
            
            # Reorder columns to match training
            df = df[self.feature_names]
            
            # Scale features
            scaled_features = self.scaler.transform(df)
            
            return scaled_features, metadata
            
        except Exception as e:
            print(f"Error preprocessing: {e}")
            return None, None
    
    def predict(self, features):
        """Predict if traffic is malicious"""
        if self.model is None:
            return {'error': 'Model not loaded'}
        
        try:
            # Preprocess
            scaled_features, metadata = self.preprocess_features(features)
            
            if scaled_features is None:
                return {'error': 'Preprocessing failed'}
            
            # Predict
            prediction = self.model.predict(scaled_features)[0]
            probabilities = self.model.predict_proba(scaled_features)[0]
            confidence = probabilities[1]  # Probability of attack
            
            threat_detected = prediction == 1
            
            result = {
                'threat_detected': bool(threat_detected),
                'confidence': float(confidence),
                'prediction': 'Attack' if threat_detected else 'Normal',
                'timestamp': metadata.get('timestamp', datetime.now().isoformat()),
                'src_ip': metadata.get('src_ip', 'unknown'),
                'dst_ip': metadata.get('dst_ip', 'unknown'),
            }
            
            # Add to history
            self.threat_history.append(result)
            
            # Keep only last 1000 threats
            if len(self.threat_history) > 1000:
                self.threat_history = self.threat_history[-1000:]
            
            # Send real-time update via WebSocket
            socketio.emit('threat_update', result)
            
            # Send alert if threat detected with high confidence
            if threat_detected and confidence >= self.alert_threshold:
                self.send_alert(result)
            
            return result
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {'error': str(e)}
    
    def send_alert(self, threat_info):
        """Send alert via Twilio SMS"""
        if not self.twilio_enabled:
            return
        
        try:
            message_body = (
                f"🚨 IDS ALERT\n"
                f"Threat Detected!\n"
                f"Source: {threat_info['src_ip']}\n"
                f"Destination: {threat_info['dst_ip']}\n"
                f"Confidence: {threat_info['confidence']:.1%}\n"
                f"Time: {threat_info['timestamp']}"
            )
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=self.twilio_from,
                to=self.admin_phone
            )
            
            print(f"✓ Alert sent via SMS: {message.sid}")
            
        except Exception as e:
            print(f"✗ Failed to send SMS alert: {e}")

# Initialize IDS engine
ids_engine = IDSEngine()

# API Routes
@app.route('/')
def index():
    """Serve dashboard"""
    return render_template('dashboard.html')

@app.route('/analyze', methods=['POST'])
def analyze_traffic():
    """Analyze network traffic"""
    try:
        features = request.json
        result = ids_engine.predict(features)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/threats', methods=['GET'])
def get_threats():
    """Get threat history"""
    return jsonify({
        'threats': ids_engine.threat_history[-100:],  # Last 100 threats
        'total': len(ids_engine.threat_history)
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    threats = ids_engine.threat_history
    
    if not threats:
        return jsonify({
            'total_analyzed': 0,
            'threats_detected': 0,
            'threat_rate': 0,
            'avg_confidence': 0
        })
    
    threats_detected = sum(1 for t in threats if t['threat_detected'])
    confidences = [t['confidence'] for t in threats if t['threat_detected']]
    
    return jsonify({
        'total_analyzed': len(threats),
        'threats_detected': threats_detected,
        'threat_rate': threats_detected / len(threats) if threats else 0,
        'avg_confidence': np.mean(confidences) if confidences else 0
    })

@app.route('/test-alert', methods=['POST'])
def test_alert():
    """Test Twilio alert"""
    if not ids_engine.twilio_enabled:
        return jsonify({'error': 'Twilio not configured'}), 400
    
    test_threat = {
        'src_ip': '192.168.1.100',
        'dst_ip': '192.168.1.1',
        'confidence': 0.95,
        'timestamp': datetime.now().isoformat()
    }
    
    ids_engine.send_alert(test_threat)
    return jsonify({'message': 'Test alert sent'})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("IDS API Server")
    print("=" * 60)
    print("Starting server on http://localhost:5000")
    print("Dashboard: http://localhost:5000")
    print("=" * 60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)