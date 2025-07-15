#!/usr/bin/env python3
"""
Wild Kratts Server for Railway - Simple FastAPI implementation
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# FastAPI app
app = FastAPI(
    title="Wild Kratts MCP Server",
    description="Wild Kratts content and basic maps functionality",
    version="1.0.0"
)

class WildKrattsAPI:
    def __init__(self):
        self.base_url = "https://wildkratts.com/wp-json"
        self.episodes_api = f"{self.base_url}/wild-kratts/v1/episodes"
        self.products_api = f"{self.base_url}/wp/v2/products"
    
    async def get_products(self, search_term: str = None, category: str = None, page: int = 1) -> dict:
        """Fetch Wild Kratts products"""
        per_page = 20  # Reduced for faster response
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.products_api}?per_page={per_page}&page={page}"
                response = await client.get(url)
                
                if not response.is_success:
                    raise Exception(f"API request failed with status {response.status_code}")
                
                products = response.json() or []
                
                # Simple filtering if search term provided
                if search_term:
                    search_lower = search_term.lower()
                    products = [p for p in products 
                              if search_lower in p.get('title', {}).get('rendered', '').lower()]
                
                # Simple category filtering
                if category:
                    products = [p for p in products 
                              if category.lower() in str(p.get('product_categories', [])).lower()]
                
                # Simplify product data
                simplified_products = []
                for product in products:
                    simplified_products.append({
                        'id': product.get('id'),
                        'title': product.get('title', {}).get('rendered', ''),
                        'link': product.get('link', ''),
                        'categories': product.get('product_categories', [])
                    })
                
                return {
                    'products': simplified_products,
                    'count': len(simplified_products),
                    'page': page
                }
                
        except Exception as error:
            return {
                'error': f"Error fetching products: {str(error)}",
                'products': [],
                'count': 0,
                'page': page
            }

    async def get_episodes(self, season_number: int = None, limit: int = 10) -> dict:
        """Fetch Wild Kratts episodes"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.episodes_api)
                
                if not response.is_success:
                    raise Exception(f"API request failed with status {response.status_code}")
                
                episodes = response.json() or []
                
                # Filter by season if provided
                if season_number is not None:
                    episodes = [ep for ep in episodes if ep.get('Season') == season_number]
                
                # Limit results
                episodes = episodes[:limit]
                
                # Simplify episode data
                simplified_episodes = []
                for episode in episodes:
                    simplified_episodes.append({
                        'season': episode.get('Season'),
                        'episode_number': episode.get('Episode Number (Broadcast Order)'),
                        'title': episode.get('Episode Title', ''),
                        'air_date': episode.get('Air Date', ''),
                        'animals': episode.get('Animals Featured', [])[:5]  # Limit to 5 animals
                    })
                
                return {
                    'episodes': simplified_episodes,
                    'count': len(simplified_episodes)
                }
                
        except Exception as error:
            return {
                'error': f"Error fetching episodes: {str(error)}",
                'episodes': [],
                'count': 0
            }

# Initialize API
api = WildKrattsAPI()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Wild Kratts MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/health", "/products", "/episodes", "/tools"]
    }

@app.get("/health")
async def health_check():
    """Health check for Railway"""
    return {"status": "healthy"}

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            {"name": "get_products", "description": "Get Wild Kratts products"},
            {"name": "get_episodes", "description": "Get Wild Kratts episodes"},
            {"name": "view_maps", "description": "View locations (placeholder)"}
        ]
    }

@app.get("/products")
async def get_products(searchTerm: str = None, category: str = None, page: int = 1):
    """Get Wild Kratts products"""
    return await api.get_products(searchTerm, category, page)

@app.get("/episodes")
async def get_episodes(seasonNumber: int = None, limit: int = 10):
    """Get Wild Kratts episodes"""
    return await api.get_episodes(seasonNumber, limit)

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"test": "success", "timestamp": "2024-07-15"}

@app.post("/mcp")
async def handle_mcp_request(request: Request):
    """Handle MCP protocol requests via HTTP"""
    try:
        body = await request.json()
        
        # Extract method and params from MCP request
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "wild-kratts-mcp-server",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            # Return list of available tools
            tools = [
                {
                    "name": "get_wild_kratts_products",
                    "description": "Search and fetch Wild Kratts products with filtering options",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "searchTerm": {"type": "string", "description": "Search term to find products"},
                            "category": {"type": "string", "description": "Category filter"},
                            "page": {"type": "integer", "description": "Page number", "default": 1}
                        }
                    }
                },
                {
                    "name": "get_wild_kratts_episodes",
                    "description": "Fetch Wild Kratts episodes with season and limit options",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "seasonNumber": {"type": "integer", "description": "Season number to filter episodes"},
                            "limit": {"type": "integer", "description": "Maximum number of episodes to return", "default": 10}
                        }
                    }
                },
                {
                    "name": "view_location_google_maps",
                    "description": "View a specific geographical location (placeholder)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Location to view"}
                        },
                        "required": ["query"]
                    }
                }
            ]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            # Handle tool call
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "get_wild_kratts_products":
                result = await api.get_products(
                    arguments.get("searchTerm"),
                    arguments.get("category"), 
                    arguments.get("page", 1)
                )
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_wild_kratts_episodes":
                result = await api.get_episodes(
                    arguments.get("seasonNumber"),
                    arguments.get("limit", 10)
                )
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text", 
                                "text": json.dumps(result, indent=2)
                            }
                        ]
                    }
                }
            
            elif tool_name == "view_location_google_maps":
                query = arguments.get("query", "")
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Location information for: {query} (placeholder functionality)"
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if "body" in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)