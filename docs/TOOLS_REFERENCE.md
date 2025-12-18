# MCP Tools Reference Guide

Complete reference for all available tools in the Logistics MCP Orchestrator Server.

## 📋 Table of Contents

- [Basic Tools](#basic-tools)
- [Advanced Search Tools](#advanced-search-tools)
- [Analytics Tools](#analytics-tools)
- [System Tools](#system-tools)
- [Use Cases & Examples](#use-cases--examples)

---

## Basic Tools

### 1. `search_shipments`

Simple search with basic filters.

**Parameters:**
- `risk_flag` (bool, optional): Filter by risk status
- `status_code` (string, optional): Filter by status (e.g., 'IN_TRANSIT', 'DELIVERED')
- `container_no` (string, optional): Filter by container number
- `master_bill` (string, optional): Filter by bill of lading
- `limit` (int, default=10): Maximum results

**Example Query:**
> "Show me risky shipments"
> "Find shipments with status IN_TRANSIT"

**Response:**
```json
{
  "success": true,
  "count": 3,
  "results": [
    {
      "id": "job-2025-002",
      "container_no": "COSU9876543",
      "status": "DELAYED",
      "risk_flag": true,
      "origin": "Hong Kong",
      "destination": "Rotterdam, Netherlands",
      "eta": "2025-12-22T16:00:00"
    }
  ]
}
```

---

### 2. `track_shipment`

Get detailed tracking for a specific shipment.

**Parameters:**
- `identifier` (string, required): Job ID, container number, or bill of lading

**Example Query:**
> "Track container MSCU1234567"
> "What's the status of job-2025-001?"

**Response:**
```json
{
  "success": true,
  "shipment": {
    "id": "job-2025-001",
    "container_no": "MSCU1234567",
    "vessel": "MSC GULSUN",
    "voyage": "025W",
    "status": "IN_TRANSIT",
    "risk_flag": false,
    "eta": "2025-12-25T14:30:00",
    "notes": []
  }
}
```

---

### 3. `update_shipment_eta`

Update the estimated arrival time for a shipment.

**Parameters:**
- `identifier` (string, required): Shipment identifier
- `new_eta` (string, required): New ETA (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
- `reason` (string, optional): Reason for the change

**Example Query:**
> "Update ETA for MSCU1234567 to 2025-12-28 due to weather delay"

---

### 4. `set_risk_flag`

Flag or unflag a shipment as high-risk.

**Parameters:**
- `identifier` (string, required): Shipment identifier
- `is_risk` (bool, required): true to flag, false to clear
- `reason` (string, optional): Reason for the change

**Example Query:**
> "Flag container COSU9876543 as high risk due to customs issues"

---

### 5. `add_agent_note`

Add operational notes to a shipment.

**Parameters:**
- `identifier` (string, required): Shipment identifier
- `note` (string, required): Note text
- `agent_name` (string, optional): Name of the agent

**Example Query:**
> "Add note to job-2025-002: Customer called asking for update"

---

## Advanced Search Tools

### 6. `search_shipments_advanced`

**⭐ Most Flexible Search Tool** - Supports multiple simultaneous filters.

**Parameters:**
- `vessel_name` (string, optional): Filter by vessel (partial match)
- `voyage_number` (string, optional): Filter by voyage
- `origin_port` (string, optional): Origin port (partial match)
- `destination_port` (string, optional): Destination port (partial match)
- `status_codes` (list, optional): Multiple status codes
- `risk_flag` (bool, optional): Filter by risk
- `eta_from` (string, optional): Arriving after this date
- `eta_to` (string, optional): Arriving before this date
- `current_location` (string, optional): Current location (partial match)
- `limit` (int, default=20): Max results

**Example Queries:**
> "Find all shipments from Shanghai arriving in Los Angeles"
> "Show me delayed or in-transit shipments with ETA before December 25"
> "Get all shipments on vessel MSC GULSUN"

**Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "job-2025-001",
      "vessel_name": "MSC GULSUN",
      "voyage_number": "025W",
      "origin": "Shanghai, China",
      "destination": "Los Angeles, USA",
      "status": "IN_TRANSIT",
      "current_location": "South China Sea",
      "eta": "2025-12-25T14:30:00"
    }
  ]
}
```

---

### 7. `query_shipments_by_criteria`

**⭐ Flexible Text Search** - Search across all fields with custom sorting.

**Parameters:**
- `search_text` (string, optional): Search across container, bill, vessel, ports, location
- `include_fields` (list, optional): Specific fields to return
- `sort_by` (string, default="eta"): Sort field (eta, etd, status_code, risk_flag, id)
- `sort_order` (string, default="asc"): Sort order (asc/desc)
- `limit` (int, default=10): Max results

**Example Queries:**
> "Search for anything related to Rotterdam"
> "Find shipments with Los Angeles sorted by ETA descending"
> "Search for MSC vessels showing only container number and ETA"

**Response:**
```json
{
  "success": true,
  "count": 1,
  "query": {
    "search_text": "Rotterdam",
    "sort_by": "eta",
    "sort_order": "asc"
  },
  "results": [
    {
      "id": "job-2025-002",
      "container_no": "COSU9876543",
      "destination_port": "Rotterdam, Netherlands",
      "eta": "2025-12-22T16:00:00"
    }
  ]
}
```

---

## Analytics Tools

### 8. `get_shipments_analytics`

**⭐ Comprehensive Statistics** - Get overview of all shipments.

**Parameters:** None

**Example Query:**
> "Give me an overview of all shipments"
> "Show me shipment statistics"

**Response:**
```json
{
  "success": true,
  "summary": {
    "total_shipments": 10,
    "risk_flagged": 3,
    "status_breakdown": {
      "IN_TRANSIT": 5,
      "DELAYED": 2,
      "DELIVERED": 1,
      "AT_PORT": 1,
      "CUSTOMS_HOLD": 1
    },
    "active_vessels_count": 7
  },
  "details": {
    "top_origin_ports": [
      {"port": "Shanghai, China", "count": 2},
      {"port": "Hong Kong", "count": 1}
    ],
    "top_destination_ports": [
      {"port": "Los Angeles, USA", "count": 2}
    ],
    "active_vessels": ["MSC GULSUN", "COSCO SHIPPING UNIVERSE"],
    "upcoming_arrivals": {
      "count": 3,
      "shipments": [...]
    }
  }
}
```

---

### 9. `get_delayed_shipments`

Find shipments that are past their ETA.

**Parameters:**
- `days_delayed` (int, default=1): Minimum days past ETA

**Example Query:**
> "Show me all delayed shipments"
> "Find shipments delayed by more than 2 days"

**Response:**
```json
{
  "success": true,
  "count": 2,
  "criteria": "Delayed by 1+ days",
  "results": [
    {
      "id": "job-2025-006",
      "container_no": "EGLV1112223",
      "vessel_name": "EVER GIVEN",
      "status": "DELAYED",
      "original_eta": "2025-12-20T10:00:00",
      "days_delayed": 2,
      "risk_flag": true
    }
  ]
}
```

---

### 10. `get_shipments_by_route`

Get shipments on a specific trade route with statistics.

**Parameters:**
- `origin` (string, optional): Origin port (partial match)
- `destination` (string, optional): Destination port (partial match)
- `status_filter` (string, optional): Filter by status

**Example Query:**
> "Show me all shipments from China to USA"
> "What's on the route from Hong Kong to Rotterdam?"

**Response:**
```json
{
  "success": true,
  "route": {
    "origin": "Hong Kong",
    "destination": "Rotterdam"
  },
  "statistics": {
    "total": 1,
    "in_transit": 0,
    "delayed": 1,
    "at_risk": 1
  },
  "shipments": [
    {
      "id": "job-2025-002",
      "vessel_name": "COSCO SHIPPING UNIVERSE",
      "status": "DELAYED",
      "eta": "2025-12-22T16:00:00"
    }
  ]
}
```

---

## System Tools

### 11. `get_server_status`

Get server health and status information.

**Parameters:**
- `include_details` (bool, default=false): Include detailed metrics

**Example Query:**
> "Is the server healthy?"
> "Get server status with details"

---

## Use Cases & Examples

### Use Case 1: Customer Service - Status Update

**Scenario:** Customer calls asking about their container

**Voice Command:**
> "Track container MSCU1234567"

**Tool Used:** `track_shipment`

**Response:** Full tracking details with ETA, location, status

---

### Use Case 2: Operations - Risk Management

**Scenario:** Identify all at-risk shipments for review

**Voice Command:**
> "Show me all shipments with risk flags"

**Tool Used:** `search_shipments(risk_flag=true)`

**Follow-up:**
> "Add a note to job-2025-002 that we contacted the customer"

**Tool Used:** `add_agent_note`

---

### Use Case 3: Planning - Route Analysis

**Scenario:** Analyze a specific trade route

**Voice Command:**
> "Show me all shipments from Shanghai to Los Angeles"

**Tool Used:** `get_shipments_by_route(origin="Shanghai", destination="Los Angeles")`

**Response:** Route statistics + list of all shipments

---

### Use Case 4: Management - Daily Overview

**Scenario:** Morning briefing on shipment status

**Voice Command:**
> "Give me an analytics overview"

**Tool Used:** `get_shipments_analytics`

**Follow-up:**
> "Show me delayed shipments"

**Tool Used:** `get_delayed_shipments`

---

### Use Case 5: Complex Search

**Scenario:** Find specific subset of shipments

**Voice Command:**
> "Find all in-transit shipments from Asia arriving before Christmas with risk flags"

**Tool Used:** 
```
search_shipments_advanced(
  origin_port="Asia",
  status_codes=["IN_TRANSIT"],
  risk_flag=true,
  eta_to="2025-12-25"
)
```

---

### Use Case 6: Text-Based Search

**Scenario:** Search for shipments mentioning a specific term

**Voice Command:**
> "Search for anything related to Suez Canal"

**Tool Used:** `query_shipments_by_criteria(search_text="Suez Canal")`

**Response:** All shipments with "Suez Canal" in any field

---

## Tool Selection Guide

**When to use each tool:**

| Need | Recommended Tool |
|------|-----------------|
| Find a specific shipment | `track_shipment` |
| Simple filter (risk/status) | `search_shipments` |
| Complex multi-filter search | `search_shipments_advanced` ⭐ |
| Text search across fields | `query_shipments_by_criteria` ⭐ |
| Get statistics/overview | `get_shipments_analytics` ⭐ |
| Find delayed shipments | `get_delayed_shipments` |
| Analyze a trade route | `get_shipments_by_route` |
| Update shipment data | `update_shipment_eta`, `set_risk_flag`, `add_agent_note` |
| Check system health | `get_server_status` |

---

## Tips for Voice Agents (11Labs)

### Natural Language Mapping

The agent should intelligently map natural language to tools:

**User says:** → **Tool to use:**
- "Show me..." → `search_*` or `get_*`
- "Find all..." → `search_shipments_advanced`
- "Track..." → `track_shipment`
- "Update..." → `update_shipment_eta` or `set_risk_flag`
- "Add note..." → `add_agent_note`
- "Statistics" / "Overview" → `get_shipments_analytics`
- "Delayed" → `get_delayed_shipments`
- "From X to Y" → `get_shipments_by_route`
- "Search for [text]" → `query_shipments_by_criteria`

### Combining Tools

For complex queries, use multiple tools in sequence:

1. **First:** Get list of shipments
2. **Then:** Get details for specific ones
3. **Finally:** Update or add notes as needed

**Example Flow:**
```
User: "Show me delayed shipments and flag them as risk"
→ get_delayed_shipments()
→ For each: set_risk_flag(identifier, true, "Delayed past ETA")
```

---

**Last Updated:** December 18, 2025
**Version:** 1.1.0
**Total Tools:** 11
