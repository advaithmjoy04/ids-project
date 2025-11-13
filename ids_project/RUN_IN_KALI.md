# How to Run IDS Dashboard in Kali Linux

## 🚀 Quick Start (3 Steps)

### Step 1: Clone/Download the Project
```bash
# If you have git installed
git clone https://github.com/advaithmjoy04/ids-project.git
cd ids-project/ids_project

# OR if you already have the project, navigate to it
cd /path/to/ids-project/ids_project
```

### Step 2: Run Installation Script
```bash
# Make script executable
chmod +x ../install_kali.sh

# Run installation (creates venv, installs packages)
../install_kali.sh
```

### Step 3: Start the Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
./dashboard/start_server.sh
```

**That's it!** The dashboard will be available at `http://localhost:5000`

---

## 📋 Detailed Step-by-Step Guide

### Prerequisites Check
```bash
# Check Python version (should be 3.8+)
python3 --version

# Check if pip is installed
pip3 --version
```

If Python or pip are missing:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Installation Process

#### Option A: Automated Installation (Recommended)
```bash
# 1. Navigate to project root
cd ids-project

# 2. Make installation script executable
chmod +x install_kali.sh

# 3. Run installation
./install_kali.sh
```

This script will:
- ✅ Create Python virtual environment
- ✅ Install all required packages
- ✅ Create `.env` configuration file
- ✅ Check for model files

#### Option B: Manual Installation
```bash
# 1. Navigate to project directory
cd ids-project/ids_project

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip setuptools wheel

# 5. Install requirements
pip install -r data/requirements.txt
```

### Starting the Server

#### Method 1: Quick Start (Development/Testing)
```bash
cd ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh
```

#### Method 2: Using Python Script Directly
```bash
cd ids-project/ids_project
source venv/bin/activate
python3 dashboard/start_server.py --server gunicorn --port 5000
```

#### Method 3: As a System Service (Production)
```bash
# Setup systemd service
cd ids-project
sudo chmod +x setup_kali_service.sh
sudo ./setup_kali_service.sh

# Start the service
sudo systemctl start ids-dashboard

# Check status
sudo systemctl status ids-dashboard

# View logs
sudo journalctl -u ids-dashboard -f
```

### Accessing the Dashboard

1. **From Kali Linux (localhost):**
   ```bash
   firefox http://localhost:5000
   # or
   chromium http://localhost:5000
   ```

2. **From Another Machine:**
   - Find your Kali IP:
     ```bash
     hostname -I
     # or
     ip addr show
     ```
   - Access from browser: `http://<kali-ip>:5000`
   - If firewall blocks, allow port:
     ```bash
     sudo ufw allow 5000/tcp
     # or
     sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
     ```

### Login Credentials
- **Username:** `admin`
- **Password:** `admin`

---

## 🔧 Common Commands

### Start Server
```bash
cd ids-project/ids_project
source venv/bin/activate
./dashboard/start_server.sh
```

### Stop Server
- If running manually: Press `Ctrl+C` in terminal
- If running as service: `sudo systemctl stop ids-dashboard`

### Check if Server is Running
```bash
# Check process
ps aux | grep start_server

# Check port
sudo netstat -tlnp | grep 5000
# or
sudo ss -tlnp | grep 5000
```

### View Logs
```bash
# If running as service
sudo journalctl -u ids-dashboard -f

# If running manually, logs appear in terminal
```

### Restart Server
```bash
# If service
sudo systemctl restart ids-dashboard

# If manual, stop (Ctrl+C) and start again
```

---

## 🐛 Troubleshooting

### Problem: "Permission denied" when running scripts
```bash
# Solution: Make scripts executable
chmod +x dashboard/start_server.sh
chmod +x install_kali.sh
chmod +x setup_kali_service.sh
```

### Problem: "Port 5000 already in use"
```bash
# Find what's using the port
sudo lsof -i :5000

# Kill the process or change port
python3 dashboard/start_server.py --port 8080
```

### Problem: "Module not found" errors
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall requirements
pip install -r data/requirements.txt
```

### Problem: "Model files not found"
```bash
# Train the model first
cd ids-project/ids_project
source venv/bin/activate
python models/train_model.py
```

### Problem: "Cannot connect to server"
```bash
# Check if server is running
ps aux | grep start_server

# Check firewall
sudo ufw status
sudo ufw allow 5000/tcp

# Check if binding to correct interface
# Edit .env file: IDS_HOST=0.0.0.0 (not 127.0.0.1)
```

### Problem: "Gunicorn not found"
```bash
source venv/bin/activate
pip install gunicorn eventlet
```

---

## 📝 Configuration

### Edit Configuration File
```bash
nano ids_project/.env
```

Key settings:
- `IDS_PORT=5000` - Change port if needed
- `IDS_WORKERS=4` - Number of worker processes
- `IDS_SERVER_TYPE=gunicorn` - Server type
- `ADMIN_USERNAME=admin` - Login username
- `ADMIN_PASSWORD=admin` - Login password

### Change Default Port
```bash
# Edit .env file
IDS_PORT=8080

# Or start with custom port
python3 dashboard/start_server.py --port 8080
```

---

## 🔄 Complete Workflow Example

```bash
# 1. Navigate to project
cd ~/ids-project/ids_project

# 2. Activate virtual environment
source venv/bin/activate

# 3. (First time only) Train the model
python models/train_model.py

# 4. Start the server
./dashboard/start_server.sh

# 5. Open browser
firefox http://localhost:5000

# 6. Login with admin/admin

# 7. (Optional) Start network monitoring in another terminal
cd network_monitor
sudo python monitor.py
```

---

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Install | `./install_kali.sh` |
| Start Server | `./dashboard/start_server.sh` |
| Stop Server | `Ctrl+C` |
| Check Status | `sudo systemctl status ids-dashboard` |
| View Logs | `sudo journalctl -u ids-dashboard -f` |
| Access Dashboard | `http://localhost:5000` |
| Login | `admin` / `admin` |

---

## 💡 Tips

1. **Keep Server Running After SSH Disconnect:**
   ```bash
   # Use tmux or screen
   sudo apt install tmux
   tmux
   ./dashboard/start_server.sh
   # Press Ctrl+B then D to detach
   # Reattach: tmux attach
   ```

2. **Run in Background:**
   ```bash
   nohup ./dashboard/start_server.sh > server.log 2>&1 &
   ```

3. **Monitor Resource Usage:**
   ```bash
   htop -p $(pgrep -f start_server)
   ```

4. **Change Admin Password:**
   ```bash
   # Edit .env file
   ADMIN_PASSWORD=your_secure_password
   ```

---

## 📚 Additional Resources

- **Full Documentation:** See `README_SERVER.md`
- **Kali Quick Start:** See `KALI_QUICKSTART.md`
- **GitHub Repository:** https://github.com/advaithmjoy04/ids-project

---

## ✅ Verification Checklist

After installation, verify:
- [ ] Virtual environment created (`venv/` directory exists)
- [ ] All packages installed (`pip list` shows all requirements)
- [ ] Model files exist (`data/*.pkl` files)
- [ ] Server starts without errors
- [ ] Can access `http://localhost:5000`
- [ ] Can login with admin/admin
- [ ] Dashboard displays correctly

If all checked, you're ready to go! 🎉

