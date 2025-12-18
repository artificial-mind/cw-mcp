# Quick Reference Card - MCP Tools

## 🚀 Quick Tool Selector

```
Need to...                              → Use Tool
────────────────────────────────────────────────────────────────
Find specific container                 → track_shipment
Simple filter (risk/status)             → search_shipments
Complex multi-filter                    → search_shipments_advanced ⭐
Search text across all fields           → query_shipments_by_criteria ⭐
Get statistics/overview                 → get_shipments_analytics ⭐
Find delayed shipments                  → get_delayed_shipments
Analyze trade route                     → get_shipments_by_route
Update ETA                              → update_shipment_eta
Flag/unflag risk                        → set_risk_flag
Add notes                               → add_agent_note
Check server health                     → get_server_status
```

## 📋 Common Queries (Copy & Paste)

### 1. Track Container
```
"Track container MSCU1234567"
→ track_shipment(identifier="MSCU1234567")
```

### 2. Find High Risk
```
"Show me risky shipments"
→ search_shipments(risk_flag=true)
```

### 3. Dashboard Overview
```
"Give me an overview"
→ get_shipments_analytics()
```

### 4. Find Delayed
```
"What's delayed?"
→ get_delayed_shipments(days_delayed=1)
```

### 5. Complex Search
```
"MSC vessels from Shanghai to Los Angeles arriving before Dec 25"
→ search_shipments_advanced(
    vessel_name="MSC",
    origin_port="Shanghai", 
    destination_port="Los Angeles",
    eta_to="2025-12-25"
  )
```

### 6. Text Search
```
"Search for Rotterdam"
→ query_shipments_by_criteria(search_text="Rotterdam")
```

### 7. Route Analysis
```
"Shanghai to Los Angeles route"
→ get_shipments_by_route(origin="Shanghai", destination="Los Angeles")
```

## 🎯 By Use Case

### Customer Service
```
1. track_shipment → Get details
2. add_agent_note → Log interaction
3. update_shipment_eta → If needed
```

### Operations Morning Briefing
```
1. get_shipments_analytics → Dashboard
2. get_delayed_shipments → Issues
3. search_shipments(risk_flag=true) → Risks
```

### Emergency Response
```
1. search_shipments_advanced → Find affected
2. set_risk_flag → Flag issues
3. add_agent_note → Document actions
```

### Route Planning
```
1. get_shipments_by_route → Route stats
2. search_shipments_advanced → Filter details
3. get_shipments_analytics → Big picture
```

## 🔥 Power User Combos

### Find Urgent Issues
```json
search_shipments_advanced({
  "risk_flag": true,
  "status_codes": ["DELAYED", "CUSTOMS_HOLD"],
  "eta_to": "2025-12-25"
})
```

### Route Performance
```json
get_shipments_by_route({
  "origin": "Asia",
  "destination": "USA"
})
→ Then drill down with search_shipments_advanced
```

### Smart Text Search
```json
query_shipments_by_criteria({
  "search_text": "customs",
  "sort_by": "eta",
  "include_fields": ["id", "container_no", "status_code", "eta"]
})
```

## 📊 Response Field Reference

### Minimal (search_shipments)
- id, container_no, status, risk_flag, origin, destination, eta

### Detailed (search_shipments_advanced)
- + vessel_name, voyage_number, current_location, etd, status_description

### Complete (track_shipment)
- All fields + notes array

### Analytics (get_shipments_analytics)
- summary: totals, counts, breakdowns
- details: top ports, vessels, upcoming arrivals

## 🎤 Voice Command Patterns

```
"Show me..." → search/query
"Track..." → track_shipment
"Find..." → search_shipments_advanced
"What's..." → query_shipments_by_criteria
"Analytics/Overview" → get_shipments_analytics
"Delayed" → get_delayed_shipments
"Route from X to Y" → get_shipments_by_route
"Update..." → update_shipment_eta
"Flag..." → set_risk_flag
"Add note..." → add_agent_note
```

## ⚡ Speed Tips

1. **Use analytics first** for overview, then drill down
2. **Text search** when you don't know exact field
3. **Advanced search** for precise multi-filter queries
4. **Route analysis** for trade lane insights
5. **Delayed tool** for proactive monitoring

## 🔗 Quick Links

- Full Reference: `docs/TOOLS_REFERENCE.md`
- Query Samples: `QUERY_SAMPLES.md`
- Improvement Summary: `TOOLS_IMPROVEMENT_SUMMARY.md`

---

**Print this card for quick reference!** 🖨️
