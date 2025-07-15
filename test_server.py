#!/usr/bin/env python3
"""
Test script for Wild Kratts MCP Server
"""

import asyncio
import json
import subprocess
import sys
from mcp.client import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server functionality"""
    
    print("🧪 Testing Wild Kratts MCP Server...")
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                print("✅ Server connection established")
                
                # List available tools
                tools = await session.list_tools()
                print(f"📋 Available tools: {len(tools.tools)}")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test 1: Get Wild Kratts products
                print("\n🧸 Testing product search...")
                try:
                    result = await session.call_tool(
                        "get_wild_kratts_products",
                        {"searchTerm": "plush"}
                    )
                    
                    if result.content and len(result.content) > 0:
                        response_data = json.loads(result.content[0].text)
                        products = response_data.get('products', [])
                        print(f"✅ Found {len(products)} plush products")
                        if products:
                            print(f"   Example: {products[0].get('title', {}).get('rendered', 'N/A')}")
                    else:
                        print("❌ No products returned")
                        
                except Exception as e:
                    print(f"❌ Product search failed: {e}")
                
                # Test 2: Get Wild Kratts episodes
                print("\n📺 Testing episode search...")
                try:
                    result = await session.call_tool(
                        "get_wild_kratts_episodes",
                        {"seasonNumber": 1, "fields": ["Episode Title", "Animals Featured"]}
                    )
                    
                    if result.content and len(result.content) > 0:
                        episodes = json.loads(result.content[0].text)
                        print(f"✅ Found {len(episodes)} episodes from season 1")
                        if episodes:
                            print(f"   Example: {episodes[0].get('Episode Title', 'N/A')}")
                    else:
                        print("❌ No episodes returned")
                        
                except Exception as e:
                    print(f"❌ Episode search failed: {e}")
                
                # Test 3: Maps functionality
                print("\n🗺️ Testing maps functionality...")
                try:
                    result = await session.call_tool(
                        "view_location_google_maps",
                        {"query": "Yellowstone National Park"}
                    )
                    
                    if result.content and len(result.content) > 0:
                        print(f"✅ Maps tool responded: {result.content[0].text}")
                    else:
                        print("❌ No maps response")
                        
                except Exception as e:
                    print(f"❌ Maps test failed: {e}")
                
                print("\n🎉 MCP Server testing completed!")
                
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False
    
    return True


async def main():
    """Main test function"""
    success = await test_mcp_server()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())