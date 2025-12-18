# 🚀 Deployment Guide - Logistics MCP Server with 11Labs

## ✅ What Changed

**ELIMINATED** the bridge server! Now you only need to deploy **ONE SERVICE**: `server.py`

### Before (2 services):
```
11Labs → Bridge Server → MCP Server → Database
         (Port 8001)     (Port 8000)
```

### After (1 service):
```
11Labs → MCP Server → Database
         (Port 8000)
         ✅ /webhook endpoint built-in!
```

---

## 📦 Files to Deploy

Deploy **ONLY** these files to Render:

```
/Users/testing/Documents/cw-ai-server/
├── server.py              ← Main application (has /webhook endpoint!)
├── config.py              ← Configuration
├── tools.py               ← MCP tools
├── database/
│   ├── database.py        ← Database logic
│   └── models.py          ← Data models
├── auth.py                ← Authentication
├── utils.py               ← Utilities
├── requirements.txt       ← Dependencies
└── logistics.db           ← SQLite database (10 shipments)
```

**DO NOT DEPLOY:**
- ❌ `elevenlabs_bridge.py` (no longer needed!)
- ❌ `logistics-voice-ui/` (frontend, separate deployment)
- ❌ Demo files (`demo_*.py`, `ai_agent_client.py`)

---

## 🔧 Render Configuration

### Service Settings:

| Setting | Value |
|---------|-------|
| **Name** | `logistics-mcp-server` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `cd src && python server_fastmcp.py` |
| **Port** | Automatically assigned by Render |

### Environment Variables:

```bash
# Required
SERVER_HOST=0.0.0.0
SERVER_PORT=$PORT  # Render automatically sets this
DEBUG=false

# Database (must use /tmp on Render free tier)
DATABASE_URL=sqlite+aiosqlite:////tmp/logistics.db

# Optional
API_KEY=your-secure-api-key-here
LOG_LEVEL=INFO
```

