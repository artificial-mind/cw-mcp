# Quick Start Guide

## ✅ Installation Complete!

Your **Logistics MCP Orchestrator Server** is ready to use.

---

## 🚀 Quick Start

### 1. Start the Server

```bash
cd /Users/testing/Documents/cw-ai-server
source venv/bin/activate
python server.py
```

Server will be available at: **http://localhost:8000**

### 2. Test the Server

In a new terminal:

```bash
cd /Users/testing/Documents/cw-ai-server
source venv/bin/activate
python test_client.py
```

### 3. Access Endpoints

- **Health Check**: http://localhost:8000/health
- **Server Info**: http://localhost:8000/info
- **SSE (MCP)**: http://localhost:8000/sse
- **Documentation**: http://localhost:8000/docs (FastAPI auto-docs)

---

## 📊 Sample Data

Database has been seeded with **10 shipments**:
- ✅ 3 flagged as high-risk
- 📦 Various status codes: IN_TRANSIT, DELAYED, AT_PORT, DELIVERED, CUSTOMS_HOLD
- 📝 4 audit log entries showing agent actions

### Query Risk Shipments

```bash
curl http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_shipments",
      "arguments": {"risk_flag": true}
    },
    "id": 1
  }'
```

---

## 🔧 MCP Tools Available

1. **track_shipment** - Fetch shipment data
2. **update_shipment_eta** - Update ETA with dual-write
3. **set_risk_flag** - Flag shipments as risky
4. **add_agent_note** - Add observations
5. **search_shipments** - Search with filters

Full documentation in [README.md](README.md)

---

## 🗂️ Project Structure

```
cw-ai-server/
├── server.py              # Main FastAPI + MCP server
├── config.py              # Configuration settings
├── tools.py               # MCP tool implementations
├── auth.py                # Authentication middleware
├── utils.py               # Helper functions
├── seed_database.py       # Database seeder
├── test_client.py         # Test suite
├── requirements.txt       # Python dependencies
├── database/              
│   ├── models.py          # SQLAlchemy models
│   ├── database.py        # Database connection
│   └── crud.py            # CRUD operations
├── adapters/              
│   ├── base_adapter.py    # Base adapter class
│   ├── logitude_adapter.py
│   ├── dpworld_adapter.py
│   └── tracking_adapter.py
└── logistics.db           # SQLite database (created)
```

---

## 🐛 Troubleshooting

### Server won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Use different port
SERVER_PORT=8001 python server.py
```

### Database issues

```bash
# Reset database
rm logistics.db
python seed_database.py
```

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📚 Next Steps

1. **Connect AI Agents**: Point your MCP client to `http://localhost:8000/sse`
2. **Replace Mock APIs**: Update adapters with real API credentials in `.env`
3. **Add More Tools**: Extend `tools.py` with additional logistics operations
4. **Deploy**: See [README.md](README.md) for production deployment guide

---

## 🎉 You're Ready!

The Logistics MCP Orchestrator is now running and ready to serve AI agents!
