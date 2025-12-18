# MCP Tools Query Samples

Real-world query examples for all 11 tools with expected responses.

---

## 🔍 Basic Search Queries

### 1. Find All High-Risk Shipments

**Voice Command:**
> "Show me all shipments with risk flags"

**Tool:** `search_shipments`
```json
{
  "risk_flag": true,
  "limit": 20
}
```

**Expected Response:**
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
    },
    {
      "id": "job-2025-006",
      "container_no": "EGLV1112223",
      "status": "DELAYED",
      "risk_flag": true,
      "origin": "Kaohsiung, Taiwan",
      "destination": "Felixstowe, UK",
      "eta": "2025-12-20T10:00:00"
    },
    {
      "id": "job-2025-009",
      "container_no": "ZIMU9998887",
      "status": "CUSTOMS_HOLD",
      "risk_flag": true,
      "origin": "Haifa, Israel",
      "destination": "Dubai, UAE",
      "eta": "2025-12-17T13:00:00"
    }
  ]
}
```

---

### 2. Find Shipments by Status

**Voice Command:**
> "Show me all delayed shipments"

**Tool:** `search_shipments`
```json
{
  "status_code": "DELAYED",
  "limit": 10
}
```

**Expected Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "id": "job-2025-002",
      "container_no": "COSU9876543",
      "status": "DELAYED",
      "risk_flag": true
    },
    {
      "id": "job-2025-006",
      "container_no": "EGLV1112223",
      "status": "DELAYED",
      "risk_flag": true
    }
  ]
}
```

---

### 3. Track Specific Container

**Voice Command:**
> "Track container MSCU1234567"

**Tool:** `track_shipment`
```json
{
  "identifier": "MSCU1234567"
}
```

**Expected Response:**
```json
{
  "success": true,
  "shipment": {
    "id": "job-2025-001",
    "container_no": "MSCU1234567",
    "master_bill": "MAEU123456789",
    "status": "IN_TRANSIT",
    "risk_flag": false,
    "origin": "Shanghai, China",
    "destination": "Los Angeles, USA",
    "eta": "2025-12-25T14:30:00",
    "vessel": "MSC GULSUN",
    "voyage": "025W",
    "notes": []
  }
}
```

---

## 🚀 Advanced Search Queries

### 4. Multi-Filter Search - Vessel + Port

**Voice Command:**
> "Show me all MSC vessels going to Los Angeles"

**Tool:** `search_shipments_advanced`
```json
{
  "vessel_name": "MSC",
  "destination_port": "Los Angeles",
  "limit": 20
}
```

**Expected Response:**
```json
{
  "success": true,
  "count": 1,
  "results": [
    {
      "id": "job-2025-001",
      "container_no": "MSCU1234567",
      "vessel_name": "MSC GULSUN",
      "voyage_number": "025W",
      "status": "IN_TRANSIT",
      "origin": "Shanghai, China",
      "destination": "Los Angeles, USA",
      "current_location": "South China Sea",
      "eta": "2025-12-25T14:30:00",
      "etd": "2025-12-10T08:00:00"
    }
  ]
}
```

---

### 5. Date Range Query

**Voice Command:**
> "Find all shipments arriving before Christmas"

**Tool:** `search_shipments_advanced`
```json
{
  "eta_to": "2025-12-25",
  "status_codes": ["IN_TRANSIT", "DELAYED"],
  "limit": 20
}
```

**Expected Response:**
```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": "job-2025-006",
      "vessel_name": "EVER GIVEN",
      "status": "DELAYED",
      "destination": "Felixstowe, UK",
      "eta": "2025-12-20T10:00:00"
    },
    {
      "id": "job-2025-002",
      "vessel_name": "COSCO SHIPPING UNIVERSE",
      "status": "DELAYED",
      "destination": "Rotterdam, Netherlands",
      "eta": "2025-12-22T16:00:00"
    }
  ]
}
```

---

### 6. Complex Multi-Filter Query

**Voice Command:**
> "Show me all high-risk shipments from Asia arriving in USA ports that are in transit or delayed"

