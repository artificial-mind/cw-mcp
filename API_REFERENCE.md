# CW MCP Server - API Reference

**Version:** 1.2.0  
**Base URL:** `http://localhost:8000`  
**Protocol:** MCP (Model Context Protocol) over SSE (Server-Sent Events)

## Overview

The CW MCP Server provides access to 22 logistics tools via the Model Context Protocol. It uses FastMCP library for SSE-based communication and exposes tools for:
- Shipment tracking and search (5 tools)
- ETA updates and risk management
- Analytics and reporting (7 tools)
- Predictive delay detection
- Document generation (3 tools)
- Real-time vessel and container tracking (3 tools)
- Customer notifications and communications (2 tools)
- Exception management and proactive warnings (2 tools)

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
| **Real-Time Tracking (Day 6)** | `track_vessel_realtime`, `track_multimodal_shipment`, `track_container_live` | 3 |
| **Customer Communication (Day 7)** | `send_status_update`, `generate_customer_portal_link` | 2 |
| **Exception Management (Day 7)** | `proactive_exception_notification` | 1 |
| **Batch** | `batch_track_shipments` | 1 |
| **Total** | | **22** |

---

## Day 6 - Real-Time Tracking Tools (Tools 12-14)

### `track_vessel_realtime`

**Description:** Track vessel in real-time using AIS data with comprehensive navigation details. Provides live GPS position, speed in knots, heading in degrees, vessel status, next port, and ETA.

**Input Schema:**
```json
{
  "vessel_name": "MAERSK",
  "imo_number": "1234567",
  "mmsi": "123456789"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "vessel_name": "MAERSK SEALAND",
    "imo": "9632179",
    "mmsi": "220532000",
    "position": {
      "lat": 37.776995,
      "lon": -122.420063
    },
    "speed": 12.64,
    "heading": 273.0,
    "status": "Underway using engine",
    "next_port": "Oakland",
    "eta": "2025-01-25T14:00:00Z"
  }
}
```

### `track_multimodal_shipment`

**Description:** Track shipment across multiple transport modes (ocean, rail, truck). Shows complete journey with all legs, progress percentage, current location, and handoff points between carriers.

**Input Schema:**
```json
{
  "shipment_id": "job-2025-001"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "shipment_id": "job-2025-001",
    "status": "in_transit",
    "progress_percentage": 16.7,
    "current_mode": "ocean",
    "journey": [
      {
        "leg_number": 1,
        "mode": "ocean",
        "from": "Shanghai Port",
        "to": "Los Angeles Port",
        "status": "in_transit",
        "eta": "2025-01-23T14:00:00Z"
      }
    ],
    "total_legs": 3
  }
}
```

### `track_container_live`

**Description:** Track container with live IoT sensor data. Provides real-time GPS location, temperature monitoring, humidity, shock detection, door events, battery level, and active alerts.

**Input Schema:**
```json
{
  "container_number": "MAEU1234567"
}
```

**Output:**
```json
{
  "success": true,
  "data": {
    "container_number": "MAEU1234567",
    "container_type": "40HC Reefer",
    "battery_level": 87,
    "gps": {
      "latitude": 37.776995,
      "longitude": -122.420063
    },
    "temperature": {
      "temperature_celsius": -15.8,
      "setpoint_celsius": -18.0,
      "deviation": 2.2
    },
    "alerts": [
      {
        "type": "temperature_deviation",
        "severity": "medium",
        "message": "Temperature deviation: 2.2°C from setpoint"
      }
    ],
    "alert_count": 1
  }
}
```

---

### 6. Customer Communication Tools (Day 7 - Tool 28)

#### `send_status_update`

**Description:** Send shipment status notification to customer via email or SMS. Supports multiple notification types (departed, in_transit, arrived, customs_cleared, delivered, delay_warning, exception_alert) and multi-language support.

**Input Schema:**
```json
{
  "shipment_id": "SHIP12345",
  "notification_type": "departed",
  "recipient_email": "customer@example.com",
  "recipient_phone": "+1234567890",
  "channel": "email",
  "language": "en"
}
```

**Arguments:**
- `shipment_id` (required): Shipment ID
- `notification_type` (required): Type of notification - one of:
  - `departed`: Shipment has left origin
  - `in_transit`: Update while shipment is moving
  - `arrived`: Shipment arrived at destination
  - `customs_cleared`: Cleared customs successfully
  - `delivered`: Final delivery completed
  - `delay_warning`: Potential delay detected
  - `exception_alert`: Issue requiring attention
- `recipient_email` (optional): Customer email address
- `recipient_phone` (optional): Customer phone number (format: +1234567890)
- `channel` (optional): Delivery channel - `email`, `sms`, or `both` (default: `email`)
- `language` (optional): Notification language - `en`, `ar`, or `zh` (default: `en`)

