"""
IDS API - Analyzes network traffic and sends alerts via Twilio
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import threading
from collections import deque
import os
from pathlib import Path
from twilio.rest import Client
from dotenv import load_dotenv
from functools import wraps

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Constants
MAX_HISTORY_SIZE = 1000
THREAT_DISPLAY_LIMIT = 100
ALERT_THRESHOLD = 0.7
METADATA_FIELDS = ['src_ip', 'dst_ip', 'timestamp', 'timestamp_raw']
MODEL_DIR = Path(__file__).parent.parent / 'data'

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'ids-dashboard-secret-key-change-in-production')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Admin credentials
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')

class IDSEngine:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.label_encoders = None
        # Use deque for efficient O(1) append and automatic size limiting
        self.threat_history = deque(maxlen=MAX_HISTORY_SIZE)
        self.alert_threshold = ALERT_THRESHOLD
        
        # Stats cache for performance
        self._stats_cache = None
        self._stats_cache_time = None
        self._cache_ttl = 5  # Cache for 5 seconds
        
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
            model_path = MODEL_DIR / 'ids_model.pkl'
            scaler_path = MODEL_DIR / 'scaler.pkl'
            features_path = MODEL_DIR / 'feature_names.pkl'
            encoders_path = MODEL_DIR / 'label_encoders.pkl'
            
            if not all(p.exists() for p in [model_path, scaler_path, features_path, encoders_path]):
                raise FileNotFoundError("One or more model files not found")
            
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_names = joblib.load(features_path)
            self.label_encoders = joblib.load(encoders_path)
            print("✓ Model loaded successfully")
        except FileNotFoundError as e:
            print(f"✗ Error loading model: {e}")
            print(f"  Model directory: {MODEL_DIR}")
            print("  Please train the model first using: python models/train_model.py")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            print("  Please train the model first using: python models/train_model.py")
    
    def preprocess_features(self, features):
        """Preprocess features for prediction"""
        try:
            # Extract metadata first (more efficient)
            metadata = {k: features.get(k) for k in METADATA_FIELDS if k in features}
            
            # Create feature dict excluding metadata
            feature_dict = {k: v for k, v in features.items() if k not in METADATA_FIELDS}
            
            # Create DataFrame from feature dict only
            df = pd.DataFrame([feature_dict])
            
            # Encode categorical features
            for col, encoder in self.label_encoders.items():
                if col in df.columns:
                    # More efficient encoding using vectorized operations
                    df[col] = df[col].astype(str).map(
                        lambda x: encoder.transform([x])[0] if x in encoder.classes_ else -1
                    )
            
            # Ensure all features are present (fill missing with 0)
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
            
            # Add to history (deque automatically limits size)
            self.threat_history.append(result)
            
            # Invalidate stats cache
            self._stats_cache = None
            
            # Send real-time update via WebSocket (non-blocking)
            socketio.emit('threat_update', result)
            
            # Send alert asynchronously if threat detected with high confidence
            if threat_detected and confidence >= self.alert_threshold:
                threading.Thread(target=self.send_alert, args=(result,), daemon=True).start()
            
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

# Allow /analyze endpoint without authentication (for network monitor)
@app.before_request
def check_api_access():
    """Allow /analyze endpoint without authentication"""
    if request.path == '/analyze' and request.method == 'POST':
        # Skip authentication for /analyze endpoint - allow API access
        return None
    # For all other routes, continue with normal processing

# Authentication decorator
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For API endpoints, return JSON error instead of redirect
        if request.path.startswith('/api/') or request.path == '/analyze':
            if 'logged_in' not in session or not session['logged_in']:
                return jsonify({'error': 'Authentication required'}), 401
        elif 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login', error=1))
    
    # If already logged in, redirect to dashboard
    if session.get('logged_in'):
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

# API Routes
@app.route('/')
@login_required
def index():
    """Serve dashboard"""
    username = session.get('username', 'admin')
    return render_template('dashboard.html', username=username)

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_traffic():
    """Analyze network traffic - Allow API access without login for monitor"""
    # Allow API access from localhost without authentication (for network monitor)
    # Dashboard routes still require login
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Check if request has JSON
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        features = request.json
        if not features:
            return jsonify({'error': 'No features provided'}), 400
        
        # Check if model is loaded
        if ids_engine.model is None:
            return jsonify({'error': 'Model not loaded. Please train the model first.'}), 503
        
        result = ids_engine.predict(features)
        
        # Ensure result is a dict (predict might return error dict)
        if not isinstance(result, dict):
            return jsonify({'error': 'Invalid prediction result'}), 500
        
        return jsonify(result)
    except Exception as e:
        # Always return JSON, even for errors
        return jsonify({'error': str(e)}), 400

@app.route('/threats', methods=['GET'])
@login_required
def get_threats():
    """Get threat history"""
    # Convert deque to list for JSON serialization (only last N items)
    threats_list = list(ids_engine.threat_history)[-THREAT_DISPLAY_LIMIT:]
    return jsonify({
        'threats': threats_list,
        'total': len(ids_engine.threat_history)
    })

@app.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get statistics with caching for performance"""
    engine = ids_engine
    current_time = datetime.now().timestamp()
    
    # Use cached stats if available and fresh
    if (engine._stats_cache is not None and 
        engine._stats_cache_time is not None and
        current_time - engine._stats_cache_time < engine._cache_ttl):
        return jsonify(engine._stats_cache)
    
    threats = engine.threat_history
    
    if not threats:
        stats = {
            'total_analyzed': 0,
            'threats_detected': 0,
            'threat_rate': 0,
            'avg_confidence': 0
        }
        engine._stats_cache = stats
        engine._stats_cache_time = current_time
        return jsonify(stats)
    
    # More efficient calculation using single pass
    threats_detected = 0
    confidences_sum = 0.0
    confidences_count = 0
    
    for threat in threats:
        if threat['threat_detected']:
            threats_detected += 1
            confidences_sum += threat['confidence']
            confidences_count += 1
    
    total = len(threats)
    stats = {
        'total_analyzed': total,
        'threats_detected': threats_detected,
        'threat_rate': threats_detected / total if total > 0 else 0,
        'avg_confidence': confidences_sum / confidences_count if confidences_count > 0 else 0
    }
    
    # Cache the results
    engine._stats_cache = stats
    engine._stats_cache_time = current_time
    
    return jsonify(stats)

@app.route('/test-alert', methods=['POST'])
@login_required
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
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    host = os.environ.get('IDS_HOST', '0.0.0.0')
    port = int(os.environ.get('IDS_PORT', 5000))
    debug = os.environ.get('IDS_DEBUG', 'True').lower() == 'true'
    
    print("\n" + "=" * 60)
    print("IDS API Server (Development Mode)")
    print("=" * 60)
    print(f"Starting server on http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"Dashboard: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    print(f"Debug: {debug}")
    print("=" * 60)
    print("\nFor production, use: python dashboard/start_server.py")
    print("=" * 60 + "\n")
    
    socketio.run(app, host=host, port=port, debug=debug)