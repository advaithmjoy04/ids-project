# Fix: ModuleNotFoundError - No module named 'flask'

## Problem
You're getting `ModuleNotFoundError: No module named 'flask'` because:
1. Virtual environment is not activated, OR
2. Packages are not installed in the virtual environment

## Solution

### Step 1: Navigate to Project Directory
```bash
cd ~/ids-project/ids_project
```

### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt:
```
(venv) kali@kali:~/ids-project/ids_project$
```

### Step 3: Verify Flask is Installed
```bash
pip list | grep flask
```

If Flask is not listed, install requirements:
```bash
pip install -r data/requirements.txt
```

### Step 4: Start Server (WITH venv activated)
```bash
python3 dashboard/start_server.py --server gunicorn --port 5000
```

---

## Complete Fix Commands

```bash
# 1. Go to project directory
cd ~/ids-project/ids_project

# 2. Activate virtual environment (IMPORTANT!)
source venv/bin/activate

# 3. Check if packages are installed
pip list | grep flask

# 4. If not installed, install them
pip install -r data/requirements.txt

# 5. Now start the server
python3 dashboard/start_server.py --server gunicorn --port 5000
```

---

## Alternative: Use the Startup Script (Easier)

The startup script automatically activates the venv:

```bash
cd ~/ids-project/ids_project
./dashboard/start_server.sh
```

This script handles venv activation automatically!

---

## If Virtual Environment Doesn't Exist

If `venv/` directory doesn't exist, create it:

```bash
cd ~/ids-project/ids_project

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install all packages
pip install --upgrade pip
pip install -r data/requirements.txt

# Now start server
python3 dashboard/start_server.py --server gunicorn --port 5000
```

---

## Quick Check Commands

```bash
# Check if venv exists
ls -la venv/

# Check if venv is activated (should show venv path)
which python3

# Should show: /home/kali/ids-project/ids_project/venv/bin/python3

# If it shows: /usr/bin/python3 (system Python), venv is NOT activated!
```

---

## Always Remember

**Before running any Python command, activate the virtual environment:**
```bash
source venv/bin/activate
```

Or use the startup script which does it automatically:
```bash
./dashboard/start_server.sh
```

