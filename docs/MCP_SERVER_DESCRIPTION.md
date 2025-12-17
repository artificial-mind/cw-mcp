# Logistics MCP Server - Technical Description

## 🎯 Executive Summary

A production-grade **Model Context Protocol (MCP)** server that acts as a universal translator between AI agents and logistics systems. Provides real-time shipment tracking, vessel monitoring, and risk management through standardized protocols (MCP, SSE) and voice interfaces (11Labs webhooks).

---

## 📋 What is This Server?

**Name:** Logistics MCP Orchestrator Server

**Purpose:** Enable AI agents (voice assistants, chatbots, automation tools) to access and manage logistics data through natural language.

**Technology Stack:**
- **Framework:** FastAPI (Python 3.11+)
- **Protocol:** Model Context Protocol (MCP) + Custom webhooks
- **Database:** SQLite (production: PostgreSQL/MySQL compatible)
- **Integrations:** 11Labs Voice, external logistics APIs (Logitude, DP World)
- **Transport:** SSE (Server-Sent Events) + REST API

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  AI Agent Layer                          │
│  (11Labs Voice, Claude, GPT, Custom Agents)             │
└──────────────┬─────────────────────┬────────────────────┘
               │                     │
      HTTP POST /webhook      SSE /sse (MCP)
               │                     │
               ▼                     ▼
┌─────────────────────────────────────────────────────────┐
│           Logistics MCP Orchestrator Server              │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Webhook Handler    |    MCP Protocol Handler    │  │
│  │  (Voice AI)         |    (AI Agents)             │  │
│  └────────────┬───────────────────┬─────────────────┘  │
│               │                   │                      │
│               ▼                   ▼                      │
│  ┌────────────────────────────────────────────────┐    │
│  │         5 MCP Tools (Business Logic)           │    │
│  │  • search_shipments    • track_shipment        │    │
│  │  • update_eta          • set_risk_flag         │    │
│  │  • add_agent_note                              │    │
│  └────────────┬───────────────────────────────────┘    │
│               │                                          │
│               ▼                                          │
│  ┌──────────────────┐  ┌──────────────────────────┐   │
│  │  SQLite Database │  │  External API Adapters   │   │
│  │  (Shipments,     │  │  • Logitude API          │   │
│  │   Tracking Data) │  │  • DP World API          │   │
│  └──────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 Supported Protocols

### 1. **SSE (Server-Sent Events)** - PRIMARY for MCP Clients
- **Endpoint:** `/sse`
- **Protocol:** JSON-RPC 2.0 over SSE
- **Transport:** Server-Sent Events streaming
- **Use Case:** Claude Desktop, GPT integrations, MCP-compatible agents
- **Features:** Real-time updates, persistent connection, standardized tool calling
- **Status:** ✅ Primary and recommended connection method

### 2. **HTTP Webhooks** - For Voice Assistants
- **Endpoint:** `/webhook`
- **Protocol:** Simple JSON
- **Transport:** HTTP POST
- **Use Case:** 11Labs, Twilio, custom voice UIs
- **Features:** Fast response, voice-optimized text, simple integration

### 3. **REST API** - Alternative for Traditional Clients
- **Endpoint:** `/messages`
- **Protocol:** JSON-RPC 2.0 over HTTP
- **Transport:** HTTP POST
- **Use Case:** Custom clients, testing, direct integration

---

## 🛠️ Core Capabilities (5 MCP Tools)

### 1. **search_shipments**
Search and filter shipments by multiple criteria
- **Parameters:** risk_flag, status_code, container_no, master_bill, limit
- **Returns:** List of matching shipments with tracking data
- **Use Case:** "Show me all delayed shipments", "Find high-risk cargo"

### 2. **track_shipment** 
Get detailed information about specific shipment
- **Parameters:** identifier (job ID, container number, or bill of lading)
- **Returns:** Complete tracking data, location, vessel, schedule, risk flags
- **Use Case:** "Where is container COSU9876543?", "Track JOB-2025-002"

### 3. **update_shipment_eta**
Update estimated arrival time for shipments
- **Parameters:** identifier, new_eta, reason
- **Returns:** Confirmation and updated schedule
- **Use Case:** "Vessel delayed, update ETA to December 25th"

### 4. **set_risk_flag**
Flag shipments as high-risk with explanations
- **Parameters:** identifier, is_risk (boolean), reason
- **Returns:** Confirmation and risk status
- **Use Case:** "Customer very concerned, flag as high priority"

### 5. **add_agent_note**
Add operational notes to shipments
- **Parameters:** identifier, note, agent_name
- **Returns:** Confirmation with updated notes
- **Use Case:** "Customer called, add note about delivery concerns"

---

## 📊 Data Model

### Shipment Object
```python
{
  "id": "JOB-2025-002",              # Job identifier
  "tracking": {
    "container": "COSU9876543",      # Container number
    "vessel": "COSCO SHIPPING UNIVERSE",
    "voyage": "012E",
    "location": {
      "name": "Suez Canal",
      "lat": 30.5234,
      "lng": 32.3426
    }
  },
  "schedule": {
    "etd": "2025-12-05T10:00:00",    # Estimated departure
    "eta": "2025-12-23T21:52:49"     # Estimated arrival
  },
  "status": {
    "code": "DELAYED",                # IN_TRANSIT, DELIVERED, DELAYED, CUSTOMS_HOLD
    "description": "Vessel delayed by 48 hours..."
  },
  "flags": {
    "is_risk": true,                  # High-risk flag
    "agent_notes": "Customer called, very concerned..."
  },
  "metadata": {
    "master_bill": "COSU987654321",
    "created_at": "2025-12-15T14:18:49",
    "updated_at": "2025-12-15T16:22:51"
  }
}
```