**Tool:** `search_shipments_advanced`
```json
{
  "origin_port": "Asia",
  "destination_port": "USA",
  "status_codes": ["IN_TRANSIT", "DELAYED"],
  "risk_flag": true,
  "limit": 20
}
```

---

### 7. Specific Trade Route with Date Range

**Voice Command:**
> "Find shipments from China to USA arriving between December 20-30"

**Tool:** `search_shipments_advanced`
```json
{
  "origin_port": "China",
  "destination_port": "USA",
  "eta_from": "2025-12-20",
  "eta_to": "2025-12-30",
  "limit": 20
}
```

---

## 📊 Analytics Queries

### 8. Complete Dashboard Overview

**Voice Command:**
> "Give me an overview of all shipments"
> "Show me statistics"
> "What's the current status?"

**Tool:** `get_shipments_analytics`
```json
{}
```

**Expected Response:**
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
      {"port": "Shanghai, China", "count": 1},
      {"port": "Hong Kong", "count": 1},
      {"port": "Singapore", "count": 1},
      {"port": "Ningbo, China", "count": 1},
      {"port": "Marseille, France", "count": 1}
    ],
    "top_destination_ports": [
      {"port": "Los Angeles, USA", "count": 2},
      {"port": "Rotterdam, Netherlands", "count": 1},
      {"port": "Hamburg, Germany", "count": 1},
      {"port": "Long Beach, USA", "count": 1},
      {"port": "New York, USA", "count": 1}
    ],
    "active_vessels": [
      "MSC GULSUN",
      "COSCO SHIPPING UNIVERSE",
      "OOCL HONG KONG",
      "CMA CGM ANTOINE DE SAINT EXUPERY",
      "EVER GIVEN",
      "ONE APUS",
      "MSC MAYA"
    ],
    "upcoming_arrivals": {
      "count": 3,
      "shipments": [
        {
          "id": "job-2025-006",
          "container_no": "EGLV1112223",
          "eta": "2025-12-20T10:00:00",
          "destination": "Felixstowe, UK"
        },
        {
          "id": "job-2025-002",
          "container_no": "COSU9876543",
          "eta": "2025-12-22T16:00:00",
          "destination": "Rotterdam, Netherlands"
        },
        {
          "id": "job-2025-004",
          "container_no": "OOLU3334445",
          "eta": "2025-12-24T11:00:00",
          "destination": "Long Beach, USA"
        }
      ]
    }
  }
}
```

---

## 🔎 Flexible Text Search

### 9. Search Across All Fields

**Voice Command:**
> "Search for anything related to Rotterdam"

**Tool:** `query_shipments_by_criteria`
```json
{
  "search_text": "Rotterdam",
  "sort_by": "eta",
  "sort_order": "asc",
  "limit": 10
}
```

**Expected Response:**
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
      "master_bill": "COSU987654321",
      "vessel_name": "COSCO SHIPPING UNIVERSE",
      "origin_port": "Hong Kong",
      "destination_port": "Rotterdam, Netherlands",
      "status_code": "DELAYED",
      "eta": "2025-12-22T16:00:00"
    }
  ]
}
```

---

### 10. Search with Custom Fields

**Voice Command:**
> "Find MSC vessels and show only container number, vessel name, and ETA"

**Tool:** `query_shipments_by_criteria`
```json
{
  "search_text": "MSC",
  "include_fields": ["container_no", "vessel_name", "eta"],
  "sort_by": "eta",
  "limit": 10
}
```

**Expected Response:**
```json
{
  "success": true,
  "count": 2,
  "results": [
    {
      "container_no": "MSCU1234567",
      "vessel_name": "MSC GULSUN",
      "eta": "2025-12-25T14:30:00"
    },
    {
      "container_no": "MSMU7776665",
      "vessel_name": "MSC MAYA",
      "eta": "2025-12-30T17:00:00"
    }
  ]
}
```

---

### 11. Search with Sorting

**Voice Command:**
> "Show all in-transit shipments sorted by ETA, most urgent first"

