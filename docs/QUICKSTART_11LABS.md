# 11Labs Voice Agent Integration - Quick Start Guide

## 🚀 What You Now Have

A complete **voice AI integration bridge** that connects your 11Labs voice agent to the Logistics MCP Orchestrator.

### Architecture
```
11Labs Voice Agent → Bridge (Port 8001) → Logistics API (Port 8000) → Database
```

## ✅ What's Been Created

1. **`elevenlabs_bridge.py`** - Main integration server
   - Natural language processing
   - Intent parsing
   - Voice-friendly response formatting
   - Webhook endpoint for 11Labs
   - Health checks

2. **`test_elevenlabs_integration.py`** - Comprehensive test suite
   - 8 automated voice query tests
   - 4 realistic conversation simulations
   - Health checks

## 🧪 Testing Locally (RIGHT NOW)

### Step 1: Start the Logistics API
```bash
# Terminal 1
python server.py
# Should see: "Uvicorn running on http://0.0.0.0:8000"
```

### Step 2: Start the Integration Bridge
```bash
# Terminal 2
python elevenlabs_bridge.py
# Should see: "Bridge running on: http://0.0.0.0:8001"
```

### Step 3: Run Tests
```bash
# Terminal 3
python test_elevenlabs_integration.py
```

This will simulate 12 voice interactions including:
- "Where is shipment JOB-2025-001?"
- "Show me all high risk shipments"
- "What shipments are delayed?"
- Multi-turn conversations

## 🌐 Testing with Real 11Labs Agent

### Step 1: Install ngrok (if not already)
```bash
brew install ngrok
# OR download from: https://ngrok.com/download
```

### Step 2: Authenticate ngrok (one-time)
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
# Get token from: https://dashboard.ngrok.com/get-started/your-authtoken
```

### Step 3: Start ngrok tunnel
```bash
# Terminal 3 (with bridge running on port 8001)
ngrok http 8001
```

You'll see:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8001
```

**Copy that HTTPS URL!**

### Step 4: Configure 11Labs Agent

1. Go to: https://elevenlabs.io/app/conversational-ai
2. Create or edit your agent
3. Go to **Settings** → **Webhooks** or **Functions**
4. Add webhook URL: `https://abc123.ngrok-free.app/webhook`

### Step 5: Define Functions (if using function calling)

In 11Labs dashboard, add these functions:

#### Function 1: Track Shipment
```json
{
  "name": "track_shipment",
  "description": "Track a specific shipment by ID or container number",
  "parameters": {
    "type": "object",
    "properties": {
      "identifier": {
        "type": "string",
        "description": "Shipment ID (JOB-2025-001) or container number"
      }
    },
    "required": ["identifier"]
  }
}
```

#### Function 2: Search High Risk
```json
{
  "name": "search_high_risk",
  "description": "Find all high risk or critical shipments",
  "parameters": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "description": "Maximum number of results",
        "default": 5
      }
    }
  }
}
```

#### Function 3: Search Delayed
```json
{
  "name": "search_delayed",
  "description": "Find all delayed shipments",
  "parameters": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "description": "Maximum number of results",
        "default": 10
      }
    }
  }
}
```

## 🗣️ Example Voice Conversations

### Conversation 1: Simple Tracking
```
You: "Hi, where is my shipment JOB-2025-001?"

Agent: "I found shipment JOB-2025-001. It's currently at 
Hong Kong Container Terminal on the MSC GULSUN. The status 
is in transit. Expected arrival is December 15th."
```

### Conversation 2: Risk Management
```
You: "Show me all high risk shipments"

Agent: "I found 4 shipments. Shipment 1: JOB-2025-002, delayed, 
currently at Hong Kong. Shipment 2: JOB-2025-004, delivered, 
at Sydney. Shipment 3: JOB-2025-006, delayed, at Singapore. 
And 1 more shipment. Would you like more details on any 
specific shipment?"
```

