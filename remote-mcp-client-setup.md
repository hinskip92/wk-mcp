# Remote MCP Client Setup

Connect your MCP client directly to your Railway deployment: `https://web-production-347ab.up.railway.app`

## 🌐 Method 1: Direct HTTP MCP Bridge (Recommended)

### Claude Desktop Configuration

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "node",
      "args": [
        "-e",
        "const https = require('https'); const { stdin, stdout } = process; stdin.on('data', async (data) => { try { const request = JSON.parse(data.toString()); const postData = JSON.stringify(request); const options = { hostname: 'web-production-347ab.up.railway.app', port: 443, path: '/mcp', method: 'POST', headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(postData) } }; const req = https.request(options, (res) => { let responseData = ''; res.on('data', (chunk) => responseData += chunk); res.on('end', () => { try { const response = JSON.parse(responseData); stdout.write(JSON.stringify(response) + '\\n'); } catch (e) { stdout.write(JSON.stringify({jsonrpc: '2.0', id: request.id, error: {code: -32603, message: 'Invalid response'}}) + '\\n'); } }); }); req.on('error', (err) => { stdout.write(JSON.stringify({jsonrpc: '2.0', id: request.id, error: {code: -32603, message: err.message}}) + '\\n'); }); req.write(postData); req.end(); } catch (err) { stdout.write(JSON.stringify({jsonrpc: '2.0', id: null, error: {code: -32700, message: 'Parse error'}}) + '\\n'); } });"
      ]
    }
  }
}
```

## 🐍 Method 2: Python HTTP Bridge

### Create Remote Bridge Script

Save this as a one-liner in your Claude Desktop config:

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "python",
      "args": [
        "-c",
        "import sys, json, urllib.request, urllib.parse; [print(json.dumps((lambda r: {'jsonrpc': '2.0', 'id': r.get('id'), 'result': json.loads(urllib.request.urlopen(urllib.request.Request('https://web-production-347ab.up.railway.app/mcp', data=json.dumps(r).encode(), headers={'Content-Type': 'application/json'})).read())['result']} if r.get('method') else {'jsonrpc': '2.0', 'id': r.get('id'), 'error': {'code': -32601, 'message': 'Method not found'}})(json.loads(line.strip()))) for line in sys.stdin if line.strip()]"
      ]
    }
  }
}
```

## 🔧 Method 3: cURL-based MCP Bridge

### Using cURL (Cross-platform)

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "bash",
      "args": [
        "-c",
        "while read line; do curl -s -X POST https://web-production-347ab.up.railway.app/mcp -H 'Content-Type: application/json' -d \"$line\"; done"
      ]
    }
  }
}
```

## 🚀 Method 4: Universal Remote MCP Client

### For any MCP Client

Use this generic approach that works with any MCP client:

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "npx",
      "args": [
        "--yes",
        "@modelcontextprotocol/create-mcp-proxy",
        "https://web-production-347ab.up.railway.app/mcp"
      ]
    }
  }
}
```

## 🌍 Method 5: Environment Variable Configuration

### Set Server URL as Environment Variable

```bash
# Windows
set MCP_SERVER_URL=https://web-production-347ab.up.railway.app/mcp

# macOS/Linux
export MCP_SERVER_URL=https://web-production-347ab.up.railway.app/mcp
```

Then use in config:
```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "python",
      "args": [
        "-c",
        "import os, sys, json, urllib.request; url = os.environ.get('MCP_SERVER_URL', 'https://web-production-347ab.up.railway.app/mcp'); [print(json.dumps(json.loads(urllib.request.urlopen(urllib.request.Request(url, data=json.dumps(json.loads(line.strip())).encode(), headers={'Content-Type': 'application/json'})).read()))) for line in sys.stdin if line.strip()]"
      ]
    }
  }
}
```

## 📋 Test Your Remote Connection

### Test MCP Protocol Directly

```bash
# Test tools/list
curl -X POST https://web-production-347ab.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'

# Test tools/call
curl -X POST https://web-production-347ab.up.railway.app/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_wild_kratts_products", "arguments": {"searchTerm": "magazine"}}}'
```

## 🔄 Restart Claude Desktop

After updating the configuration:
1. Close Claude Desktop completely
2. Restart Claude Desktop
3. Your Wild Kratts server should appear as a remote tool

## 🎯 Available Remote Tools

Your remote MCP server provides:
- `get_wild_kratts_products` - Search Wild Kratts products
- `get_wild_kratts_episodes` - Get episode information
- `view_maps` - Map functionality (placeholder)

## 🆘 Troubleshooting Remote Connection

### Common Issues:

1. **Network connectivity**: Ensure Railway server is accessible
2. **HTTPS certificate**: Modern clients require valid SSL
3. **Request timeout**: Railway may have cold start delays
4. **Rate limiting**: Railway free tier has usage limits

### Debug Steps:

1. Test server health: `curl https://web-production-347ab.up.railway.app/health`
2. Test MCP endpoint: Use curl examples above
3. Check network connectivity to Railway
4. Verify Claude Desktop logs for connection errors

### Railway-Specific Considerations:

- **Cold starts**: First request may be slow
- **Auto-sleep**: Free tier apps sleep after 30 minutes
- **Rate limits**: Free tier has usage restrictions
- **SSL required**: All connections must use HTTPS

Your **Wild Kratts MCP Server is fully remote and ready for client connections!** 🎉

No local files needed - everything connects directly to Railway!