**Tool:** `query_shipments_by_criteria`
```json
{
  "search_text": "IN_TRANSIT",
  "sort_by": "eta",
  "sort_order": "asc",
  "limit": 10
}
```

---

## ⏰ Delayed Shipments

### 12. Find All Delayed Shipments

**Voice Command:**
> "Show me all delayed shipments"
> "What's running late?"

**Tool:** `get_delayed_shipments`
```json
{
  "days_delayed": 1
}
```

**Expected Response:**
```json
{
  "success": true,
  "count": 2,
  "criteria": "Delayed by 1+ days",
  "results": [
    {
      "id": "job-2025-009",
      "container_no": "ZIMU9998887",
      "vessel_name": "ZIM SAMMY OFER",
      "status": "CUSTOMS_HOLD",
      "origin": "Haifa, Israel",
      "destination": "Dubai, UAE",
      "original_eta": "2025-12-17T13:00:00",
      "days_delayed": 1,
      "risk_flag": true,
      "agent_notes": "URGENT: Missing commercial invoice. Coordinating with shipper."
    },
    {
      "id": "job-2025-006",
      "container_no": "EGLV1112223",
      "vessel_name": "EVER GIVEN",
      "status": "DELAYED",
      "origin": "Kaohsiung, Taiwan",
      "destination": "Felixstowe, UK",
      "original_eta": "2025-12-20T10:00:00",
      "days_delayed": 0,
      "risk_flag": true,
      "agent_notes": "High priority shipment. Customer anxious about delays."
    }
  ]
}
```

---

### 13. Find Critically Delayed Shipments

**Voice Command:**
> "Show me shipments delayed by more than 3 days"

**Tool:** `get_delayed_shipments`
```json
{
  "days_delayed": 3
}
```

---

## 🌍 Route-Based Queries

### 14. Analyze Specific Trade Route

**Voice Command:**
> "Show me all shipments from Shanghai to Los Angeles"
> "What's on the China to USA route?"

**Tool:** `get_shipments_by_route`
```json
{
  "origin": "Shanghai",
  "destination": "Los Angeles"
}
```

**Expected Response:**
```json
{
  "success": true,
  "route": {
    "origin": "Shanghai",
    "destination": "Los Angeles"
  },
  "statistics": {
    "total": 1,
    "in_transit": 1,
    "delayed": 0,
    "at_risk": 0
  },
  "shipments": [
    {
      "id": "job-2025-001",
      "container_no": "MSCU1234567",
      "vessel_name": "MSC GULSUN",
      "status": "IN_TRANSIT",
      "origin": "Shanghai, China",
      "destination": "Los Angeles, USA",
      "eta": "2025-12-25T14:30:00",
      "risk_flag": false
    }
  ]
}
```

---

### 15. Filter Route by Status

**Voice Command:**
> "Show me only delayed shipments from Asia to Europe"

**Tool:** `get_shipments_by_route`
```json
{
  "origin": "Asia",
  "destination": "Europe",
  "status_filter": "DELAYED"
}
```

---

### 16. Analyze Destination Port

**Voice Command:**
> "What shipments are going to Los Angeles?"

**Tool:** `get_shipments_by_route`
```json
{
  "destination": "Los Angeles"
}
```

---

## 🔄 Update Operations

### 17. Update ETA

**Voice Command:**
> "Update ETA for container MSCU1234567 to December 28th due to weather delay"

**Tool:** `update_shipment_eta`
```json
{
  "identifier": "MSCU1234567",
  "new_eta": "2025-12-28",
  "reason": "Weather delay in Pacific Ocean"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "ETA updated for job-2025-001",
  "old_eta": "2025-12-25T14:30:00",
  "new_eta": "2025-12-28T00:00:00"
}
```

---

### 18. Set Risk Flag

**Voice Command:**
> "Flag container COSU9876543 as high risk due to customs issues"

