"""
Main FastAPI server with MCP SSE transport
Logistics Orchestrator MCP Server - Production Grade
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.responses import StreamingResponse

from config import settings
from database.database import init_db
from tools import LogisticsTools
from auth import AuthMiddleware, verify_api_key
from utils import setup_logging, format_response

# Setup logging
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting Logistics MCP Orchestrator Server...")
    logger.info(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    logger.info("✅ Server startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")


# Create FastAPI app
app = FastAPI(
    title="Logistics MCP Orchestrator",
    description="Universal Translator for AI Agents and Logistics Systems",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
# Note: Disabled for MCP SSE endpoint as it has its own auth
# app.middleware("http")(AuthMiddleware(app))

# Create MCP server
mcp_server = Server("logistics-orchestrator")

# Register tools
logistics_tools = LogisticsTools(mcp_server)

logger.info("✅ MCP tools registered")


@app.get("/")
async def root():
    """Root endpoint - server info"""
    return {
        "name": "Logistics MCP Orchestrator",
        "version": "1.0.0",
        "description": "Universal Translator for AI Agents and Logistics Systems",
        "status": "running",
        "endpoints": {
            "sse": "/sse",
            "webhook": "/webhook (11Labs voice agent)",
            "messages": "/messages (MCP JSON-RPC)",
            "health": "/health",
            "info": "/info"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return format_response(
        success=True,
        data={"status": "healthy", "service": "logistics-mcp-orchestrator"}
    )


@app.get("/info")
async def server_info():
    """Server information and configuration (non-sensitive)"""
    return format_response(
        success=True,
        data={
            "server": {
                "name": "Logistics MCP Orchestrator",
                "version": "1.0.0",
                "debug": settings.DEBUG
            },
            "database": {
                "type": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql"
            },
            "external_apis": {
                "logitude": "connected" if settings.LOGITUDE_API_KEY != "placeholder-key" else "mock",
                "dpworld": "connected" if settings.DPWORLD_API_KEY != "placeholder-key" else "mock",
                "tracking": "connected" if settings.TRACKING_API_KEY != "placeholder-key" else "mock"
            },
            "tools": [
                "track_shipment",
                "update_shipment_eta",
                "set_risk_flag",
                "add_agent_note",
                "search_shipments"
            ]
        }
    )


@app.get("/sse")
@app.post("/sse")
async def handle_sse(request: Request):
    """
    SSE endpoint for MCP protocol using proper MCP SDK transport
    This is the primary endpoint for MCP clients (11Labs, Claude, etc.)
    """
    from mcp.server.sse import SseServerTransport
    from mcp.shared.memory import InMemoryStream
    
    logger.info(f"🔌 New SSE connection from {request.client.host} (method: {request.method})")
    
    # Handle POST requests for client messages
    if request.method == "POST":
        try:
            body = await request.json()
            logger.info(f"📨 Received MCP message: {body}")
            
            # Create in-memory streams for this request
            read_stream = InMemoryStream()
            write_stream = InMemoryStream()
            
            # Write the incoming message to read stream
            await read_stream.write(body)
            
            # Process with MCP server
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options()
            )
            
            # Read response from write stream
            response = await write_stream.read()
            logger.info(f"📤 Sending MCP response: {response}")
            
            return JSONResponse(content=response)
            
        except Exception as e:
            logger.error(f"❌ Error handling POST: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
            )
    
    # Handle GET for SSE stream
    else:
        async def event_generator():
            """Generate SSE events for MCP protocol"""
            import json
            
            try:
                # Send endpoint message (MCP spec)
                endpoint_msg = {
                    "jsonrpc": "2.0",
                    "method": "endpoint",
                    "params": {
                        "uri": str(request.url).replace("/sse", "/messages")
                    }
                }
                yield f"event: endpoint\n"
                yield f"data: {json.dumps(endpoint_msg)}\n\n"
                
                logger.info("✅ SSE stream established, sent endpoint")
                
                # Keep connection alive
                while True:
                    await asyncio.sleep(30)
                    
                    if await request.is_disconnected():
                        logger.info("🔌 SSE client disconnected")
                        break
                    
                    # Send ping to keep alive
                    yield f": ping\n\n"
                    
            except asyncio.CancelledError:
                logger.info("🔌 SSE connection cancelled")
            except Exception as e:
                logger.error(f"❌ SSE error: {e}", exc_info=True)
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS"
            }
        )


def format_for_voice(result: dict, tool_name: str) -> str:
    """Format tool results into natural voice responses for 11Labs"""
    
    if tool_name == "search_shipments":
        results = result.get("results", [])
        count = len(results)
        
        if count == 0:
            return "I didn't find any shipments matching your criteria. Would you like to try a different search?"
        
        response = f"I found {count} shipment{'s' if count != 1 else ''}. "
        
        # Describe first 3 shipments
        for i, ship in enumerate(results[:3], 1):
            ship_id = ship.get('id', 'Unknown')
            location = ship.get('tracking', {}).get('location', {}).get('name', 'Unknown')
            status = ship.get('status', {}).get('code', 'UNKNOWN').replace('_', ' ').lower()
            response += f"Shipment {i}: {ship_id}, {status}, currently at {location}. "
        
        if count > 3:
            response += f"And {count - 3} more shipment{'s' if count - 3 != 1 else ''}. "
        
        response += "Would you like details on any specific shipment?"
        return response
    
    elif tool_name == "get_shipment_details" or tool_name == "track_shipment":
        # Result format from track_shipment tool
        if result.get("success"):
            data = result.get("data", {})
            shipment = data  # The actual shipment data
        else:
            return "I couldn't find that shipment. Please check the ID and try again."
        
        if not shipment:
            return "I couldn't find that shipment. Please check the ID and try again."
        
        ship_id = shipment.get('id', 'Unknown')
        vessel = shipment.get('tracking', {}).get('vessel', 'Unknown vessel')
        location = shipment.get('tracking', {}).get('location', {}).get('name', 'Unknown')
        status = shipment.get('status', {}).get('code', 'UNKNOWN').replace('_', ' ').lower()
        
        response = f"Shipment {ship_id} is {status}. "
        response += f"It's currently at {location} on the {vessel}. "
        
        if shipment.get('flags', {}).get('is_risk'):
            response += "This shipment is flagged as high risk. "
            notes = shipment.get('flags', {}).get('agent_notes', '')
            if notes:
                response += notes[:150] + ". " if len(notes) > 150 else notes + ". "
        
        return response
    
    elif tool_name == "update_shipment_status" or tool_name == "set_risk_flag":
        if result.get("success"):
            return f"Successfully updated. {result.get('message', '')}"
        return "I couldn't complete the update. Please try again."
    
    elif tool_name == "track_vessel":
        results = result.get("results", [])
        vessel_name = result.get("vessel_name", "Unknown")
        
        if not results:
            return f"I couldn't find any shipments on the {vessel_name}. Please check the vessel name."
        
        location = results[0].get('tracking', {}).get('location', {}).get('name', 'Unknown') if results else 'Unknown'
        
        response = f"The {vessel_name} "
        if location != 'Unknown':
            response += f"is currently at {location}. "
        response += f"It's carrying {len(results)} shipment{'s' if len(results) != 1 else ''}. "
        
        if len(results) <= 3:
            for ship in results:
                ship_id = ship.get('id', 'Unknown')
                status = ship.get('status', {}).get('code', '').replace('_', ' ').lower()
                response += f"{ship_id} is {status}. "
        
        return response
    
    elif tool_name == "get_analytics":
        # Return aggregated statistics
        results = result.get("results", [])
        return f"Analytics complete. Found {len(results)} total records."
    
    # Default: return success message
    return result.get("message", "Operation completed successfully.")


@app.post("/webhook")
async def handle_elevenlabs_webhook(request: Request):
    """
    Direct webhook endpoint for 11Labs voice agent
    
    Accepts: {"function": "search_shipments", "arguments": {"risk_flag": true}}
    Returns: Plain string response for voice synthesis
    
    This eliminates the need for a separate bridge server!
    """
    try:
        data = await request.json()
        logger.info(f"11Labs webhook: {data}")
        
        # Extract function and arguments
        function_name = data.get("function") or data.get("name")
        arguments = data.get("arguments") or data.get("parameters") or {}
        
        if not function_name:
            return "I didn't receive a valid function call."
        
        # Map 11Labs function names to MCP tool names
        tool_map = {
            "search_shipments": "search_shipments",
            "get_shipment_details": "track_shipment",  # Maps to track_shipment
            "update_shipment_status": "set_risk_flag",  # For status updates
            "track_vessel": "track_shipment",  # Use track_shipment with vessel filter
            "get_analytics": "search_shipments"  # Use search for analytics
        }
        
        tool_name = tool_map.get(function_name, function_name)
        tools_obj = LogisticsTools(mcp_server)
        
        # Call the appropriate tool
        if tool_name == "search_shipments":
            result = await tools_obj.search_shipments(**arguments)
        elif tool_name == "track_shipment":
            # Handle both get_shipment_details and track_vessel
            if "shipment_id" in arguments:
                result = await tools_obj.track_shipment(identifier=arguments["shipment_id"])
            elif "vessel_name" in arguments:
                # For vessel tracking, search all and filter by vessel in response
                all_shipments = await tools_obj.search_shipments(limit=50)
                vessel_name = arguments["vessel_name"].upper()
                filtered = [s for s in all_shipments.get("results", []) 
                           if vessel_name in s.get("tracking", {}).get("vessel", "").upper()]
                result = {"success": True, "results": filtered, "vessel_name": arguments["vessel_name"]}
            else:
                result = await tools_obj.track_shipment(**arguments)
        elif tool_name == "set_risk_flag":
            result = await tools_obj.set_risk_flag(**arguments)
        elif tool_name == "add_agent_note":
            result = await tools_obj.add_agent_note(**arguments)
        elif tool_name == "update_shipment_eta":
            result = await tools_obj.update_shipment_eta(**arguments)
        else:
            return f"Unknown function: {function_name}"
        
        # Format for voice and return plain string
        voice_response = format_for_voice(result, function_name)
        logger.info(f"Voice response: {voice_response}")
        
        return voice_response
    
    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return "I encountered an error processing your request. Please try again."


@app.post("/messages")
async def handle_messages(request: Request):
    """
    Handle POST messages for MCP JSON-RPC 2.0 protocol
    Used by MCP clients and AI agents
    """
    try:
        message = await request.json()
        logger.debug(f"Received message: {message}")
        
        # Extract method and params
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id", 1)
        
        # Handle tools/call
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Call the tool directly
            tools_obj = LogisticsTools(mcp_server)
            
            if tool_name == "track_shipment":
                result = await tools_obj.track_shipment(**arguments)
            elif tool_name == "update_shipment_eta":
                result = await tools_obj.update_shipment_eta(**arguments)
            elif tool_name == "set_risk_flag":
                result = await tools_obj.set_risk_flag(**arguments)
            elif tool_name == "add_agent_note":
                result = await tools_obj.add_agent_note(**arguments)
            elif tool_name == "search_shipments":
                result = await tools_obj.search_shipments(**arguments)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            })
        
        # Handle tools/list
        elif method == "tools/list":
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {"name": "track_shipment", "description": "Track a shipment by identifier"},
                        {"name": "update_shipment_eta", "description": "Update shipment ETA"},
                        {"name": "set_risk_flag", "description": "Flag shipment as high-risk"},
                        {"name": "add_agent_note", "description": "Add note to shipment"},
                        {"name": "search_shipments", "description": "Search for shipments"}
                    ]
                }
            })
        
        else:
            return JSONResponse(content={
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            })
    
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=format_response(
            success=False,
            error=str(exc),
            path=str(request.url)
        )
    )


if __name__ == "__main__":
    import uvicorn
    import sys
    from pathlib import Path
    
    # Ensure proper PYTHONPATH for imports
    # Add parent directory to path so 'from config import settings' works
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    logger.info("=" * 60)
    logger.info("LOGISTICS MCP ORCHESTRATOR SERVER")
    logger.info("=" * 60)
    logger.info(f"MCP Protocol: SSE (Server-Sent Events)")
    logger.info(f"Primary Endpoint: /sse")
    logger.info(f"Server: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    logger.info("=" * 60)
    
    # For production/non-reload mode: pass app object
    # For development with reload: pass import string
    if settings.DEBUG:
        # Use import string for reload mode
        uvicorn.run(
            "server:app",
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            reload=True,
            log_level="debug"
        )
    else:
        # Use app object for production
        uvicorn.run(
            app,
            host=settings.SERVER_HOST,
            port=settings.SERVER_PORT,
            log_level="info"
        )
