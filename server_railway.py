#!/usr/bin/env python3
"""
Wild Kratts MCP Server optimized for Railway deployment
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

# FastAPI app for Railway deployment
app = FastAPI(
    title="Wild Kratts MCP Server",
    description="MCP server providing Wild Kratts content and basic maps functionality",
    version="1.0.0"
)

class WildKrattsAPI:
    def __init__(self):
        self.base_url = "https://wildkratts.com/wp-json"
        self.episodes_api = f"{self.base_url}/wild-kratts/v1/episodes"
        self.products_api = f"{self.base_url}/wp/v2/products"
    
    async def get_products(self, search_term: str = None, category: str = None, page: int = 1) -> dict:
        """Fetch Wild Kratts products"""
        per_page = 100
        
        try:
            async with httpx.AsyncClient() as client:
                if search_term:
                    # Search mode - fetch all pages and filter
                    matching_products = []
                    current_page = 1
                    total_pages = 1
                    
                    while current_page <= total_pages and len(matching_products) < per_page:
                        url = f"{self.products_api}?per_page={per_page}&page={current_page}"
                        response = await client.get(url)
                        
                        if not response.is_success:
                            if current_page == 1:
                                raise Exception(f"API request failed with status {response.status_code}")
                            break
                            
                        if current_page == 1:
                            total_pages = int(response.headers.get('X-WP-TotalPages', '1'))
                            
                        products = response.json()
                        if not products:
                            break
                            
                        # Filter by search term
                        search_lower = search_term.lower()
                        for product in products:
                            title_match = search_lower in product.get('title', {}).get('rendered', '').lower()
                            desc = product.get('description', '')
                            # Strip HTML tags for description search
                            import re
                            clean_desc = re.sub(r'<[^>]*>', '', desc).lower()
                            desc_match = search_lower in clean_desc
                            
                            if title_match or desc_match:
                                # Apply category filter if provided
                                if category:
                                    categories = product.get('product_categories', [])
                                    if not any(category.lower() in cat.lower() for cat in categories):
                                        continue
                                        
                                matching_products.append({
                                    'id': product.get('id'),
                                    'link': product.get('link'),
                                    'title': product.get('title'),
                                    'description': product.get('description'),
                                    'featured_image': product.get('featured_image'),
                                    'product_categories': product.get('product_categories'),
                                    'retailers': product.get('retailers')
                                })
                                
                                if len(matching_products) >= per_page:
                                    break
                        
                        current_page += 1
                    
                    result = {
                        'products': matching_products[:per_page],
                        'pagination': {
                            'currentPage': 1,
                            'totalItems': len(matching_products),
                            'totalPages': max(1, (len(matching_products) + per_page - 1) // per_page),
                            'itemsPerPage': per_page
                        }
                    }
                    
                else:
                    # Browse mode - standard pagination
                    url = f"{self.products_api}?per_page={per_page}&page={page}"
                    response = await client.get(url)
                    
                    if not response.is_success:
                        raise Exception(f"API request failed with status {response.status_code}")
                    
                    total_items = int(response.headers.get('X-WP-Total', '0'))
                    total_pages = int(response.headers.get('X-WP-TotalPages', '0'))
                    
                    products = response.json() or []
                    
                    # Apply category filter if provided
                    if category:
                        filtered_products = []
                        for product in products:
                            categories = product.get('product_categories', [])
                            if any(category.lower() in cat.lower() for cat in categories):
                                filtered_products.append({
                                    'id': product.get('id'),
                                    'link': product.get('link'),
                                    'title': product.get('title'),
                                    'description': product.get('description'),
                                    'featured_image': product.get('featured_image'),
                                    'product_categories': product.get('product_categories'),
                                    'retailers': product.get('retailers')
                                })
                        products = filtered_products
                    else:
                        products = [{
                            'id': product.get('id'),
                            'link': product.get('link'),
                            'title': product.get('title'),
                            'description': product.get('description'),
                            'featured_image': product.get('featured_image'),
                            'product_categories': product.get('product_categories'),
                            'retailers': product.get('retailers')
                        } for product in products]
                    
                    result = {
                        'products': products,
                        'pagination': {
                            'currentPage': page,
                            'totalItems': total_items,
                            'totalPages': total_pages,
                            'itemsPerPage': per_page
                        }
                    }
                
                return result
                
        except Exception as error:
            return {
                'error': f"Error fetching products: {str(error)}",
                'products': [],
                'pagination': {
                    'currentPage': page if not search_term else 1,
                    'totalItems': 0,
                    'totalPages': 0,
                    'itemsPerPage': per_page
                }
            }

    async def get_episodes(self, season_number: int = None, episode_title: str = None, 
                          animals_featured: List[str] = None, fields: List[str] = None) -> dict:
        """Fetch Wild Kratts episodes"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.episodes_api)
                
                if not response.is_success:
                    raise Exception(f"API request failed with status {response.status_code}")
                
                episodes = response.json() or []
                
                # Apply filters
                filtered_episodes = episodes
                
                if season_number is not None:
                    filtered_episodes = [ep for ep in filtered_episodes if ep.get('Season') == season_number]
                
                if episode_title:
                    title_lower = episode_title.lower()
                    filtered_episodes = [ep for ep in filtered_episodes 
                                       if title_lower in ep.get('Episode Title', '').lower()]
                
                if animals_featured:
                    def episode_has_animals(episode, required_animals):
                        episode_animals = episode.get('Animals Featured', [])
                        if not isinstance(episode_animals, list):
                            return False
                        episode_animals_lower = [animal.lower() for animal in episode_animals]
                        return all(
                            any(req_animal.lower() in ep_animal for ep_animal in episode_animals_lower)
                            for req_animal in required_animals
                        )
                    
                    filtered_episodes = [ep for ep in filtered_episodes 
                                       if episode_has_animals(ep, animals_featured)]
                
                # Apply field selection if specified
                if fields:
                    valid_fields = [
                        "Season", "Episode Number (Broadcast Order)", "Episode Number (Internal)",
                        "Episode Title", "Air Date", "imagePath", "Summary", "Animals Featured",
                        "Creature Powers", "Locations", "streamingUrls"
                    ]
                    valid_requested_fields = [f for f in fields if f in valid_fields]
                    
                    if valid_requested_fields:
                        filtered_episodes = [
                            {field: ep.get(field) for field in valid_requested_fields}
                            for ep in filtered_episodes
                        ]
                
                return {"episodes": filtered_episodes}
                
        except Exception as error:
            return {'error': f"Error fetching episodes: {str(error)}"}