---

## 🚀 Key Features

### Real-Time Tracking
- Live vessel positions (GPS coordinates + location names)
- Container status updates
- Delay detection and notifications
- ETA calculations with weather/port conditions

### Risk Management
- Automatic delay flagging (>24 hours)
- Custom risk flags with reasons
- Agent notes for operational context
- Customer concern tracking

### Multi-Protocol Support
- **SSE streaming** for real-time MCP clients
- **HTTP webhooks** for voice assistants
- **REST API** for traditional integrations
- All protocols access same business logic

### Voice Optimization
- Responses formatted for natural speech
- Location names instead of coordinates
- Concise summaries for multiple results
- Automatic truncation of long text

### Data Aggregation
- Combines local database with external APIs
- Falls back to cached data if APIs unavailable
- Unified response format across sources
- Performance optimization with async queries

---

## 🔐 Security Features

- Bearer token authentication (configurable)
- CORS middleware for web clients
- Request validation and sanitization
- Rate limiting ready (middleware available)
- Environment-based configuration

---

## 📈 Performance Characteristics

- **Response Time:** <500ms for database queries
- **Concurrent Users:** 100+ (FastAPI async)
- **Database:** SQLite (dev), PostgreSQL/MySQL (production)
- **Scalability:** Horizontal scaling ready
- **Caching:** In-memory cache for external APIs
- **Monitoring:** Health check endpoint, structured logging

---

## 🌐 Deployment Options

### Cloud Platforms
- **Render.com** ✅ (Recommended, zero-config)
- **Railway.app** ✅ (One-click deploy)
- **Heroku** ✅ (With Procfile)
- **AWS/GCP/Azure** ✅ (Container/serverless)
- **DigitalOcean** ✅ (Droplet/App Platform)

### Requirements
- Python 3.11+
- 512MB RAM minimum (1GB recommended)
- 100MB disk space
- HTTPS endpoint (for 11Labs webhooks)

---

## 📚 Integration Examples

### 11Labs Voice Agent
```json
POST /webhook
{
  "function": "search_shipments",
  "arguments": {"risk_flag": true}
}

Response: "I found 4 high-risk shipments. Shipment 1: JOB-2025-002..."
```

### Claude Desktop (MCP)
```json
GET /sse
(Server-Sent Events stream with JSON-RPC messages)

Tool call: track_shipment(identifier="JOB-2025-002")
Response: Complete shipment object with tracking data
```

### Custom Client
```json
POST /messages
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

---

## 🎯 Use Cases

### Operations Teams
- Morning risk assessments
- Delay investigations
- Customer inquiry responses
- Performance analytics

### Customer Service
- Real-time tracking updates
- Proactive delay notifications
- Issue escalation
- ETA confirmations

### Management
- High-risk shipment reports
- Operational metrics
- Delay analysis
- Fleet utilization

### Automation
- Automated delay alerts
- Risk-based routing decisions
- Customer notification triggers
- Analytics dashboards

---

## 🔧 Technical Specifications

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.11+ |
| **Framework** | FastAPI 0.124+ |
| **Protocol** | MCP 1.0, JSON-RPC 2.0, REST |
| **Database** | SQLite (SQLAlchemy ORM) |
| **Transport** | SSE, HTTP, WebSocket-ready |
| **Auth** | Bearer token, API key |
| **CORS** | Configurable origins |
| **Logging** | Structured JSON logs |
| **Health Check** | `/health` endpoint |
| **Documentation** | OpenAPI/Swagger at `/docs` |

---

## 📦 Package Dependencies

```
fastapi>=0.124.0
uvicorn[standard]>=0.25.0
mcp>=1.0.0
sqlalchemy>=2.0.0
aiosqlite>=0.19.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

---

## 🔄 Data Flow Example

**Voice Query: "Show me high-risk shipments"**

1. **User speaks** → 11Labs captures audio
2. **11Labs transcribes** → "Show me high-risk shipments"
3. **11Labs AI interprets** → Function: `search_shipments`, Args: `{"risk_flag": true}`
4. **HTTP POST to `/webhook`** → Server receives function call
5. **Server queries database** → SELECT * WHERE risk_flag = true
6. **Server formats response** → "I found 4 shipments. Shipment 1: JOB-2025-002..."
7. **Returns plain text** → 11Labs receives voice-ready response
8. **11Labs synthesizes** → Speaks result to user

**Total latency:** ~1-2 seconds (including voice processing)

---

## 🎉 Why This Server?

✅ **Universal Protocol Support** - Works with any AI agent (MCP, webhooks, REST)
✅ **Voice Optimized** - Responses formatted for natural speech
✅ **Production Ready** - Authentication, logging, health checks, error handling
✅ **Easy to Deploy** - One-click deployment to major platforms
✅ **Extensible** - Add new tools, data sources, or protocols easily
✅ **Real Data** - Connects to actual logistics APIs (Logitude, DP World)
✅ **Developer Friendly** - Clean code, comprehensive docs, test suite

---

## 📖 Documentation

- **README.md** - Quick start and overview
- **docs/DEPLOYMENT.md** - Deployment instructions
- **docs/ELEVENLABS_COMPLETE_GUIDE.md** - Voice integration guide
- **docs/CONNECTION_TYPES.md** - Protocol comparison
- **docs/QUICKSTART.md** - API reference
- **src/server.py** - Source code with inline docs

---

## 🚀 Get Started

```bash
# Clone and setup
git clone <repo-url>
cd cw-ai-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
python src/seed_database.py

# Run server (entry point)
python src/server.py

# Server starts at http://localhost:8000
# MCP SSE endpoint: http://localhost:8000/sse
```

---

**Built for modern logistics operations. Powered by AI. Ready for production.** 🌟
