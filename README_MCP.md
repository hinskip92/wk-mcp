# Wild Kratts MCP Server

A standalone Model Context Protocol (MCP) server providing Wild Kratts content and basic maps functionality.

## Features

### Available Tools

1. **Wild Kratts Products API**
   - `get_wild_kratts_products` - Search and browse Wild Kratts merchandise
   - Supports search mode (searchTerm) and browse mode (pagination)
   - Category filtering available
   - Returns products with titles, descriptions, images, and retailer links

2. **Wild Kratts Episodes API** 
   - `get_wild_kratts_episodes` - Fetch episode information
   - Filter by season, title, or featured animals
   - Field selection for efficient queries
   - Returns comprehensive episode data including creature powers and streaming links

3. **Basic Maps Tools**
   - `view_location_google_maps` - View specific locations
   - `search_google_maps` - Search for places
   - `directions_on_google_maps` - Get directions between locations
   - Returns textual confirmation (no visual maps)

## Quick Start

### Prerequisites
- Python 3.12+
- pip or Docker

### Local Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python server.py
   ```

3. **Test the server:**
   ```bash
   python test_server.py
   ```

### Docker Deployment

1. **Deploy with Docker Compose:**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop the server:**
   ```bash
   docker-compose down
   ```

## MCP Integration

### Claude Desktop Configuration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "cwd": "path/to/project",
      "env": {}
    }
  }
}
```

### Programmatic Usage

```python
from mcp.client import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Call tools
        result = await session.call_tool(
            "get_wild_kratts_products",
            {"searchTerm": "plush"}
        )
```

## API Examples

### Search Products
```python
# Search for plush toys
await session.call_tool("get_wild_kratts_products", {
    "searchTerm": "plush",
    "category": "Play"
})

# Browse products by page
await session.call_tool("get_wild_kratts_products", {
    "page": 2,
    "category": "Read"
})
```

### Query Episodes
```python
# Get all season 1 episodes
await session.call_tool("get_wild_kratts_episodes", {
    "seasonNumber": 1
})

# Search episodes featuring specific animals
await session.call_tool("get_wild_kratts_episodes", {
    "animalsFeatured": ["Lion", "Zebra"],
    "fields": ["Episode Title", "Creature Powers"]
})
```

### Maps Queries
```python
# View a location
await session.call_tool("view_location_google_maps", {
    "query": "Yellowstone National Park"
})

# Get directions
await session.call_tool("directions_on_google_maps", {
    "origin": "New York",
    "destination": "Boston"
})
```

## Architecture

- **server.py** - Main MCP server implementation using official MCP SDK
- **WildKrattsServer** - Server class handling tool definitions and API calls
- **HTTP Client** - Uses httpx for async API requests to wildkratts.com
- **Error Handling** - Comprehensive error handling with graceful fallbacks
- **Docker Support** - Containerized deployment with health checks

## Development

### Project Structure
```
├── server.py           # Main MCP server
├── test_server.py      # Test suite
├── requirements.txt    # Python dependencies
├── mcp_config.json    # MCP configuration
├── Dockerfile         # Container definition
├── docker-compose.yml # Deployment configuration
├── deploy.sh          # Deployment script
└── README_MCP.md      # This documentation
```

### Testing
Run the test suite to verify all tools work correctly:
```bash
python test_server.py
```

### Logs
When running with Docker, logs are available at:
```bash
docker-compose logs -f wild-kratts-mcp-server
```

## Troubleshooting

### Common Issues

1. **Python version errors**: Ensure Python 3.12+ is installed
2. **Network issues**: Check internet connection for API calls
3. **Permission errors**: Ensure proper file permissions on scripts
4. **Docker issues**: Verify Docker is running and accessible

### Debug Mode
Add environment variable for verbose logging:
```bash
export MCP_LOG_LEVEL=DEBUG
python server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Submit a pull request

## License

Apache 2.0 License - See project LICENSE file for details.