# Initialize API
api = WildKrattsAPI()

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
            "tools": "/tools",
            "products": "/products",
            "episodes": "/episodes"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "service": "Wild Kratts MCP Server"}

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

@app.get("/products")
async def get_products(searchTerm: str = None, category: str = None, page: int = 1):
    """Get Wild Kratts products"""
    result = await api.get_products(searchTerm, category, page)
    return result

@app.get("/episodes")
async def get_episodes(seasonNumber: int = None, episodeTitle: str = None, 
                      animalsFeatured: str = None, fields: str = None):
    """Get Wild Kratts episodes"""
    # Parse comma-separated strings to lists
    animals_list = animalsFeatured.split(',') if animalsFeatured else None
    fields_list = fields.split(',') if fields else None
    
    result = await api.get_episodes(seasonNumber, episodeTitle, animals_list, fields_list)
    return result

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
    """Handle tool calls"""
    
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
        result = await api.get_products(
            arguments.get("searchTerm"),
            arguments.get("category"), 
            arguments.get("page", 1)
        )
        return [{"type": "text", "text": json.dumps(result)}]
        
    elif name == "get_wild_kratts_episodes":
        result = await api.get_episodes(
            arguments.get("seasonNumber"),
            arguments.get("episodeTitle"),
            arguments.get("animalsFeatured"),
            arguments.get("fields")
        )
        return [{"type": "text", "text": json.dumps(result)}]
        
    else:
        raise ValueError(f"Unknown tool: {name}")

# Test endpoints
@app.get("/test/products")
async def test_products():
    """Test endpoint for products"""
    try:
        result = await api.get_products("plush")
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/test/episodes")
async def test_episodes():
    """Test endpoint for episodes"""
    try:
        result = await api.get_episodes(season_number=1, fields=["Episode Title"])
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

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