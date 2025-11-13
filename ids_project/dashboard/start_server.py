#!/usr/bin/env python3
"""
Startup script for IDS Dashboard Server
Supports both development and production modes
"""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    parser = argparse.ArgumentParser(description='Start IDS Dashboard Server')
    parser.add_argument(
        '--host',
        default=os.environ.get('IDS_HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.environ.get('IDS_PORT', 5000)),
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.environ.get('IDS_DEBUG', 'False').lower() == 'true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=int(os.environ.get('IDS_WORKERS', 4)),
        help='Number of worker processes (default: 4)'
    )
    parser.add_argument(
        '--server',
        choices=['waitress', 'gunicorn', 'dev'],
        default=os.environ.get('IDS_SERVER_TYPE', 'waitress'),
        help='Server type: waitress (Windows), gunicorn (Linux), or dev (development)'
    )
    parser.add_argument(
        '--env-file',
        type=str,
        help='Path to .env file for configuration'
    )
    
    args = parser.parse_args()
    
    # Load environment variables from .env file if provided
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
    elif Path('.env').exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    # Set environment variables from args
    os.environ['IDS_HOST'] = args.host
    os.environ['IDS_PORT'] = str(args.port)
    os.environ['IDS_DEBUG'] = str(args.debug)
    os.environ['IDS_WORKERS'] = str(args.workers)
    os.environ['IDS_SERVER_TYPE'] = args.server
    
    if args.server == 'dev':
        # Development server
        from dashboard.app import app, socketio
        print("\n" + "=" * 60)
        print("IDS Development Server")
        print("=" * 60)
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Debug: {args.debug}")
        print("=" * 60)
        print(f"\nDashboard available at: http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
        print("Press Ctrl+C to stop\n")
        
        socketio.run(
            app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.debug
        )
    else:
        # Production server
        from dashboard.server import run_production_server, run_gunicorn_server
        
        if args.server == 'gunicorn' and sys.platform != 'win32':
            run_gunicorn_server()
        else:
            run_production_server()

if __name__ == '__main__':
    main()

