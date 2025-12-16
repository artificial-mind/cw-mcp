# 🎯 11Labs Agent Configuration Guide

## Current Status
✅ Voice UI Connected to 11Labs Agent
✅ Bridge Server Running (Port 8001)
✅ MCP Server Running (Port 8000)
✅ Cloudflare Tunnel Active

## 🔴 ISSUE: Agent Not Calling MCP Functions

Your agent is connected but not executing logistics queries. You need to configure **Custom Tools** in the 11Labs dashboard.

---

## 📋 Step-by-Step Configuration

### 1. Go to 11Labs Dashboard
Open: https://elevenlabs.io/app/conversational-ai

### 2. Select Your Agent
- Click on agent: `agent_7501k3gxzjx4fj0ts0t2mydrgyvw`
- Go to **"Tools"** or **"Functions"** section

### 3. Add Webhook URL
**Webhook Endpoint:**
```
https://push-lynn-advice-hitting.trycloudflare.com/webhook
```

⚠️ **IMPORTANT**: This URL changes every time you restart the tunnel. Current URL is above.

### 4. Configure Custom Tools/Functions

Add these 5 functions to your agent:

---

#### Function 1: Search Shipments
```json
{
  "name": "search_shipments",
  "description": "Search for shipments with optional filters. Use this when user asks about shipments, containers, or tracking status.",
  "parameters": {
    "type": "object",
    "properties": {
      "container_no": {
        "type": "string",
        "description": "Container number (e.g., COSU9876543)"
      },
      "master_bill": {
        "type": "string",
        "description": "Master bill of lading number"
      },
      "status_code": {
        "type": "string",
        "description": "Status code: IN_TRANSIT, DELIVERED, DELAYED, CUSTOMS_HOLD"
      },
      "risk_flag": {
        "type": "boolean",
        "description": "Filter by high-risk shipments only"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of results (default: 5)"
      }
    }
  }
}
```

---

#### Function 2: Get Shipment Details
```json
{
  "name": "get_shipment_details",
  "description": "Get detailed information about a specific shipment by job ID or container number.",
  "parameters": {
    "type": "object",
    "properties": {
      "shipment_id": {
        "type": "string",
        "description": "Shipment job ID (e.g., JOB-2025-001) or container number"
      }
    },
    "required": ["shipment_id"]
  }
}
```

---

#### Function 3: Update Shipment Status
```json
{
  "name": "update_shipment_status",
  "description": "Update the status and notes for a shipment. Use when user reports changes or issues.",
  "parameters": {
    "type": "object",
    "properties": {
      "shipment_id": {
        "type": "string",
        "description": "Shipment job ID or container number"
      },
      "status_code": {
        "type": "string",
        "description": "New status: IN_TRANSIT, DELIVERED, DELAYED, CUSTOMS_HOLD"
      },
      "agent_notes": {
        "type": "string",
        "description": "Notes about the update or issue"
      }
    },
    "required": ["shipment_id"]
  }
}
```

---

#### Function 4: Track Vessel
```json
{
  "name": "track_vessel",
  "description": "Get real-time location and status of a vessel by name.",
  "parameters": {
    "type": "object",
    "properties": {
      "vessel_name": {
        "type": "string",
        "description": "Vessel name (e.g., MSC GULSUN, MAERSK ESSEX)"
      }
    },
    "required": ["vessel_name"]
  }
}
```

---

#### Function 5: Get Analytics
```json
{
  "name": "get_analytics",
  "description": "Get analytics and statistics about shipments, delays, and risk levels.",
  "parameters": {
    "type": "object",
    "properties": {
      "metric": {
        "type": "string",
        "description": "Metric to analyze: total_shipments, delayed_shipments, high_risk_shipments, by_status"
      }
    }
  }
}
```

---

## 5. Configure Agent Prompt

Add this to your agent's system prompt:

```
You are a logistics AI assistant with access to a real-time shipment tracking system. 

When users ask about shipments, containers, vessels, or logistics status:
1. Use the available functions to query the MCP server
2. Always provide clear, concise information
3. For high-risk shipments, explain the issue and any actions being taken
4. When tracking vessels, provide location and ETA information

Available tools:
- search_shipments: Find shipments with filters
- get_shipment_details: Get detailed info about specific shipment
- update_shipment_status: Update status and add notes
- track_vessel: Track vessel by name
- get_analytics: Get statistics and metrics

Example queries you should handle:
- "Show me all high-risk shipments"
- "Where is container COSU9876543?"
- "Track shipment JOB-2025-002"
- "What shipments are delayed?"
- "Where is the MSC GULSUN?"
```

---

## 6. Test the Configuration

### Test Webhook Directly
```bash
curl -X POST https://push-lynn-advice-hitting.trycloudflare.com/test \
  -H "Content-Type: application/json" \
  -d '{"query": "show me all high risk shipments"}'
```

### Test with Voice Agent
Once configured, try saying:
1. "Show me all high-risk shipments"
2. "Where is container COSU9876543?"
3. "What shipments are delayed?"
4. "Track shipment JOB-2025-002"

---

## 🔧 Troubleshooting

### Agent Not Calling Functions?
✅ Check webhook URL is correct in dashboard
✅ Verify functions are enabled/active
✅ Check agent prompt mentions the tools
✅ Make sure tunnel is running: `ps aux | grep cloudflared`

### Tunnel Not Working?
```bash
# Restart tunnel
cloudflared tunnel --url http://localhost:8001 > cloudflare_tunnel.log 2>&1 &

# Get new URL
cat cloudflare_tunnel.log | grep https
```

### Bridge Server Not Responding?
```bash
# Check if running
lsof -i :8001

# Restart if needed
python elevenlabs_bridge.py
```

---

## 📊 Current System State

| Component | Status | URL/Port |
|-----------|--------|----------|
| Voice UI | ✅ Running | http://localhost:3000 |
| MCP Server | ✅ Running | Port 8000 |
| Bridge Server | ✅ Running | Port 8001 |
| Cloudflare Tunnel | ✅ Running | https://push-lynn-advice-hitting.trycloudflare.com |
| 11Labs Agent | ✅ Connected | agent_7501k3gxzjx4fj0ts0t2mydrgyvw |
| Database | ✅ Ready | 10 shipments, 4 high-risk |

---

## 🎯 Next Steps

1. **Configure functions in 11Labs dashboard** (see above)
2. **Update agent prompt** to mention available tools
3. **Test with voice queries**
4. **Monitor logs** in the conversation UI

Once configured, your agent will be able to:
- ✅ Query real shipment data
- ✅ Track containers and vessels
- ✅ Update statuses
- ✅ Provide analytics
- ✅ All through natural voice conversation!

---

## 📝 Notes

- Cloudflare tunnel URL changes on restart - update in dashboard when needed
- Bridge server translates 11Labs calls to MCP format
- All conversation logs appear in the UI
- Agent has access to 10 real shipments in the database

**Current Webhook URL:** `https://push-lynn-advice-hitting.trycloudflare.com/webhook`

Update this in your 11Labs dashboard now! 🚀
