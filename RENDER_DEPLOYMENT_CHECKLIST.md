# Render Deployment Checklist ✅

## Pre-Deployment

- [ ] Push latest code to GitHub repository
- [ ] Verify `requirements.txt` includes all dependencies
- [ ] Confirm `render.yaml` is properly configured

## Render Dashboard Configuration

### 1. Service Settings
- [ ] **Environment:** Python 3
- [ ] **Build Command:** `pip install -r requirements.txt`
- [ ] **Start Command:** `cd src && python server_fastmcp.py`
- [ ] **Region:** Choose closest to your users (e.g., Oregon)
- [ ] **Plan:** Free tier

### 2. Environment Variables

Configure these in Render Dashboard → Environment:

```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=$PORT
DEBUG=false
DATABASE_URL=sqlite+aiosqlite:////tmp/logistics.db
```

### 3. Important Notes

#### Database Location
✅ **MUST use `/tmp/logistics.db`**
- Render's free tier has a read-only filesystem except for `/tmp`
- Database is automatically created on startup
- Sample data is seeded automatically if database is empty

#### Data Persistence
⚠️ **Database is ephemeral on free tier:**
- Data persists during instance lifetime
- **Lost on redeployments** (code updates, restarts)
- Automatically recreated with sample data on startup

For persistent data, consider:
- Upgrading to Render paid plan with persistent disks
- Using external database (PostgreSQL, MySQL)

## Post-Deployment Verification

### 1. Check Logs
- [ ] Service started successfully
- [ ] Database initialized: `✅ Database initialized`
- [ ] Database seeded (if empty): `✅ Seeded 10 shipments successfully!`
- [ ] Server running on assigned port

### 2. Test Health Endpoint
```bash
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 3. Test MCP Tools
```bash
curl https://your-app.onrender.com/mcp/tools
```

Should return list of available tools.

### 4. Test Sample Query
```bash
curl -X POST https://your-app.onrender.com/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all shipments with risk flags"}'
```

## 11Labs Integration

After successful deployment:

1. **Copy Render URL**
   ```
   https://your-app-name.onrender.com
   ```

2. **Configure 11Labs Agent**
   - Go to 11Labs Dashboard
   - Navigate to your agent settings
   - Set MCP Server URL to your Render URL

3. **Test Voice Commands**
   - "Show me risky shipments"
   - "What's the status of container MSCU1234567?"
   - "List all delayed shipments"

## Troubleshooting

### Issue: "Permission denied" or "Read-only file system"
**Solution:** Verify `DATABASE_URL=sqlite+aiosqlite:////tmp/logistics.db` (note the 4 slashes)

### Issue: "Module not found"
**Solution:** Check build logs, ensure all dependencies in `requirements.txt`

### Issue: Port binding error
**Solution:** Ensure `SERVER_PORT=$PORT` (Render assigns port dynamically)

### Issue: Database empty
**Solution:** This is normal! Server auto-seeds on startup. Check logs for confirmation.

### Issue: Service keeps restarting
**Solution:** 
1. Check logs for Python errors
2. Verify start command: `cd src && python server_fastmcp.py`
3. Ensure all dependencies installed

## Monitoring

### Key Metrics to Watch
- **Response time:** Should be < 1s for most queries
- **Uptime:** Monitor for unexpected restarts
- **Logs:** Watch for errors or warnings

### Log Messages to Look For

✅ Success indicators:
```
✅ Database initialized
✅ Database ready with existing data
✅ Seeded 10 shipments successfully!
Server running on 0.0.0.0:XXXXX
```

❌ Error indicators:
```
❌ Error: [error message]
Failed to initialize database
Permission denied
```

## Redeployment

When you push new code:

1. **Automatic trigger:** Render detects GitHub push
2. **Build phase:** Installs dependencies
3. **Start phase:** 
   - Creates new `/tmp/logistics.db`
   - Initializes tables
   - Seeds sample data
   - Starts server

⚠️ **Note:** Previous database data is lost (ephemeral storage)

## Quick Reference

```bash
# View logs
Click "Logs" tab in Render dashboard

# Manual deploy
Click "Manual Deploy" → "Deploy latest commit"

# Environment variables
Settings → Environment → Add/Edit

# Service info
Dashboard → Service → Settings
```

## Support

- **Render Status:** https://status.render.com
- **Render Docs:** https://render.com/docs
- **Project Docs:** See `docs/` folder

---

**Last Updated:** December 18, 2025
