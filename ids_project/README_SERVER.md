# IDS Dashboard Server Setup

This guide explains how to run the IDS Dashboard in production mode.

## Quick Start for Kali Linux

### Automated Installation
```bash
# Run the installation script
cd ids-project
chmod +x install_kali.sh
./install_kali.sh
```

### Start Server (Manual)
```bash
cd ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh
```

### Setup as System Service (Recommended)
```bash
# Install and setup systemd service
sudo chmod +x setup_kali_service.sh
sudo ./setup_kali_service.sh

# Start the service
sudo systemctl start ids-dashboard

# Check status
sudo systemctl status ids-dashboard

# View logs
sudo journalctl -u ids-dashboard -f
```

## Quick Start (Other Platforms)

### Development Mode (Default)
```bash
# Run the Flask development server
python ids_project/dashboard/app.py
```

### Production Mode

#### Windows
```bash
# Using Waitress (recommended for Windows)
python ids_project/dashboard/start_server.py --server waitress --port 5000
```

#### Linux/Unix (Non-Kali)
```bash
# Using Gunicorn (recommended for Linux)
python3 ids_project/dashboard/start_server.py --server gunicorn --port 5000

# Or use the shell script
chmod +x ids_project/dashboard/start_server.sh
./ids_project/dashboard/start_server.sh
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
# Server Configuration
IDS_HOST=0.0.0.0
IDS_PORT=5000
IDS_DEBUG=False
IDS_WORKERS=4
IDS_SERVER_TYPE=waitress

# IDS Engine Configuration
IDS_MAX_HISTORY=1000
IDS_ALERT_THRESHOLD=0.7
IDS_STATS_CACHE_TTL=5

# Twilio (Optional)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
ADMIN_PHONE_NUMBER=your_admin_number
```

### Command Line Options

```bash
python dashboard/start_server.py --help

Options:
  --host HOST       Host to bind to (default: 0.0.0.0)
  --port PORT       Port to bind to (default: 5000)
  --debug           Enable debug mode
  --workers N       Number of worker processes (default: 4)
  --server TYPE     Server type: waitress, gunicorn, or dev
  --env-file PATH   Path to .env file
```

## Server Types

### 1. Waitress (Recommended for Windows/Cross-platform)
- Pure Python, no compilation needed
- Works on Windows, Linux, macOS
- Good for moderate traffic

```bash
python dashboard/start_server.py --server waitress --workers 4
```

### 2. Gunicorn (Recommended for Linux)
- High performance
- Requires eventlet/gevent for WebSocket support
- Linux/Unix only

```bash
python dashboard/start_server.py --server gunicorn --workers 4
```

### 3. Development Server
- Flask built-in server
- Auto-reload on code changes
- Not for production use

```bash
python dashboard/start_server.py --server dev --debug
```

## Production Deployment

### Using systemd (Kali Linux)

**Automated Setup:**
```bash
# Use the provided setup script
sudo chmod +x setup_kali_service.sh
sudo ./setup_kali_service.sh
```

**Manual Setup:**
Create `/etc/systemd/system/ids-dashboard.service`:

```ini
[Unit]
Description=IDS Dashboard Server
After=network.target

[Service]
Type=simple
User=kali
Group=kali
WorkingDirectory=/path/to/ids-project/ids_project
Environment="PATH=/path/to/ids-project/ids_project/venv/bin"
ExecStart=/path/to/ids-project/ids_project/venv/bin/python3 /path/to/ids-project/ids_project/dashboard/start_server.py --server gunicorn --port 5000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ids-dashboard
sudo systemctl start ids-dashboard
sudo systemctl status ids-dashboard
```

### Using Nginx as Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "dashboard/start_server.py", "--server", "waitress", "--host", "0.0.0.0", "--port", "5000"]
```

Build and run:
```bash
docker build -t ids-dashboard .
docker run -p 5000:5000 --env-file .env ids-dashboard
```

## Performance Tuning

### Worker Processes
- **Waitress**: Use 4-8 workers for moderate traffic
- **Gunicorn**: Use (2 x CPU cores) + 1 workers

### Memory
- Each worker uses ~100-200MB RAM
- Monitor with: `htop` or `top`

### WebSocket Connections
- Default: 1000 connections per worker
- Increase if needed: `--workers 8`

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000  # Linux/Mac
netstat -ano | findstr :5000  # Windows

# Kill process or change port
python dashboard/start_server.py --port 8080
```

### WebSocket Not Working
- Ensure you're using eventlet/gevent with Gunicorn
- Check firewall settings
- Verify reverse proxy configuration

### Model Not Loading
- Ensure model files exist in `ids_project/data/`
- Check file permissions
- Run training script first: `python models/train_model.py`

## Monitoring

### Logs
- Check application logs in console output
- For systemd: `journalctl -u ids-dashboard -f`

### Health Check
```bash
curl http://localhost:5000/stats
```

## Security Considerations

1. **Change default port** in production
2. **Use HTTPS** with SSL certificates
3. **Set CORS origins** to specific domains
4. **Use environment variables** for secrets
5. **Run as non-root user** in production
6. **Enable firewall** rules
7. **Regular updates** of dependencies

## Support

For issues or questions, check:
- Application logs
- System logs
- Network connectivity
- Model file existence

