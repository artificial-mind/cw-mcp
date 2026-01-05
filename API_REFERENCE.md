# CW MCP Server - API Reference

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Protocol:** MCP (Model Context Protocol) over SSE (Server-Sent Events)

## Overview

The CW MCP Server provides access to 16 logistics tools via the Model Context Protocol. It uses FastMCP library for SSE-based communication and exposes tools for:
- Shipment tracking and search
- ETA updates and risk management
- Analytics and reporting
- Predictive delay detection
- Document generation (BOL, Invoice, Packing List)
- Real-time vessel tracking

---

## Connection

### SSE Endpoint

**`GET /sse`**  
Opens a Server-Sent Events connection for MCP protocol communication.

**Response:** SSE stream with endpoint information
```
event: endpoint
data: /messages/?session_id=<uuid>
```

### Message Endpoint

**`POST /messages/?session_id=<session_id>`**  
Send JSON-RPC messages to call tools

**Headers:**
```
Content-Type: application/json
```

---

## MCP Protocol

### Initialize

**Method:** `initialize`

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "client-name",
      "version": "1.0.0"
    }
  }
}
```

### List Tools

**Method:** `tools/list`

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "track_shipment",
        "description": "Track a single shipment by ID, container number, or bill of lading",
        "inputSchema": {...}
      },
      // ... 15 more tools
    ]
  }
}
```

### Call Tool

