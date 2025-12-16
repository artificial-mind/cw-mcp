# 🔌 Connection Types Quick Reference

## Two Ways to Connect

### 🎤 11Labs Voice Agent → HTTP Webhook
```
Connection: HTTP POST
Endpoint:   /webhook
Protocol:   Simple JSON
Response:   Plain text string
Streaming:  No
Use case:   Voice assistants
```

### 🤖 MCP Clients (Claude, GPT) → SSE Stream
```
Connection: Server-Sent Events (SSE)
Endpoint:   /sse
Protocol:   JSON-RPC 2.0
Response:   JSON objects
Streaming:  Yes (real-time)
Use case:   AI agent integration
```

---

## 🎤 11Labs Configuration

**Webhook URL:**
```
https://your-server.onrender.com/webhook
```

**Request Example:**
```json
{
  "function": "search_shipments",
  "arguments": {"risk_flag": true}
}
```

**Response Example:**
```
"I found 4 shipments. Shipment 1: JOB-2025-002, delayed at Suez Canal..."
```

**System Prompt:**
See `docs/ELEVENLABS_COMPLETE_GUIDE.md` for the complete prompt.

---

## 🤖 MCP Client Configuration

**SSE URL:**
```
https://your-server.onrender.com/sse
```

**Request Example (via /messages):**
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "track_shipment",
    "arguments": {"identifier": "JOB-2025-002"}
  },
  "id": 1
}
```

**Response Example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "id": "JOB-2025-002",
      "tracking": { ... },
      "status": { ... }
    }
  }
}
```

---

## 🎯 Quick Decision

**Choose HTTP Webhook if:**
- ✅ Building voice assistant (11Labs, Twilio, etc.)
- ✅ Need simple request/response
- ✅ Want plain text responses
- ✅ Single query per request

**Choose SSE if:**
- ✅ Integrating with Claude/GPT
- ✅ Need real-time updates
- ✅ Want persistent connection
- ✅ Following MCP standard

---

## 📊 Comparison Table

| Feature | HTTP Webhook | SSE Stream |
|---------|-------------|------------|
| **Endpoint** | `/webhook` | `/sse` |
| **Method** | POST | GET |
| **Connection** | One-shot | Persistent |
| **Request** | `{function, arguments}` | JSON-RPC 2.0 |
| **Response** | Plain string | JSON object |
| **Format** | Voice-ready text | Structured data |
| **Streaming** | ❌ No | ✅ Yes |
| **Protocol** | Simple JSON | MCP Standard |
| **Best for** | Voice UIs | AI Agents |
| **Example** | 11Labs | Claude Desktop |

---

## 🧪 Test Both

### Test HTTP Webhook (11Labs):
```bash
curl -X POST https://your-server.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"function": "search_shipments", "arguments": {"risk_flag": true}}'
```
Expected: Plain text response

### Test SSE Stream (MCP):
```bash
curl -N https://your-server.com/sse
```
Expected: Stream of SSE events with JSON payloads

### Test JSON-RPC (MCP):
```bash
curl -X POST https://your-server.com/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "track_shipment",
      "arguments": {"identifier": "JOB-2025-002"}
    },
    "id": 1
  }'
```
Expected: JSON-RPC response with structured data

---

## 🎯 Summary

**Your server supports BOTH connection types:**

1. **HTTP Webhook** (`/webhook`) for voice assistants
   - Simple, fast, voice-ready
   - Perfect for 11Labs integration

2. **SSE Stream** (`/sse`) for MCP clients
   - Standards-compliant, real-time
   - Perfect for Claude, GPT integration

**Choose based on your client!** 🚀