**Tool:** `set_risk_flag`
```json
{
  "identifier": "COSU9876543",
  "is_risk": true,
  "reason": "Customs documentation issues at port"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Risk flag set for job-2025-002",
  "risk_flag": true
}
```

---

### 19. Add Agent Note

**Voice Command:**
> "Add note to job-2025-002 that customer called requesting urgent update"

**Tool:** `add_agent_note`
```json
{
  "identifier": "job-2025-002",
  "note": "Customer called requesting urgent update on delivery status",
  "agent_name": "Sarah Johnson"
}
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Note added to job-2025-002"
}
```

---

## 🎯 Real-World Scenarios

### Scenario 1: Morning Operations Briefing

**Agent:** "Good morning! Give me a quick overview"

**Query Sequence:**
1. `get_shipments_analytics()` → Dashboard overview
2. `get_delayed_shipments(days_delayed=1)` → Check delays
3. `search_shipments(risk_flag=true)` → High-risk items

---

### Scenario 2: Customer Service Call

**Customer:** "Where is my container MSCU1234567?"

**Query Sequence:**
1. `track_shipment(identifier="MSCU1234567")` → Full details
2. If delayed → `update_shipment_eta()` + `add_agent_note()`

---

### Scenario 3: Route Performance Analysis

**Manager:** "How's the Shanghai to LA route performing?"

**Query Sequence:**
1. `get_shipments_by_route(origin="Shanghai", destination="Los Angeles")` → Route stats
2. `search_shipments_advanced(origin_port="Shanghai", destination_port="Los Angeles", status_codes=["DELAYED"])` → Problem shipments

---

### Scenario 4: Emergency Response

**Alert:** "Vessel EVER GIVEN delayed due to port congestion"

**Query Sequence:**
1. `search_shipments_advanced(vessel_name="EVER GIVEN")` → Find all affected
2. For each: `set_risk_flag(is_risk=true, reason="Port congestion delay")`
3. For each: `add_agent_note(note="Customer notified of delay")`

---

### Scenario 5: End of Day Report

**Manager:** "What needs attention before we close?"

**Query Sequence:**
1. `get_delayed_shipments(days_delayed=1)` → Urgent items
2. `get_shipments_analytics()` → Overall status
3. `search_shipments(risk_flag=true, limit=20)` → Risk review

---

## 💡 Pro Tips

### Combining Filters for Power Queries

**Find urgent high-risk shipments from Asia:**
```json
{
  "tool": "search_shipments_advanced",
  "params": {
    "origin_port": "Asia",
    "risk_flag": true,
    "status_codes": ["DELAYED", "CUSTOMS_HOLD"],
    "eta_to": "2025-12-25"
  }
}
```

### Using Text Search Smartly

**Search for anything related to a problem:**
```json
{
  "tool": "query_shipments_by_criteria",
  "params": {
    "search_text": "customs",
    "sort_by": "eta",
    "sort_order": "asc"
  }
}
```

### Route Analysis with Filters

**Check specific vessel on route:**
```json
{
  "tool": "search_shipments_advanced",
  "params": {
    "vessel_name": "MSC GULSUN",
    "origin_port": "Shanghai",
    "destination_port": "Los Angeles"
  }
}
```

---

## 🎤 Natural Language → Tool Mapping

| What User Says | Tool to Use | Key Parameters |
|----------------|-------------|----------------|
| "Show me..." | `search_shipments` or `search_shipments_advanced` | Based on complexity |
| "Track..." | `track_shipment` | identifier |
| "Find anything about X" | `query_shipments_by_criteria` | search_text |
| "What's delayed?" | `get_delayed_shipments` | days_delayed |
| "Route from X to Y" | `get_shipments_by_route` | origin, destination |
| "Give me statistics" | `get_shipments_analytics` | none |
| "Update ETA..." | `update_shipment_eta` | identifier, new_eta |
| "Flag as risk..." | `set_risk_flag` | identifier, is_risk |
| "Add note..." | `add_agent_note` | identifier, note |

---

**Last Updated:** December 18, 2025  
**Total Examples:** 19 query samples + 5 real-world scenarios