**Method:** `tools/call`

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "track_shipment",
    "arguments": {
      "identifier": "job-2025-001"
    }
  }
}
```

---

## Available Tools

### 1. Tracking Tools

#### `track_shipment`
**Description:** Track a single shipment by ID, container number, or bill of lading

**Arguments:**
```python
{
  "identifier": str  # Job ID, container number, or BOL
}
```

**Returns:**
```json
{
  "success": true,
  "shipment": {
    "id": "job-2025-001",
    "container_no": "MSCU1234567",
    "master_bill": "BOL123456",
    "vessel_name": "MAERSK ANTWERP",
    "status_code": "IN_TRANSIT",
    "origin_port": "Shanghai",
    "destination_port": "Los Angeles",
    "eta": "2026-02-05T00:00:00",
    "current_location": "Pacific Ocean",
    "risk_flag": false
  }
}
```

#### `search_shipments`
**Description:** Search shipments with flexible criteria

**Arguments:**
```python
{
  "query": Dict[str, Any],  # Search criteria
  "limit": int = 50  # Max results
}
```

**Query Examples:**
```json
{
  "query": {"status_code": "IN_TRANSIT"},
  "limit": 10
}
```

**Returns:**
```json
{
  "success": true,
  "count": 5,
  "shipments": [...]
}
```

#### `search_shipments_advanced`
**Description:** Advanced search with multiple filters

**Arguments:**
```python
{
  "status": Optional[str],
  "origin_port": Optional[str],
  "destination_port": Optional[str],
  "vessel_name": Optional[str],
  "risk_flag": Optional[bool],
  "limit": int = 50
}
```

#### `query_shipments_by_criteria`
**Description:** Query shipments with complex criteria including date ranges

**Arguments:**
```python
{
  "status": Optional[str],
  "port": Optional[str],
  "vessel": Optional[str],
  "risk_only": bool = False,
  "eta_from": Optional[str],  # ISO 8601 date
  "eta_to": Optional[str],
  "limit": int = 100
}
```

---

### 2. Update Tools

#### `update_shipment_eta`
**Description:** Update the ETA for a shipment

**Arguments:**
```python
{
  "shipment_id": str,
  "new_eta": str,  # ISO 8601 datetime
  "reason": Optional[str]
}
```

**Returns:**
```json
{
  "success": true,
  "shipment_id": "job-2025-001",
  "old_eta": "2026-02-05T00:00:00",
  "new_eta": "2026-02-07T00:00:00",
  "message": "ETA updated successfully"
}
```

#### `set_risk_flag`
**Description:** Flag a shipment as high-risk or remove the risk flag

**Arguments:**
```python
{
  "identifier": str,  # Job ID, container, or BOL
  "is_risk": bool,
  "reason": Optional[str]
}
```

**Returns:**
```json
{
  "success": true,
  "shipment_id": "job-2025-001",
  "risk_flag": true,
  "message": "Risk flag set successfully"
}
```

#### `add_agent_note`
**Description:** Add a note to a shipment

**Arguments:**
```python
{
  "shipment_id": str,
  "note": str,
  "note_type": str = "general"  # general, exception, update, etc.
}
```

---

### 3. Analytics Tools

#### `get_shipments_analytics`
**Description:** Get comprehensive shipment analytics

**Returns:**
```json
{
  "success": true,
  "total_shipments": 150,
  "by_status": {
    "IN_TRANSIT": 85,
    "DELIVERED": 45,
    "DELAYED": 20
  },
  "risk_summary": {
    "total_at_risk": 12,
    "risk_percentage": 8.0
  },
  "port_summary": {
    "Shanghai": 30,
    "Los Angeles": 25
  }
}
```

#### `get_delayed_shipments`
**Description:** Get shipments that are currently delayed

**Arguments:**
```python
{
  "days_delayed": int = 1  # Minimum days delayed
}
```

**Returns:**
```json
{
  "success": true,
  "count": 5,
  "delayed_shipments": [
    {
      "id": "job-2025-001",
      "days_delayed": 3,
      "original_eta": "2026-01-10",
      "current_eta": "2026-01-13"
    }
  ]
}
```

#### `get_shipments_by_route`
**Description:** Get shipments by origin and/or destination port

**Arguments:**
```python
{
  "origin_port": Optional[str],
  "destination_port": Optional[str],
  "limit": int = 100
}
```

---

### 4. Predictive AI Tools

#### `predictive_delay_detection`
**Description:** Use ML to predict if a shipment will be delayed

**Arguments:**
```python
{
  "identifier": str  # Job ID, container, or BOL
}
```

**Returns:**
```json
{
  "success": true,
  "shipment_id": "job-2025-001",
  "prediction": {
    "will_delay": false,
    "confidence": 0.78,
    "delay_probability": 0.22,
    "risk_factors": ["high_volume_route", "peak_season"],
    "recommendation": "Monitor closely - moderate risk",
    "model_accuracy": 0.85
  }
}
```

#### `real_time_vessel_tracking`
**Description:** Track vessel position in real-time using external APIs

**Arguments:**
```python
{
  "vessel_name": str
}
```

**Returns:**
```json
{
  "success": true,
  "vessel_name": "MAERSK ANTWERP",
  "tracking_data": {
    "position": {
      "lat": 35.123,
      "lon": -120.456
    },
    "speed": 18.5,
    "course": 270,
    "status": "Under way using engine",
    "last_update": "2026-01-05T12:00:00"
  }
}
```

---

### 5. Document Generation Tools

#### `generate_bill_of_lading`
**Description:** Generate Bill of Lading (BOL) PDF document

**Arguments:**
```python
{
  "shipment_id": str
}
```

**Returns:**
```json
{
  "success": true,
  "document_type": "BILL_OF_LADING",
  "document_number": "BOL-job-2025-001",
  "file_path": "/path/to/BOL_job-2025-001_20260105_123456.pdf",
  "document_url": "/documents/BOL_job-2025-001_20260105_123456.pdf",
  "file_size_kb": 2.54
}
```

#### `generate_commercial_invoice`
**Description:** Generate Commercial Invoice PDF for customs clearance

**Arguments:**
```python
{
  "shipment_id": str,
  "invoice_number": Optional[str]  # Auto-generated if not provided
}
```

**Returns:**
```json
{
  "success": true,
  "document_type": "COMMERCIAL_INVOICE",
  "invoice_number": "INV-2025-001",
  "file_path": "/path/to/INV_INV-2025-001_20260105_123456.pdf",
  "document_url": "/documents/INV_INV-2025-001_20260105_123456.pdf",
  "file_size_kb": 2.34,
  "total_amount": 12800.00,
  "currency": "USD"
}
```

#### `generate_packing_list`
**Description:** Generate Packing List PDF with cargo details

**Arguments:**
```python
{
  "shipment_id": str,
  "packing_list_number": Optional[str]  # Auto-generated if not provided
}
```

**Returns:**
```json
{
  "success": true,
  "document_type": "PACKING_LIST",
  "packing_list_number": "PKG-job-2025-001",
  "file_path": "/path/to/PKG_PKG-job-2025-001_20260105_123456.pdf",
  "document_url": "/documents/PKG_PKG-job-2025-001_20260105_123456.pdf",
  "file_size_kb": 2.16,
  "total_packages": 1,
  "total_weight_kg": 250.0
}
```

---

## Tool Categories

| Category | Tools | Count |
|----------|-------|-------|
| **Tracking** | `track_shipment`, `search_shipments`, `search_shipments_advanced`, `query_shipments_by_criteria` | 4 |
| **Updates** | `update_shipment_eta`, `set_risk_flag`, `add_agent_note` | 3 |
| **Analytics** | `get_shipments_analytics`, `get_delayed_shipments`, `get_shipments_by_route` | 3 |
| **AI/ML** | `predictive_delay_detection`, `real_time_vessel_tracking` | 2 |
| **Documents** | `generate_bill_of_lading`, `generate_commercial_invoice`, `generate_packing_list` | 3 |
| **Batch** | `batch_track_shipments` | 1 |
| **Total** | | **16** |

---

## Data Models

### Shipment Object
```python
{
  "id": str,  # Job ID (primary)
  "container_no": Optional[str],
  "master_bill": Optional[str],  # Bill of lading
  "vessel_name": Optional[str],
  "voyage_number": Optional[str],
  "origin_port": Optional[str],
  "destination_port": Optional[str],
  "status_code": str,  # IN_TRANSIT, DELIVERED, DELAYED, etc.
  "status_description": Optional[str],
  "etd": Optional[str],  # ISO 8601 datetime
  "eta": Optional[str],  # ISO 8601 datetime
  "current_location": Optional[str],
  "current_lat": Optional[str],
  "current_lng": Optional[str],
  "risk_flag": bool,
  "agent_notes": Optional[str],
  "created_at": str,
  "updated_at": str
}
```

### Error Response
```python
{
  "success": false,
  "error": str  # Error message
}
```

---

## Setup & Configuration

### Starting the Server

```bash
cd cw-ai-server
python src/server_fastmcp.py
```

Server runs on: `http://0.0.0.0:8000`

