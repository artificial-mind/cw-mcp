# Logistics MCP Orchestrator Server

> Production-grade logistics tracking system with Model Context Protocol (MCP) and 11Labs voice integration

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124+-green.svg)](https://fastapi.tiangolo.com)
[![MCP](https://img.shields.io/badge/MCP-1.0-orange.svg)](https://modelcontextprotocol.io)

## 🎯 Overview

A universal translator between AI agents and logistics systems. Provides real-time shipment tracking, vessel monitoring, and risk management through:
- **MCP Protocol** - Standard JSON-RPC 2.0 interface for AI agents
- **11Labs Voice** - Natural voice conversation interface
- **REST API** - Traditional HTTP endpoints
- **SSE** - Server-Sent Events for real-time updates

## ✨ Features

- 🚢 **Real-time Shipment Tracking** - Container, vessel, and cargo tracking
- 🎤 **Voice AI Integration** - Natural language queries via 11Labs
- ⚠️ **Risk Management** - Automated delay detection and flagging
- 📊 **Analytics** - Operational metrics and reporting
- 🔄 **Real-time Updates** - SSE streaming for live data
- 🔌 **MCP Standard** - Compatible with Claude, GPT, and other AI agents

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- SQLite (included)
- (Optional) 11Labs API key for voice

### Installation

```bash
# Clone repository
git clone <your-repo-url>
cd cw-ai-server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python src/seed_database.py

# Run server (entry point)
python src/server.py
```

Server runs on: `http://localhost:8000`
MCP SSE endpoint: `http://localhost:8000/sse`

### Test It

```bash
# Health check
curl http://localhost:8000/health

# Search high-risk shipments
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"function": "search_shipments", "arguments": {"risk_flag": true}}'
```

## 📁 Project Structure

```
cw-ai-server/
├── src/                          # Source code
│   ├── server.py                 # Main FastAPI application
│   ├── tools.py                  # MCP tools implementation
│   ├── config.py                 # Configuration
│   ├── auth.py                   # Authentication
│   ├── utils.py                  # Utilities
│   ├── seed_database.py          # Database seeding
│   ├── database/                 # Database layer
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── database.py           # DB connection
│   │   └── crud.py               # Database operations
│   └── adapters/                 # External API adapters
│       ├── base_adapter.py       # Base adapter class
│       ├── logitude_adapter.py   # Logitude API
│       ├── dpworld_adapter.py    # DP World API
│       └── tracking_adapter.py   # Aggregator
│
├── tests/                        # Test suite
│   ├── test_comprehensive.py    # Full integration tests
│   ├── test_sse.py              # SSE streaming tests
│   ├── test_client.py           # Client tests
│   ├── demo_realtime_operations.py
│   └── demo_interactive_queries.py
│
├── docs/                         # Documentation
│   ├── DEPLOYMENT.md            # Deployment guide
│   ├── QUICKSTART.md            # Quick start guide
│   ├── QUICKSTART_11LABS.md     # 11Labs setup
│   ├── ELEVENLABS_AGENT_PROMPT.md    # Voice agent prompt
│   ├── ELEVENLABS_AGENT_SETUP.md     # Agent configuration
│   └── README.md                # Architecture docs
│
├── logistics-voice-ui/           # React voice interface
│   ├── src/                     # UI source
│   └── package.json             # Dependencies
│
├── logistics.db                  # SQLite database
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

## 🔌 API Endpoints

### Primary Connection: SSE (Server-Sent Events)

**MCP Protocol via SSE** - The recommended way to connect
- Persistent connection with real-time updates
- JSON-RPC 2.0 protocol
- Used by Claude Desktop, AI agents, MCP clients
- **Endpoint:** `GET /sse`

### Additional Connection Types

**1. HTTP Webhooks (For 11Labs Voice)**
- Simple request → response
- Plain text responses (voice-ready)
- No streaming
- **Endpoint:** `POST /webhook`

**2. REST JSON-RPC (Alternative)**
- Standard HTTP POST
- JSON-RPC 2.0 protocol
- **Endpoint:** `POST /messages`

### REST Endpoints

| Endpoint | Method | Protocol | Description |
|----------|--------|----------|-------------|
| `/` | GET | HTTP | Server information |
| `/health` | GET | HTTP | Health check |
| `/sse` | GET | **SSE** | **Primary: Server-Sent Events stream (MCP)** |
| `/webhook` | POST | HTTP | 11Labs voice webhook (simple JSON) |
| `/messages` | POST | JSON-RPC | Alternative MCP endpoint |

### MCP Tools

| Tool | Description |
|------|-------------|
| `search_shipments` | Search with filters (risk, status, container) |
| `track_shipment` | Get detailed shipment information |
| `update_shipment_eta` | Update estimated arrival time |
| `set_risk_flag` | Flag shipment as high-risk |
| `add_agent_note` | Add operational notes |

## 🎤 11Labs Voice Integration

### Connection Type: HTTP POST Webhook
- **NOT** SSE or streaming
- Simple request/response cycle
- Plain text responses (already voice-optimized)

### Setup

1. **Deploy server** to Render/Railway/etc.
2. **Get webhook URL**: `https://your-app.com/webhook`
3. **Configure 11Labs** agent with 5 functions
4. **Add system prompt** from `docs/ELEVENLABS_COMPLETE_GUIDE.md`

### Test with Voice

Say to your agent:
- *"Show me all high-risk shipments"*
- *"Where is container COSU9876543?"*
- *"Track shipment JOB-2025-002"*
- *"What shipments are delayed?"*

**Complete guide:** `docs/ELEVENLABS_COMPLETE_GUIDE.md` (includes full system prompt)

## 🚢 Sample Data

The database includes 10 realistic shipments:

- **4 High-Risk** - Delayed, weather issues, customs holds
- **3 In Transit** - Normal operations
- **2 Delivered** - Completed
- **1 At Port** - Waiting for departure

**Vessels:** MSC GULSUN, COSCO SHIPPING UNIVERSE, MAERSK ESSEX, etc.

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python tests/test_comprehensive.py

# Test webhook
python tests/demo_realtime_operations.py

# Test voice integration
python tests/test_elevenlabs_integration.py
```

## 🌐 Deployment

### Render.com (Recommended)

```bash
# 1. Push to GitHub
git push origin main

# 2. Create new Web Service on Render
# 3. Connect GitHub repo
# 4. Configure:
#    - Build: pip install -r requirements.txt
#    - Start: python src/server.py
#    - Port: 8000

# 5. Set environment variables:
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false
```

**Detailed guide:** `docs/DEPLOYMENT.md`

### Other Platforms

- **Railway**: Same configuration as Render
- **Heroku**: Add `Procfile` with `web: python src/server.py`
- **DigitalOcean**: Use Docker (Dockerfile included)
- **AWS/GCP**: Use container services

## 🔐 Environment Variables

Create `.env` file:

```bash
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite:///logistics.db

# API Keys (optional)
LOGITUDE_API_KEY=your-key
DPWORLD_API_KEY=your-key
TRACKING_API_KEY=your-key

# Authentication
API_KEY=your-secure-key
```

## 📊 Architecture

```
┌─────────────┐
│  AI Agent   │  (Claude, GPT, Voice)
│  11Labs     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Logistics MCP Server (FastAPI)    │
│                                      │
│  ┌──────────┐  ┌─────────────────┐ │
│  │   MCP    │  │   REST/Webhook  │ │
│  │ Protocol │  │    Endpoints    │ │
│  └────┬─────┘  └────────┬────────┘ │
│       │                 │          │
│       ▼                 ▼          │
│  ┌──────────────────────────────┐ │
│  │     Logistics Tools Layer    │ │
│  │  (search, track, analyze)    │ │
│  └──────────┬───────────────────┘ │
│             │                      │
│       ┌─────┴──────┐              │
│       ▼            ▼              │
│  ┌────────┐  ┌──────────┐        │
│  │SQLite  │  │ External │        │
│  │   DB   │  │   APIs   │        │
│  └────────┘  └──────────┘        │
└─────────────────────────────────────┘
```

## 🛠️ Development

### Code Style

```bash
# Format code
black src/

# Lint
flake8 src/

# Type check
mypy src/
```

### Add New Tool

1. Define in `src/tools.py`
2. Register with MCP server
3. Add to `/webhook` endpoint mapping
4. Update documentation

### Database Changes

```bash
# Modify models in src/database/models.py
# Then recreate database:
rm logistics.db
python src/seed_database.py
```

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[11Labs Setup](docs/QUICKSTART_11LABS.md)** - Voice agent configuration
- **[Agent Prompt](docs/ELEVENLABS_AGENT_PROMPT.md)** - System prompt for voice AI
- **[Architecture](docs/README.md)** - Detailed architecture docs
- **[API Reference](docs/QUICKSTART.md)** - API documentation

## 🤝 Contributing

1. Fork repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) - MCP specification
- [FastAPI](https://fastapi.tiangolo.com) - Modern web framework
- [11Labs](https://elevenlabs.io) - Voice AI platform
- [SQLAlchemy](https://sqlalchemy.org) - Database ORM

## 📞 Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@yourdomain.com

---

**Built with ❤️ for modern logistics operations**

*Last updated: December 16, 2025*
