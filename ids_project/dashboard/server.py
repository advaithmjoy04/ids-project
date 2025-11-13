"""
Production Server for IDS Dashboard
Uses Waitress (Windows-compatible) or Gunicorn (Linux) for production deployment
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.app import app, socketio

# Configuration
HOST = os.environ.get('IDS_HOST', '0.0.0.0')
PORT = int(os.environ.get('IDS_PORT', 5000))
DEBUG = os.environ.get('IDS_DEBUG', 'False').lower() == 'true'
WORKERS = int(os.environ.get('IDS_WORKERS', 4))

def run_production_server():
    """Run production server with Waitress (cross-platform)"""
    try:
        from waitress import serve
        print("\n" + "=" * 60)
        print("IDS Production Server (Waitress)")
        print("=" * 60)
        print(f"Host: {HOST}")
        print(f"Port: {PORT}")
        print(f"Workers: {WORKERS}")
        print(f"Debug: {DEBUG}")
        print("=" * 60)
        print(f"\nDashboard available at: http://{HOST if HOST != '0.0.0.0' else 'localhost'}:{PORT}")
        print("Press Ctrl+C to stop\n")
        
        # Waitress doesn't support SocketIO directly, so we use the Flask-SocketIO server
        # For production with WebSocket support, use eventlet or gevent
        if socketio:
            socketio.run(
                app,
                host=HOST,
                port=PORT,
                debug=DEBUG,
                use_reloader=False,
                log_output=True
            )
        else:
            serve(app, host=HOST, port=PORT, threads=WORKERS)
            
    except ImportError:
        print("Waitress not installed. Installing...")
        print("Run: pip install waitress")
        print("\nFalling back to development server...")
        socketio.run(app, host=HOST, port=PORT, debug=DEBUG)

def run_gunicorn_server():
    """Run production server with Gunicorn (Linux/Unix)"""
    try:
        import gunicorn.app.base
        from gunicorn.six import iteritems
        
        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super(StandaloneApplication, self).__init__()
            
            def load_config(self):
                config = {key: value for key, value in iteritems(self.options)
                          if key in self.cfg.settings and value is not None}
                for key, value in iteritems(config):
                    self.cfg.set(key.lower(), value)
            
            def load(self):
                return self.application
        
        options = {
            'bind': f'{HOST}:{PORT}',
            'workers': WORKERS,
            'worker_class': 'eventlet',
            'worker_connections': 1000,
            'timeout': 120,
            'keepalive': 5,
        }
        
        print("\n" + "=" * 60)
        print("IDS Production Server (Gunicorn)")
        print("=" * 60)
        print(f"Host: {HOST}")
        print(f"Port: {PORT}")
        print(f"Workers: {WORKERS}")
        print("=" * 60)
        print(f"\nDashboard available at: http://{HOST if HOST != '0.0.0.0' else 'localhost'}:{PORT}")
        print("Press Ctrl+C to stop\n")
        
        StandaloneApplication(app, options).run()
        
    except ImportError:
        print("Gunicorn not installed. Use Waitress or install Gunicorn:")
        print("Run: pip install gunicorn eventlet")
        run_production_server()

if __name__ == '__main__':
    # Check which server to use
    server_type = os.environ.get('IDS_SERVER_TYPE', 'waitress').lower()
    
    if server_type == 'gunicorn' and sys.platform != 'win32':
        run_gunicorn_server()
    else:
        run_production_server()