### Environment Variables

- `MCP_SERVER_HOST`: Server host (default: `0.0.0.0`)
- `MCP_SERVER_PORT`: Server port (default: `8000`)
- `DATABASE_URL`: SQLite database path (default: `sqlite+aiosqlite:///./shipments.db`)
- `ANALYTICS_ENGINE_URL`: Analytics engine URL (default: `http://localhost:8002`)

### Dependencies

- FastMCP
- SQLAlchemy (async)
- aiosqlite
- httpx
- pydantic

---

## Client Integration

### Python Client Example

```python
import aiohttp
import json

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool via SSE."""
    
    # Connect to SSE
    async with aiohttp.ClientSession() as session:
        # Get SSE endpoint
        async with session.get('http://localhost:8000/sse') as resp:
            async for line in resp.content:
                if line.startswith(b'data:'):
                    endpoint = line[5:].decode().strip()
                    break
        
        # Call tool
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        async with session.post(
            f'http://localhost:8000{endpoint}',
            json=message
        ) as resp:
            # Wait for SSE response with result
            async for line in resp.content:
                if line.startswith(b'data:'):
                    result = json.loads(line[5:])
                    return result

# Example usage
result = await call_mcp_tool("track_shipment", {"identifier": "job-2025-001"})
print(result)
```

### JavaScript Client Example

```javascript
// Connect to SSE
const eventSource = new EventSource('http://localhost:8000/sse');

eventSource.addEventListener('endpoint', async (event) => {
  const endpoint = event.data;
  
  // Call tool
  const response = await fetch(`http://localhost:8000${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: 'track_shipment',
        arguments: { identifier: 'job-2025-001' }
      }
    })
  });
  
  // Listen for result via SSE
  eventSource.addEventListener('message', (event) => {
    const result = JSON.parse(event.data);
    console.log(result);
  });
});
```

---

## Error Handling

### Common Error Codes

| Code | Message | Cause |
|------|---------|-------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Missing required params |
| -32601 | Method not found | Invalid tool name |
| -32602 | Invalid params | Wrong argument types |
| -32603 | Internal error | Server error |

### Tool-Specific Errors

```json
{
  "success": false,
  "error": "Shipment not found: job-2025-999"
}
```

---

## Performance & Limits

- **Max concurrent connections**: 100
- **Request timeout**: 30 seconds
- **Search result limit**: 100 (default: 50)
- **Database**: SQLite with async support
- **Connection**: Persistent SSE connections

---

## Testing

### Health Check

```bash
curl http://localhost:8000/
```

Expected: 404 (MCP uses SSE, not REST)

### List Tools

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["src/server_fastmcp.py"]
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")

asyncio.run(test())
```

---

## Notes

- All datetime fields use ISO 8601 format
- Database is auto-created on first run with sample data
- Tools call Analytics Engine for ML predictions and document generation
- SSE connection must be maintained for tool calls
- Session IDs are UUID format (with dashes)

---

## Version History

- **1.0.0** (2026-01-05): Initial release with 16 tools including document generation