### Conversation 3: Natural Language
```
You: "Are there any shipments delayed right now?"

Agent: "I found 2 shipments. Shipment 1: JOB-2025-002, delayed, 
currently at Hong Kong Container Terminal. Shipment 2: 
JOB-2025-006, delayed, at PSA Singapore Terminal. Would you 
like more details on any specific shipment?"
```

## 🔍 How It Works

### Natural Language Processing
The bridge automatically:
- Extracts shipment IDs (JOB-2025-001)
- Extracts container numbers (MSCU1234567)
- Identifies intent (track, search, update)
- Maps to correct API calls

### Intent Recognition
```
"Where is..." → track_shipment
"Show me high risk..." → search with risk_flag=True
"What's delayed..." → search with status=DELAYED
"Track container..." → track_shipment with container ID
```

### Voice-Friendly Responses
API data is transformed into natural speech:
- "IN_TRANSIT" → "in transit"
- Dates formatted: "2025-12-15" → "December 15th"
- Multiple results summarized
- Technical details simplified

## 📊 Monitoring

### View Bridge Logs
```bash
# Terminal 2 shows all webhook calls
2025-01-08 10:30:15 - Webhook received: {"query": "where is JOB-2025-001"}
2025-01-08 10:30:15 - Parsed intent: track_shipment with params: {...}
```

### Health Check
```bash
curl http://localhost:8001/health
```

### Test Individual Query
```bash
curl -X POST http://localhost:8001/test \
  -H "Content-Type: application/json" \
  -d '{"query": "where is shipment JOB-2025-001"}'
```

## 🐛 Troubleshooting

### Bridge not responding
```bash
# Check if running
lsof -i :8001

# Restart
pkill -f elevenlabs_bridge
python elevenlabs_bridge.py
```

### 11Labs can't reach webhook
1. Check ngrok is running: `curl https://your-ngrok-url.ngrok.io/health`
2. Check ngrok dashboard: https://dashboard.ngrok.com/observability/http-requests
3. Verify webhook URL in 11Labs has `/webhook` at the end

### "Couldn't find shipment"
- Check shipment exists: `curl http://localhost:8000/messages -H "Authorization: Bearer dev-api-key-12345" -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_shipments","arguments":{"limit":10}},"id":1}'`
- Verify shipment ID format: JOB-2025-001 (uppercase)

## 🎯 What the Voice Agent Can Do

✅ **Track specific shipments**
   - "Where is JOB-2025-001?"
   - "Track container MSCU1234567"

✅ **Find problem shipments**
   - "Show me high risk shipments"
   - "What's delayed?"
   - "Any urgent shipments?"

✅ **Status updates**
   - "Which shipments are in transit?"
   - "What's arriving soon?"
   - "Give me a status update"

✅ **Natural language queries**
   - "Do we have shipments from Shanghai?"
   - "Anything arriving this week?"
   - "Check on my delivery"

## 📈 Next Steps

### 1. Production Deployment
- Deploy to AWS/Azure/GCP
- Use proper domain instead of ngrok
- Add SSL certificate
- Enable authentication

### 2. Enhanced NLP
- Add more intent patterns
- Support date parsing ("next week", "tomorrow")
- Multi-language support
- Contextual conversations

### 3. Advanced Features
- Proactive notifications
- Multi-turn context memory
- User authentication
- Custom business logic

### 4. 11Labs Configuration
- Set agent personality/voice
- Configure conversation flow
- Add fallback responses
- Set up escalation rules

## 📞 Support

If you have issues:
1. Check logs in both terminals
2. Run health check: `curl http://localhost:8001/health`
3. Test locally first: `python test_elevenlabs_integration.py`
4. Verify ngrok URL is accessible publicly

## 🎉 You're Ready!

Your logistics voice AI is now live and ready to handle customer calls, logistics manager briefings, and real-time shipment inquiries through natural voice conversations!
