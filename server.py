#!/usr/bin/env python3
"""
Wild Kratts MCP Server
A standalone MCP server providing Wild Kratts content and basic maps functionality.
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Union
import httpx
from urllib.parse import quote

# MCP imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    LoggingLevel
)
import mcp.types as types


class WildKrattsServer:
    def __init__(self):
        self.server = Server("wild-kratts-mcp-server")
        self.base_url = "https://wildkratts.com/wp-json"
        self.episodes_api = f"{self.base_url}/wild-kratts/v1/episodes"
        self.products_api = f"{self.base_url}/wp/v2/products"
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            return [
                Tool(
                    name="view_location_google_maps",
                    description="View a specific geographical location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Location to view"
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="search_google_maps", 
                    description="Search for places near a location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "search": {
                                "type": "string", 
                                "description": "Search query for places"
                            }
                        },
                        "required": ["search"]
                    }
                ),
                Tool(
                    name="directions_on_google_maps",
                    description="Get directions from origin to destination",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "origin": {
                                "type": "string",
                                "description": "Starting location"
                            },
                            "destination": {
                                "type": "string", 
                                "description": "Destination location"
                            }
                        },
                        "required": ["origin", "destination"]
                    }
                ),
                Tool(
                    name="get_wild_kratts_products",
                    description="Fetch Wild Kratts products with search and filtering capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "searchTerm": {
                                "type": "string",
                                "description": "Search term to find products"
                            },
                            "category": {
                                "type": "string",
                                "description": "Product category filter"
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number for pagination",
                                "default": 1
                            }
                        }
                    }
                ),
                Tool(
                    name="get_wild_kratts_episodes",
                    description="Fetch Wild Kratts episodes with filtering options",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "seasonNumber": {
                                "type": "integer",
                                "description": "Filter by season number"
                            },
                            "episodeTitle": {
                                "type": "string",
                                "description": "Filter by episode title (partial match)"
                            },
                            "animalsFeatured": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Filter by animals featured"
                            },
                            "fields": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Specific fields to return for efficiency"
                            }
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
            """Handle tool calls"""
            
            if name == "view_location_google_maps":
                query = arguments.get("query", "")
                return [TextContent(
                    type="text",
                    text=f"Information for location: {query} would be processed."
                )]
                
            elif name == "search_google_maps":
                search = arguments.get("search", "")
                return [TextContent(
                    type="text", 
                    text=f"Search results for: {search} would be processed."
                )]
                
            elif name == "directions_on_google_maps":
                origin = arguments.get("origin", "")
                destination = arguments.get("destination", "")
                return [TextContent(
                    type="text",
                    text=f"Directions from {origin} to {destination} would be processed."
                )]
                
            elif name == "get_wild_kratts_products":
                return await self._handle_get_products(arguments)
                
            elif name == "get_wild_kratts_episodes":
                return await self._handle_get_episodes(arguments)
                
            else:
                raise ValueError(f"Unknown tool: {name}")

    async def _handle_get_products(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle Wild Kratts products API calls"""
        search_term = arguments.get("searchTerm")
        category = arguments.get("category")
        page = arguments.get("page", 1)
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
                
                return [TextContent(type="text", text=json.dumps(result))]
                
        except Exception as error:
            error_result = {
                'error': f"Error fetching products: {str(error)}",
                'products': [],
                'pagination': {
                    'currentPage': page if not search_term else 1,
                    'totalItems': 0,
                    'totalPages': 0,
                    'itemsPerPage': per_page
                }
            }
            return [TextContent(type="text", text=json.dumps(error_result))]

    async def _handle_get_episodes(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """Handle Wild Kratts episodes API calls"""
        season_number = arguments.get("seasonNumber")
        episode_title = arguments.get("episodeTitle")
        animals_featured = arguments.get("animalsFeatured", [])
        fields = arguments.get("fields", [])
        
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
                
                return [TextContent(type="text", text=json.dumps(filtered_episodes))]
                
        except Exception as error:
            error_result = {'error': f"Error fetching episodes: {str(error)}"}
            return [TextContent(type="text", text=json.dumps(error_result))]

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="wild-kratts-mcp-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )


async def main():
    """Main entry point"""
    server = WildKrattsServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())