**Output:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "notification_id": "NOTIF-20260107-84f6596c",
    "shipment_id": "SHIP12345",
    "notification_type": "departed",
    "sent_at": "2026-01-07T06:16:32.638982Z",
    "channels": ["email"],
    "recipient_email": "customer@example.com",
    "recipient_phone": null,
    "language": "en",
    "message_preview": "Your shipment SHIP12345 has departed",
    "tracking_url": "https://track.cwlogistics.com/SHIP12345"
  }
}
```

**Example Usage:**
```python
# Send departure notification via email
result = await mcp.call_tool("send_status_update", {
    "shipment_id": "SHIP12345",
    "notification_type": "departed",
    "recipient_email": "customer@example.com",
    "language": "en"
})

# Send delay warning via SMS
result = await mcp.call_tool("send_status_update", {
    "shipment_id": "SHIP12345",
    "notification_type": "delay_warning",
    "recipient_phone": "+12345678901",
    "channel": "sms"
})

# Send notification via both email and SMS
result = await mcp.call_tool("send_status_update", {
    "shipment_id": "SHIP12345",
    "notification_type": "delivered",
    "recipient_email": "customer@example.com",
    "recipient_phone": "+12345678901",
    "channel": "both"
})
```

#### `generate_customer_portal_link` (Day 7 - Tool 29)

**Description:** Generate a secure public tracking link for customer portal access. Creates UUID4-based token with configurable expiration (default 30 days). Link allows customers to track shipments without authentication.

**Input Schema:**
```json
{
  "shipment_id": "SHIP12345",
  "expires_in_days": 30
}
```

**Arguments:**
- `shipment_id` (required): Shipment ID to generate tracking link for
- `expires_in_days` (optional): Link validity period in days (default: 30)

**Output:**
```json
{
  "success": true,
  "tracking_url": "https://track.cwlogistics.com/a3f8b2c1-4d5e-6f7g-8h9i-0j1k2l3m4n5o",
  "token": "a3f8b2c1-4d5e-6f7g-8h9i-0j1k2l3m4n5o",
  "shipment_id": "SHIP12345",
  "expires_at": "2026-02-06T12:00:00Z",
  "created_at": "2026-01-07T12:00:00Z"
}
```

**Features:**
- UUID4-based secure tokens (RFC 4122 compliant)
- Database persistence for validation
- Configurable expiration period
- No authentication required for access
- Revocable via database deletion

**Example Usage:**
```python
# Generate tracking link with default 30-day expiration
result = await mcp.call_tool("generate_customer_portal_link", {
    "shipment_id": "SHIP12345"
})

# Generate link with custom 7-day expiration
result = await mcp.call_tool("generate_customer_portal_link", {
    "shipment_id": "SHIP12345",
    "expires_in_days": 7
})
```

#### `proactive_exception_notification` (Day 7 - Tool 30)

**Description:** Proactively warn customers about potential delays based on ML predictions. Only sends notification if ML confidence exceeds 70% threshold. Includes risk factors and predicted delay hours.

**Input Schema:**
```json
{
  "shipment_id": "SHIP12345",
  "recipient_email": "customer@example.com",
  "recipient_phone": "+1234567890",
  "language": "en"
}
```

**Arguments:**
- `shipment_id` (required): Shipment ID to analyze
- `recipient_email` (optional): Customer email address
- `recipient_phone` (optional): Customer phone number
- `language` (optional): Notification language - `en`, `es`, or `zh` (default: `en`)

**Output (Warning Sent):**
```json
{
  "success": true,
  "warning_sent": true,
  "ml_confidence": 0.85,
  "risk_factors": [
    "Weather conditions",
    "Port congestion"
  ],
  "predicted_delay_hours": 24,
  "notification_id": "NOTIF-20260107-8fdb75c9",
  "message": "Proactive delay warning sent to customer"
}
```

**Output (No Warning Needed):**
```json
{
  "success": true,
  "warning_sent": false,
  "ml_confidence": 0.65,
  "reason": "Confidence 65.0% below threshold 70%",
  "message": "ML confidence below threshold, no notification sent"
}
```

**Logic:**
1. Runs ML prediction on shipment
2. Only sends notification if confidence > 70%
3. Includes risk factors and predicted delay hours
4. Automatically uses "delayed" notification type

**Example Usage:**
```python
# Proactive delay warning with email
result = await mcp.call_tool("proactive_exception_notification", {
    "shipment_id": "SHIP12345",
    "recipient_email": "customer@example.com",
    "language": "en"
})

# Check result
if result["warning_sent"]:
    print(f"Warning sent! Confidence: {result['ml_confidence']:.0%}")
    print(f"Risk factors: {', '.join(result['risk_factors'])}")
else:
    print(f"No warning needed. Confidence: {result['ml_confidence']:.0%}")
```

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

- **1.1.0** (2026-01-06): Added 3 real-time tracking tools (vessel, multimodal, container) - Day 6 Priority 1
- **1.0.0** (2026-01-05): Initial release with 16 tools including document generation

