# Logistics MCP Orchestrator Server

**Universal Translator for AI Agents and Logistics Systems**

A production-grade MCP (Model Context Protocol) server that acts as a middleware layer between AI agents and complex logistics systems (Logitude, DP World, Tracking APIs). Exposes standardized tools via **SSE (Server-Sent Events)** for remote agent connectivity.

---

## 🎯 Features

- **Universal Data Format**: Normalizes messy logistics API responses into a consistent JSON structure
- **Dual-Write Pattern**: Updates both local cache and external APIs with automatic retry logic
- **SSE Transport**: Enables remote AI agents to connect from different servers
- **Risk Management**: Custom risk flags and agent notes not available in external systems
- **Audit Logging**: Complete audit trail of all agent actions with reasoning
- **Mock Adapters**: Placeholder implementations for Logitude, DP World, and Tracking APIs

---

## 🏗️ Architecture

```
┌─────────────────┐
│   AI Agents     │  (Remote servers connect via SSE)
│  (Remote/MCP)   │
└────────┬────────┘
         │ SSE (Port 8000)
         │
┌────────▼────────────────────────────────┐
│   Logistics MCP Orchestrator Server     │
│  ┌─────────────────────────────────┐   │
│  │      MCP Tools Layer            │   │
│  │  • track_shipment               │   │
│  │  • update_shipment_eta          │   │
│  │  • set_risk_flag                │   │
│  │  • add_agent_note               │   │
│  │  • search_shipments             │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │     Adapter Layer               │   │
│  │  • LogitudeAdapter              │   │
│  │  • DPWorldAdapter               │   │
│  │  • TrackingAPIAdapter           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │    Database Layer (SQLite)      │   │
│  │  • Shipments (with risk flags)  │   │
│  │  • Audit Logs                   │   │
│  └─────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │
    ┌──────▼────────┐
    │ External APIs  │
    │ (Mock/Real)    │
    └────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- pip or uv

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/testing/Documents/cw-ai-server
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize and seed database:**
   ```bash
   python seed_database.py
   ```

---

## 🚀 Usage

### Start the Server

```bash
python server.py
```

The server will start on `http://localhost:8000`

### Test the Server

Run the test suite to verify everything works:

```bash
python test_client.py
```

### Access the API

- **Health Check**: `GET http://localhost:8000/health`
- **Server Info**: `GET http://localhost:8000/info`
- **SSE Endpoint**: `GET http://localhost:8000/sse` (for MCP agents)
- **Messages**: `POST http://localhost:8000/messages` (alternative to SSE)

---

## 🔧 MCP Tools

### 1. track_shipment

Fetch comprehensive shipment data from local cache or external APIs.

**Arguments:**
- `identifier` (string, required): Shipment ID, container number, or master bill
- `source` (string, optional): Data source - `local`, `logitude`, `dpworld`, `tracking` (default: `local`)

**Example:**
```json
{
  "name": "track_shipment",
  "arguments": {
    "identifier": "JOB-2025-001",
    "source": "local"
  }
}
```

### 2. update_shipment_eta

Update ETA with dual-write pattern (local + external API).

**Arguments:**
- `shipment_id` (string, required): Shipment ID
- `new_eta` (string, required): New ETA in ISO 8601 format
- `reason` (string, required): Explanation for the change

**Example:**
```json
{
  "name": "update_shipment_eta",
  "arguments": {
    "shipment_id": "JOB-2025-002",
    "new_eta": "2025-12-28T16:00:00",
    "reason": "Weather delay extended by 48 hours"
  }
}
```

### 3. set_risk_flag

Flag shipments as high-risk or remove risk flag.

**Arguments:**
- `shipment_id` (string, required): Shipment ID
- `is_risk` (boolean, required): True to flag, False to clear
- `reason` (string, required): Why this is risky

**Example:**
```json
{
  "name": "set_risk_flag",
  "arguments": {
    "shipment_id": "JOB-2025-006",
    "is_risk": true,
    "reason": "Customer escalation - requires immediate attention"
  }
}
```

### 4. add_agent_note

Add observations and notes to shipments.

**Arguments:**
- `shipment_id` (string, required): Shipment ID
- `note` (string, required): Note text
- `append` (boolean, optional): Append or replace (default: true)

**Example:**
```json
{
  "name": "add_agent_note",
  "arguments": {
    "shipment_id": "JOB-2025-003",
    "note": "Customer called asking about delivery schedule",
    "append": true
  }
}
```