### Important Notes:
- **Database Location:** Must be `/tmp/logistics.db` (Render's free tier only allows writes to `/tmp`)
- **Data Persistence:** Database is recreated on each deployment with sample data
- **Auto-seeding:** Server automatically initializes and seeds the database on startup

---

## 🎯 11Labs Configuration

### 1. Get Your Render URL
After deployment, Render gives you:
```
https://logistics-mcp-server.onrender.com
```

### 2. Update 11Labs Webhook
In 11Labs dashboard, set webhook to:
```
https://logistics-mcp-server.onrender.com/webhook
```

### 3. Configure Functions

Add these 5 functions in 11Labs dashboard:

#### Function 1: search_shipments
```json
{
  "name": "search_shipments",
  "description": "Search for shipments with optional filters like risk flag, status, container number",
  "parameters": {
    "type": "object",
    "properties": {
      "risk_flag": {"type": "boolean", "description": "Filter high-risk shipments"},
      "status": {"type": "string", "description": "Status code: IN_TRANSIT, DELIVERED, DELAYED"},
      "container_no": {"type": "string", "description": "Container number"},
      "limit": {"type": "integer", "description": "Max results (default: 5)"}
    }
  }
}
```

#### Function 2: get_shipment_details
```json
{
  "name": "get_shipment_details",
  "description": "Get detailed information about a specific shipment by ID or container number",
  "parameters": {
    "type": "object",
    "properties": {
      "shipment_id": {"type": "string", "description": "Shipment ID or container number"}
    },
    "required": ["shipment_id"]
  }
}
```

#### Function 3: track_vessel
```json
{
  "name": "track_vessel",
  "description": "Track a vessel by name and see all shipments on board",
  "parameters": {
    "type": "object",
    "properties": {
      "vessel_name": {"type": "string", "description": "Vessel name (e.g., MSC GULSUN)"}
    },
    "required": ["vessel_name"]
  }
}
```

#### Function 4: update_shipment_status
```json
{
  "name": "update_shipment_status",
  "description": "Update shipment status or flag as high-risk",
  "parameters": {
    "type": "object",
    "properties": {
      "identifier": {"type": "string", "description": "Shipment ID"},
      "is_risk": {"type": "boolean", "description": "Mark as high-risk"},
      "reason": {"type": "string", "description": "Reason for flag"}
    },
    "required": ["identifier"]
  }
}
```

#### Function 5: get_analytics
```json
{
  "name": "get_analytics",
  "description": "Get analytics and statistics about shipments",
  "parameters": {
    "type": "object",
    "properties": {
      "metric": {"type": "string", "description": "Metric to query"}
    }
  }
}
```

### 4. System Prompt

Copy the **entire prompt** from `ELEVENLABS_AGENT_PROMPT.md` into your agent's system prompt field.

---

## 🧪 Testing

### Test Server Health
```bash
curl https://logistics-mcp-server.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-12-16T..."
}
```

### Test Webhook Directly
```bash
curl -X POST https://logistics-mcp-server.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "function": "search_shipments",
    "arguments": {"risk_flag": true}
  }'
```

Expected response (plain string):
```
I found 4 shipments. Shipment 1: JOB-2025-002, delayed, currently at Suez Canal. ...
```

### Test with Voice Agent

Say to your 11Labs agent:
1. **"Show me all high-risk shipments"**
   - Should return 4 high-risk shipments
2. **"Where is container COSU9876543?"**
   - Should return location and status
3. **"Track shipment JOB-2025-002"**
   - Should return detailed tracking info

---

## 📊 Endpoints Reference

| Endpoint | Method | Purpose | Used By |
|----------|--------|---------|---------|
| `/` | GET | Server info | Health check |
| `/health` | GET | Health status | Monitoring |
| `/webhook` | POST | **11Labs voice agent** | **Main endpoint** |
| `/messages` | POST | MCP JSON-RPC | MCP clients |
| `/sse` | GET | Server-Sent Events | Real-time updates |

---

## 🔍 Monitoring & Logs

### View Logs on Render:
1. Go to your service dashboard
2. Click "Logs" tab
3. Watch for incoming requests:
   ```
   11Labs webhook: {'function': 'search_shipments', 'arguments': {...}}
   Voice response: I found 4 shipments...
   ```

### Common Log Patterns:

**✅ Success:**
```
INFO: 11Labs webhook: {'function': 'search_shipments', 'arguments': {'risk_flag': True}}
INFO: Voice response: I found 4 shipments...
```

**❌ Error:**
```
ERROR: Webhook error: [detailed error]
```

---

## 🚨 Troubleshooting

### Issue: 11Labs not calling functions
**Solution:**
1. Check webhook URL is correct in dashboard
2. Verify all 5 functions are added and enabled
3. Check system prompt includes function descriptions

### Issue: Server returns 500 error
**Solution:**
1. Check Render logs for Python errors
2. Verify database file exists
3. Check environment variables are set

### Issue: "I couldn't find that shipment"
**Solution:**
1. Database might not be deployed
2. Check shipment ID is correct (e.g., `JOB-2025-002`)
3. Upload `logistics.db` to Render persistent disk

---

## 🎉 Success Checklist

- ✅ Server deployed to Render
- ✅ `/health` endpoint returns `{"status": "healthy"}`
- ✅ `/webhook` test returns plain string response
- ✅ 11Labs dashboard has webhook URL
- ✅ All 5 functions configured
- ✅ System prompt updated
- ✅ Voice queries work end-to-end

---

## 📝 What We Eliminated

### Old Architecture (Complex):
```python
# elevenlabs_bridge.py - 420 lines
- Query parsing logic (90 lines)
- Protocol translation (150 lines)
- Response formatting (180 lines)
- Separate server process
- Extra port, extra deployment
```

### New Architecture (Simple):
```python
# server.py - Added 150 lines
+ format_for_voice() - 70 lines
+ /webhook endpoint - 60 lines
+ Tool mapping - 20 lines
✅ Single deployment
✅ One codebase
✅ Easier to maintain
```

---

## 🚀 Next Steps

1. **Deploy to Render** (5 minutes)
2. **Configure 11Labs** (10 minutes)
3. **Test with voice** (5 minutes)
4. **Monitor logs** (ongoing)

You now have a **production-ready, single-service architecture** for voice-enabled logistics tracking! 🎉
