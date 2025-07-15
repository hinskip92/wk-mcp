#!/usr/bin/env python3
"""
Wild Kratts MCP Server with HTTP endpoint for Railway deployment
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Union
import httpx
from urllib.parse import quote
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    LoggingLevel
)
import mcp.types as types

# Import the original server class
from server import WildKrattsServer

# FastAPI app for HTTP endpoints
app = FastAPI(
    title="Wild Kratts MCP Server",
    description="MCP server providing Wild Kratts content and basic maps functionality",
    version="1.0.0"
)

# Global MCP server instance
mcp_server_instance = None

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server on startup"""
    global mcp_server_instance
    mcp_server_instance = WildKrattsServer()

@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Wild Kratts MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "tools": "/tools"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {
        "status": "healthy",
        "service": "Wild Kratts MCP Server",
        "version": "1.0.0"
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    tools = [
        {
            "name": "view_location_google_maps",
            "description": "View a specific geographical location",
            "parameters": ["query"]
        },
        {
            "name": "search_google_maps", 
            "description": "Search for places near a location",
            "parameters": ["search"]
        },
        {
            "name": "directions_on_google_maps",
            "description": "Get directions from origin to destination",
            "parameters": ["origin", "destination"]
        },
        {
            "name": "get_wild_kratts_products",
            "description": "Fetch Wild Kratts products with search and filtering",
            "parameters": ["searchTerm", "category", "page"]
        },
        {
            "name": "get_wild_kratts_episodes",
            "description": "Fetch Wild Kratts episodes with filtering options",
            "parameters": ["seasonNumber", "episodeTitle", "animalsFeatured", "fields"]
        }
    ]
    return {"tools": tools}

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """Handle MCP protocol requests via HTTP"""
    try:
        body = await request.json()
        
        # Extract method and params from MCP request
        method = body.get("method")
        params = body.get("params", {})
        
        if method == "tools/list":
            # Return list of available tools
            tools = [
                {
                    "name": "view_location_google_maps",
                    "description": "View a specific geographical location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Location to view"}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "search_google_maps", 
                    "description": "Search for places near a location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "search": {"type": "string", "description": "Search query"}
                        },
                        "required": ["search"]
                    }
                },
                {
                    "name": "directions_on_google_maps",
                    "description": "Get directions from origin to destination",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "origin": {"type": "string", "description": "Starting location"},
                            "destination": {"type": "string", "description": "Destination"}
                        },
                        "required": ["origin", "destination"]
                    }
                },
                {
                    "name": "get_wild_kratts_products",
                    "description": "Fetch Wild Kratts products",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "searchTerm": {"type": "string", "description": "Search term"},
                            "category": {"type": "string", "description": "Category filter"},
                            "page": {"type": "integer", "description": "Page number", "default": 1}
                        }
                    }
                },
                {
                    "name": "get_wild_kratts_episodes",
                    "description": "Fetch Wild Kratts episodes",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "seasonNumber": {"type": "integer", "description": "Season number"},
                            "episodeTitle": {"type": "string", "description": "Episode title"},
                            "animalsFeatured": {"type": "array", "items": {"type": "string"}},
                            "fields": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            # Handle tool call
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            # Use the MCP server instance to handle the call
            result = await handle_tool_call(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"content": result}
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "id": body.get("id") if "body" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
        )

async def handle_tool_call(name: str, arguments: Dict[str, Any]) -> List[Dict[str, str]]:
    """Handle tool calls using the MCP server logic"""
    
    if name == "view_location_google_maps":
        query = arguments.get("query", "")
        return [{"type": "text", "text": f"Information for location: {query} would be processed."}]
        
    elif name == "search_google_maps":
        search = arguments.get("search", "")
        return [{"type": "text", "text": f"Search results for: {search} would be processed."}]
        
    elif name == "directions_on_google_maps":
        origin = arguments.get("origin", "")
        destination = arguments.get("destination", "")
        return [{"type": "text", "text": f"Directions from {origin} to {destination} would be processed."}]
        
    elif name == "get_wild_kratts_products":
        # Use the MCP server instance
        result = await mcp_server_instance._handle_get_products(arguments)
        return [{"type": "text", "text": result[0].text}]
        
    elif name == "get_wild_kratts_episodes":
        # Use the MCP server instance
        result = await mcp_server_instance._handle_get_episodes(arguments)
        return [{"type": "text", "text": result[0].text}]
        
    else:
        raise ValueError(f"Unknown tool: {name}")

# Test endpoint for quick verification
@app.get("/test/products")
async def test_products():
    """Test endpoint for products"""
    try:
        result = await handle_tool_call("get_wild_kratts_products", {"searchTerm": "plush"})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/episodes")
async def test_episodes():
    """Test endpoint for episodes"""
    try:
        result = await handle_tool_call("get_wild_kratts_episodes", {"seasonNumber": 1, "fields": ["Episode Title"]})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",  # Required for Railway
        port=port,
        log_level="info"
    )