### 5. search_shipments

Search shipments with flexible filters.

**Arguments:**
- `container_no` (string, optional): Filter by container
- `master_bill` (string, optional): Filter by MBL
- `status_code` (string, optional): Filter by status
- `risk_flag` (boolean, optional): Filter by risk flag
- `limit` (integer, optional): Max results (default: 50)

**Example:**
```json
{
  "name": "search_shipments",
  "arguments": {
    "risk_flag": true,
    "limit": 10
  }
}
```

---

## 📊 Standard Data Format

All tools return data in this standardized format:

```json
{
  "id": "JOB-2025-001",
  "tracking": {
    "container": "MSCU1234567",
    "vessel": "MSC GULSUN",
    "voyage": "025W",
    "location": {
      "lat": 22.3193,
      "lng": 114.1694,
      "name": "South China Sea"
    }
  },
  "schedule": {
    "etd": "2025-12-10T08:00:00",
    "eta": "2025-12-25T14:30:00"
  },
  "status": {
    "code": "IN_TRANSIT",
    "description": "Container loaded on vessel, departed from Port of Shanghai"
  },
  "flags": {
    "is_risk": false,
    "agent_notes": null
  },
  "metadata": {
    "master_bill": "MAEU123456789",
    "created_at": "2025-12-09T10:00:00",
    "updated_at": "2025-12-15T12:30:00"
  }
}
```

---

## 🗄️ Database Schema

### Shipments Table
- `id` (Primary Key): Shipment reference ID
- `master_bill`: MBL / AWB number
- `container_no`: Container number
- `vessel_name`: Vessel name
- `status_code`: Standardized status code
- `eta`: Estimated time of arrival
- `risk_flag`: Custom risk flag (Boolean)
- `agent_notes`: Agent observations (Text)

### Audit Logs Table
- `id` (Auto-increment)
- `shipment_id` (Foreign Key)
- `action`: Action type (e.g., UPDATE_ETA)
- `reason`: AI's reasoning
- `field_name`: What changed
- `old_value` / `new_value`: Change tracking
- `timestamp`: When it happened

---

## 🔐 Authentication

The server uses Bearer token authentication. Set your API key in `.env`:

```env
API_KEY=your-secret-api-key-here
```

Include in requests:
```
Authorization: Bearer your-secret-api-key-here
```

---

## 🛠️ Configuration

Edit `.env` to configure:

- **Server**: `SERVER_HOST`, `SERVER_PORT`
- **Authentication**: `API_KEY`
- **Database**: `DATABASE_URL`
- **External APIs**: `LOGITUDE_API_URL`, `DPWORLD_API_URL`, etc.
- **Retry Logic**: `MAX_RETRIES`, `RETRY_DELAY`

---

## 📝 Development

### Adding New External APIs

1. Create new adapter in `adapters/`:
   ```python
   from adapters.base_adapter import BaseLogisticsAdapter
   
   class NewAPIAdapter(BaseLogisticsAdapter):
       async def normalize_response(self, raw_data):
           # Convert to standard format
           pass
       
       async def fetch_shipment(self, identifier):
           # Fetch from API
           pass
   ```

2. Register in `adapters/__init__.py`

3. Use in tools as needed

### Adding New Tools

1. Add tool definition in `tools.py`:
   ```python
   Tool(
       name="new_tool",
       description="What it does",
       inputSchema={...}
   )
   ```

2. Implement handler method:
   ```python
   async def new_tool(self, **kwargs):
       # Implementation
       pass
   ```

---

## 🧪 Testing

```bash
# Run test client
python test_client.py

# Run with custom URL
python -c "
from test_client import MCPTestClient, run_all_tests
import asyncio
asyncio.run(run_all_tests())
"
```

---

## 📦 Production Deployment

1. **Replace mock adapters** with real API implementations
2. **Use PostgreSQL** instead of SQLite (update `DATABASE_URL`)
3. **Set strong API keys** in environment
4. **Enable HTTPS** (use reverse proxy like nginx)
5. **Configure CORS** appropriately
6. **Set up monitoring** and logging
7. **Use process manager** (systemd, supervisor, docker)

---

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm logistics.db
python seed_database.py
```

### Port Already in Use
```bash
# Change port in .env
SERVER_PORT=8001
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

---

## 📞 Support

For issues and questions:
- GitHub Issues: [Project Repository]
- Documentation: This README
- Test Client: `python test_client.py`

---

**Built with ❤️ for Logistics AI Agents**
