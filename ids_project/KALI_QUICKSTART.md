# IDS Dashboard - Kali Linux Quick Start Guide

## 🚀 Quick Installation

```bash
# 1. Navigate to project directory
cd ids-project

# 2. Run installation script
chmod +x install_kali.sh
./install_kali.sh
```

This will:
- Create a Python virtual environment
- Install all required packages
- Create a `.env` configuration file
- Check for model files

## 🎯 Starting the Server

### Option 1: Manual Start (Development/Testing)
```bash
cd ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh
```

The dashboard will be available at:
- `http://localhost:5000`
- `http://<your-kali-ip>:5000`

### Option 2: System Service (Production - Recommended)
```bash
# Setup systemd service
sudo chmod +x setup_kali_service.sh
sudo ./setup_kali_service.sh

# Start the service
sudo systemctl start ids-dashboard

# Check status
sudo systemctl status ids-dashboard

# View logs
sudo journalctl -u ids-dashboard -f
```

## ⚙️ Configuration

Edit the `.env` file in `ids_project/` directory:

```bash
nano ids_project/.env
```

Key settings:
- `IDS_PORT=5000` - Change port if needed
- `IDS_WORKERS=4` - Adjust based on CPU cores
- `IDS_SERVER_TYPE=gunicorn` - Keep as gunicorn for Kali

## 🔧 Common Commands

### Check if server is running
```bash
# If running as service
sudo systemctl status ids-dashboard

# If running manually, check process
ps aux | grep start_server
```

### Stop the server
```bash
# If running as service
sudo systemctl stop ids-dashboard

# If running manually
# Press Ctrl+C in the terminal
```

### Restart the server
```bash
sudo systemctl restart ids-dashboard
```

### View real-time logs
```bash
sudo journalctl -u ids-dashboard -f
```

### Check if port is in use
```bash
sudo netstat -tlnp | grep 5000
# or
sudo ss -tlnp | grep 5000
```

## 🌐 Accessing the Dashboard

### From Kali Linux (localhost)
```bash
firefox http://localhost:5000
# or
chromium http://localhost:5000
```

### From Another Machine
1. Find your Kali IP:
   ```bash
   hostname -I
   # or
   ip addr show
   ```

2. Access from another machine:
   ```
   http://<kali-ip>:5000
   ```

3. If firewall is blocking:
   ```bash
   # Allow port 5000
   sudo ufw allow 5000/tcp
   # or
   sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
   ```

## 🔒 Security Notes for Kali

1. **Firewall**: Configure firewall to allow port 5000
   ```bash
   sudo ufw enable
   sudo ufw allow 5000/tcp
   ```

2. **Run as non-root**: The service runs as your user (not root)

3. **Change default port**: Edit `.env` to use a different port

4. **HTTPS**: For production, set up SSL certificates

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port is already in use
sudo lsof -i :5000

# Check Python version
python3 --version  # Should be 3.8+

# Check if packages are installed
source venv/bin/activate
pip list | grep gunicorn
```

### Model not loading
```bash
# Check if model files exist
ls -la ids_project/data/*.pkl

# If missing, train the model
cd ids_project
source venv/bin/activate
python models/train_model.py
```

### Permission errors
```bash
# Make scripts executable
chmod +x dashboard/start_server.sh
chmod +x install_kali.sh
chmod +x setup_kali_service.sh
```

### Service won't start
```bash
# Check service logs
sudo journalctl -u ids-dashboard -n 50

# Check service file
sudo systemctl cat ids-dashboard

# Reload systemd
sudo systemctl daemon-reload
```

## 📊 Monitoring

### Check server health
```bash
curl http://localhost:5000/stats
```

### View active connections
```bash
sudo netstat -an | grep :5000
```

### Monitor resource usage
```bash
# CPU and memory
top -p $(pgrep -f start_server)

# Or use htop if installed
htop
```

## 🔄 Updating

```bash
cd ids-project/ids_project
source venv/bin/activate

# Update packages
pip install --upgrade -r data/requirements.txt

# Restart service
sudo systemctl restart ids-dashboard
```

## 📝 Next Steps

1. **Train the model** (if not done):
   ```bash
   cd ids_project
   source venv/bin/activate
   python models/train_model.py
   ```

2. **Start network monitoring**:
   ```bash
   cd ids_project/network_monitor
   sudo python monitor.py
   ```

3. **Access dashboard** and monitor threats in real-time!

## 💡 Tips

- Use `tmux` or `screen` to keep server running after SSH disconnect
- Monitor logs regularly for security events
- Set up Twilio for SMS alerts (optional)
- Configure firewall rules for production use

## 🆘 Need Help?

- Check `README_SERVER.md` for detailed documentation
- Review application logs: `sudo journalctl -u ids-dashboard`
- Check system logs: `dmesg | tail`

