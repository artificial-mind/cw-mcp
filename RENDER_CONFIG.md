# Render Deployment Configuration

## Build Command
```bash
pip install -r requirements.txt
```

## Start Command (Choose one)

### Option 1: Using run.py (Recommended)
```bash
python run.py
```

### Option 2: Direct uvicorn (Alternative)
```bash
cd src && uvicorn server:app --host 0.0.0.0 --port $PORT
```

### Option 3: Using gunicorn (Production)
```bash
cd src && gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
```

## Environment Variables

Set these in Render dashboard:

```
SERVER_HOST=0.0.0.0
SERVER_PORT=$PORT
DEBUG=false
DATABASE_URL=sqlite:///logistics.db
```

## Common Issues

### Issue 1: "Can't open file run.py"
**Solution:** Make sure start command is just `python run.py` (not `python src/run.py`)

### Issue 2: "Module not found"
**Solution:** Verify requirements.txt is in root directory and build command ran successfully

### Issue 3: Port binding issues
**Solution:** Use `SERVER_PORT=$PORT` environment variable - Render assigns random port

---

## Quick Fix for Current Error

Your current error is because the start command might be wrong.

**Change start command to:**
```
python run.py
```

**NOT:**
```
python src/run.py
```

The `run.py` file is in the ROOT of your repository, not in `src/`.
