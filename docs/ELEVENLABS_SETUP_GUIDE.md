# 🌐 Connecting 11Labs Agent to Your Logistics MCP Server

## 🚀 Quick Setup Guide

Since ngrok setup is having issues, here are **3 alternative methods** to connect your 11Labs agent:

---

## ✅ **Method 1: Using localhost.run (Easiest - No Installation)**

### Step 1: Expose your bridge server
```bash
ssh -R 80:localhost:8001 localhost.run
```

This will give you a public URL like: `https://abc123.lhr.life`

### Step 2: Configure 11Labs
- Go to your 11Labs dashboard
- Find your agent settings
- Set webhook URL to: `https://abc123.lhr.life/webhook`

### Step 3: Test!
- Call your 11Labs agent
- Ask: "Show me all high-risk shipments"
- Watch it query your logistics system in real-time!

---

## ✅ **Method 2: Using serveo.net (No Installation)**

### Step 1: Expose your bridge server
```bash
ssh -R 80:localhost:8001 serveo.net
```

You'll get a URL like: `https://abc123.serveo.net`

### Step 2: Configure 11Labs
- Set webhook URL to: `https://abc123.serveo.net/webhook`

---

## ✅ **Method 3: Using Cloudflare Tunnel (Most Reliable)**

### Step 1: Install cloudflared
```bash
brew install cloudflare/cloudflare/cloudflared
```

### Step 2: Start tunnel
```bash
cloudflared tunnel --url http://localhost:8001
```

You'll get a URL like: `https://abc-def-123.trycloudflare.com`

### Step 3: Configure 11Labs
- Set webhook URL to: `https://abc-def-123.trycloudflare.com/webhook`

---

## 🎯 **11Labs Agent Configuration**

### In your 11Labs Dashboard:

1. **Go to your agent settings**
2. **Add Custom Functions/Tools**
3. **Configure webhook endpoint:**
   ```
   POST https://YOUR_PUBLIC_URL/webhook
   ```

4. **Function definitions to add:**

```json
{
  "functions": [
    {
      "name": "search_shipments",
      "description": "Search for shipments with filters like risk flag, status, container number",
      "parameters": {
        "type": "object",
        "properties": {
          "risk_flag": {
            "type": "boolean",
            "description": "Filter for high-risk shipments"
          },
          "status": {
            "type": "string",
            "description": "Filter by status: IN_TRANSIT, DELAYED, AT_PORT, DELIVERED, CUSTOMS_HOLD"
          },
          "container_no": {
            "type": "string",
            "description": "Search by container number"
          },
          "limit": {
            "type": "number",
            "description": "Maximum number of results (default 10)"
          }
        }
      }
    },
    {
      "name": "track_shipment",
      "description": "Get detailed tracking information for a specific shipment",
      "parameters": {
        "type": "object",
        "properties": {
          "identifier": {
            "type": "string",
            "description": "Shipment ID, container number, or master bill of lading"
          }
        },
        "required": ["identifier"]
      }
    },
    {
      "name": "update_shipment_eta",
      "description": "Update the estimated time of arrival for a shipment",
      "parameters": {
        "type": "object",
        "properties": {
          "shipment_id": {
            "type": "string",
            "description": "The shipment ID to update"
          },
          "new_eta": {
            "type": "string",
            "description": "New ETA in ISO 8601 format"
          },
          "reason": {
            "type": "string",
            "description": "Reason for the ETA change"
          }
        },
        "required": ["shipment_id", "new_eta", "reason"]
      }
    },
    {
      "name": "set_risk_flag",
      "description": "Flag a shipment as high-risk or remove the risk flag",
      "parameters": {
        "type": "object",
        "properties": {
          "shipment_id": {
            "type": "string",
            "description": "The shipment ID"
          },
          "is_risk": {
            "type": "boolean",
            "description": "true to flag as high-risk, false to clear"
          },
          "reason": {
            "type": "string",
            "description": "Reason for flagging/unflagging"
          }
        },
        "required": ["shipment_id", "is_risk", "reason"]
      }
    }
  ]
}
```

---

## 🧪 **Test Your Setup**

### Test 1: Local Test (Without 11Labs)
```bash
curl -X POST http://localhost:8001/test \
  -H "Content-Type: application/json" \
  -d '{"query": "show me all high risk shipments"}'
```

### Test 2: Through Public URL
```bash
curl -X POST https://YOUR_PUBLIC_URL/test \
  -H "Content-Type: application/json" \
  -d '{"query": "track shipment JOB-2025-002"}'
```

### Test 3: Simulate 11Labs Webhook
```bash
curl -X POST https://YOUR_PUBLIC_URL/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "search_shipments",
    "arguments": {
      "risk_flag": true,
      "limit": 5
    }
  }'
```

---

## 💬 **Example Voice Queries for 11Labs Agent**

Once connected, your 11Labs agent can handle queries like:

1. **"Show me all high-risk shipments"**
   - Agent calls `search_shipments` with `risk_flag: true`
   
2. **"Where is container COSU9876543?"**
   - Agent calls `search_shipments` with `container_no: "COSU9876543"`
   
3. **"Track shipment JOB-2025-002"**
   - Agent calls `track_shipment` with `identifier: "JOB-2025-002"`
   
4. **"What shipments are delayed?"**
   - Agent calls `search_shipments` with `status: "DELAYED"`
   
5. **"Update the ETA for JOB-2025-006 to December 25th due to port congestion"**
   - Agent calls `update_shipment_eta` with new date and reason

---

## 📊 **Current System Status**

✅ **Logistics MCP Server:** Running on port 8000  
✅ **11Labs Bridge:** Running on port 8001  
✅ **Database:** 10 shipments loaded (4 high-risk)  
✅ **All 5 tools:** Operational  

---

## 🎯 **Quick Start Command**

Choose one and run it:

```bash
# Option 1: localhost.run
ssh -R 80:localhost:8001 localhost.run

# Option 2: serveo.net
ssh -R 80:localhost:8001 serveo.net

# Option 3: Cloudflare (after installing cloudflared)
cloudflared tunnel --url http://localhost:8001
```

Then copy the public URL you get and paste it into your 11Labs agent configuration!

---

## 🔥 **What Happens When You Call**

1. You speak to your 11Labs agent: *"Show me all delayed shipments"*
2. 11Labs agent recognizes this needs the `search_shipments` function
3. 11Labs sends webhook POST to your public URL
4. Bridge server receives it and translates to MCP format
5. Logistics MCP server queries the database
6. Results flow back through the bridge
7. 11Labs agent reads the results back to you in natural language

**It's a full voice-to-database pipeline!** 🎤 → 🌐 → 💾 → 🔊

---

## ⚡ **Ready to Test!**

1. Run one of the tunnel commands above
2. Copy your public URL
3. Add `/webhook` to the end
4. Paste into 11Labs dashboard
5. Call your agent and ask about shipments!

**Let me know which tunnel method you want to use and I'll help you set it up!**
