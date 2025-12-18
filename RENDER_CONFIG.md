# Render Deployment Configuration

## Important: Database Location

**On Render's free tier, the filesystem is read-only except for `/tmp`.**

The database MUST be stored in `/tmp/logistics.db` because:
- Render's ephemeral filesystem only allows writes to `/tmp`
- The database will be automatically recreated and seeded on each deployment
- Data persists during the instance lifetime but is lost on redeployments

## Build Command
```bash
pip install -r requirements.txt
```

## Start Command
```bash
cd src && python server_fastmcp.py
```

The server will automatically:
1. Create the database in `/tmp/logistics.db`
2. Initialize tables if they don't exist
3. Seed sample data if the database is empty

## Environment Variables

Set these in Render dashboard:

```
SERVER_HOST=0.0.0.0
SERVER_PORT=$PORT
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:////tmp/logistics.db
```

**Important:** The `DATABASE_URL` uses 4 slashes (`////`) because:
- `sqlite+aiosqlite://` - SQLAlchemy async SQLite dialect
- `/tmp/logistics.db` - Absolute path to database file

## Data Persistence

**Important Notes:**
- The `/tmp` directory data persists **during the instance lifetime**
- Data is **lost on redeployments** (code changes, manual restarts, etc.)
- The server automatically recreates and seeds the database on startup
- For production use with persistent data, consider:
  - Upgrading to Render's paid plan with persistent disks
  - Using an external database service (PostgreSQL, MySQL, etc.)

## Common Issues

### Issue 1: "Permission denied" or "Read-only filesystem"
**Solution:** Database must be in `/tmp/logistics.db`, not in the project directory

### Issue 2: "Module not found"
**Solution:** Verify requirements.txt is in root directory and build command ran successfully

### Issue 3: Port binding issues
**Solution:** Use `SERVER_PORT=$PORT` environment variable - Render assigns random port

### Issue 4: Database is empty after deployment
**Solution:** This is expected! The server automatically seeds sample data on first startup
