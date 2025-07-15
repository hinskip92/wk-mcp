# MCP Client Setup Guide

Your Wild Kratts MCP Server is now live at: `https://web-production-347ab.up.railway.app`

## 🖥️ Claude Desktop Setup

### 1. Locate Configuration File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 2. Add Server Configuration

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "node",
      "args": ["-e", "
        const https = require('https');
        const { stdin, stdout } = process;
        
        stdin.on('data', async (data) => {
          try {
            const request = JSON.parse(data.toString());
            const options = {
              hostname: 'web-production-347ab.up.railway.app',
              port: 443,
              path: '/mcp',
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(JSON.stringify(request))
              }
            };
            
            const req = https.request(options, (res) => {
              let responseData = '';
              res.on('data', (chunk) => responseData += chunk);
              res.on('end', () => {
                stdout.write(responseData + '\\n');
              });
            });
            
            req.on('error', (err) => {
              const errorResponse = {
                jsonrpc: '2.0',
                id: request.id,
                error: { code: -32603, message: err.message }
              };
              stdout.write(JSON.stringify(errorResponse) + '\\n');
            });
            
            req.write(JSON.stringify(request));
            req.end();
          } catch (err) {
            const errorResponse = {
              jsonrpc: '2.0',
              id: null,
              error: { code: -32700, message: 'Parse error' }
            };
            stdout.write(JSON.stringify(errorResponse) + '\\n');
          }
        });
      "]
    }
  }
}
```

### 3. Alternative: Python Proxy (Easier)

Create a simple Python proxy script:

```python
#!/usr/bin/env python3
# mcp_proxy.py
import sys
import json
import requests

SERVER_URL = "https://web-production-347ab.up.railway.app/mcp"

def main():
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            response = requests.post(
                SERVER_URL,
                json=request,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.ok:
                print(response.text)
            else:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32603,
                        "message": f"HTTP {response.status_code}: {response.text}"
                    }
                }
                print(json.dumps(error_response))
                
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))

if __name__ == "__main__":
    main()
```

Then configure Claude Desktop:

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "python",
      "args": ["path/to/mcp_proxy.py"]
    }
  }
}
```

## 🔧 Direct HTTP Integration

### For Custom Applications

```python
import requests

# Call your MCP server directly
def call_mcp_tool(tool_name, arguments):
    response = requests.post(
        "https://web-production-347ab.up.railway.app/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
    )
    return response.json()

# Examples
products = call_mcp_tool("get_wild_kratts_products", {"searchTerm": "plush"})
episodes = call_mcp_tool("get_wild_kratts_episodes", {"seasonNumber": 1})
```

### For JavaScript Applications

```javascript
async function callMCPTool(toolName, arguments) {
  const response = await fetch('https://web-production-347ab.up.railway.app/mcp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: arguments
      }
    })
  });
  
  return await response.json();
}

// Examples
const products = await callMCPTool('get_wild_kratts_products', { searchTerm: 'magazine' });
const episodes = await callMCPTool('get_wild_kratts_episodes', { seasonNumber: 1 });
```

## 🧪 Testing Your MCP Connection

### Test MCP Protocol Endpoints

```bash
# List available tools
curl -X POST https://web-production-347ab.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'

# Call a tool
curl -X POST https://web-production-347ab.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_wild_kratts_products",
      "arguments": {"searchTerm": "magazine"}
    }
  }'
```

## 🛠️ Alternative: Use REST Endpoints Directly

If MCP protocol is complex, you can use the REST endpoints directly:

```bash
# Direct API calls (simpler)
curl "https://web-production-347ab.up.railway.app/products?searchTerm=magazine"
curl "https://web-production-347ab.up.railway.app/episodes?seasonNumber=1"
```

## 🔄 Restart Claude Desktop

After updating the configuration:
1. Close Claude Desktop completely
2. Restart Claude Desktop
3. Your Wild Kratts server should appear in the available tools

## 🎯 Available Tools

Your MCP server provides these tools:
- `get_wild_kratts_products` - Search Wild Kratts products
- `get_wild_kratts_episodes` - Get episode information
- `view_maps` - Map functionality (placeholder)

## 🆘 Troubleshooting

### Common Issues:

1. **Configuration not loading**: Check JSON syntax in config file
2. **Connection timeout**: Increase timeout in proxy script
3. **Server not responding**: Verify server is running at Railway URL
4. **Tool not found**: Check tool names match exactly

### Debug Steps:

1. Test server directly: `curl https://web-production-347ab.up.railway.app/test`
2. Test MCP endpoint: Use curl examples above
3. Check Claude Desktop logs for errors
4. Verify configuration file path and permissions

Your Wild Kratts MCP Server is ready for integration! 🎉