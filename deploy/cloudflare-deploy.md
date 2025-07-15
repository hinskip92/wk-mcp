# Deploy to Cloudflare Workers

Cloudflare offers official remote MCP server hosting with global edge deployment and enterprise-grade performance.

## Prerequisites
- Cloudflare account (free tier available)
- Node.js 18+ (for Wrangler CLI)
- MCP server adapted for Workers runtime

## Setup Wrangler CLI

```bash
# Install Wrangler
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

## Project Configuration

### wrangler.toml
```toml
name = "wild-kratts-mcp-server"
main = "src/worker.js"
compatibility_date = "2024-07-14"
compatibility_flags = ["nodejs_compat"]

[env.production]
name = "wild-kratts-mcp-server-prod"

[vars]
ENVIRONMENT = "production"

[[kv_namespaces]]
binding = "MCP_CACHE"
id = "your-kv-namespace-id"
preview_id = "your-preview-kv-id"
```

## Worker Implementation

### src/worker.js
```javascript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { Transport } from '@modelcontextprotocol/sdk/shared/transport.js';

export default {
  async fetch(request, env, ctx) {
    // Handle MCP requests
    if (request.method === 'POST' && request.url.endsWith('/mcp')) {
      return handleMcpRequest(request, env);
    }
    
    // Health check
    if (request.method === 'GET') {
      return new Response(JSON.stringify({
        status: 'healthy',
        server: 'Wild Kratts MCP Server',
        version: '1.0.0'
      }), {
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    return new Response('Not Found', { status: 404 });
  }
};

async function handleMcpRequest(request, env) {
  try {
    const mcpServer = new McpServer({
      name: 'wild-kratts-cloudflare-server',
      version: '1.0.0'
    });
    
    // Define tools
    mcpServer.tool(
      'get_wild_kratts_products',
      'Fetch Wild Kratts products',
      { searchTerm: z.string().optional() },
      async ({ searchTerm }) => {
        const response = await fetch('https://wildkratts.com/wp-json/wp/v2/products');
        const products = await response.json();
        // Filter and return products
        return { content: [{ type: 'text', text: JSON.stringify(products) }] };
      }
    );
    
    // Process MCP request
    const body = await request.json();
    const result = await mcpServer.handleRequest(body);
    
    return new Response(JSON.stringify(result), {
      headers: { 'Content-Type': 'application/json' }
    });
    
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
```

## Convert Python to Workers

Since Cloudflare Workers use JavaScript/TypeScript, convert your Python MCP server:

### package.json
```json
{
  "name": "wild-kratts-mcp-worker",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.11.4",
    "zod": "^3.25.7"
  },
  "devDependencies": {
    "wrangler": "^3.0.0"
  }
}
```

## Deployment

### Deploy to Cloudflare
```bash
# Install dependencies
npm install

# Deploy to production
wrangler deploy

# Deploy with custom name
wrangler deploy --name wild-kratts-mcp-prod

# Deploy to staging
wrangler deploy --env staging
```

## Environment Variables
```bash
# Set environment variables
wrangler secret put API_KEY
wrangler secret put WEBHOOK_SECRET

# List secrets
wrangler secret list
```

## Custom Domains

### Add Domain
```bash
# Add custom domain
wrangler domain add your-domain.com

# List domains
wrangler domain list
```

### DNS Configuration
```toml
# In wrangler.toml
[env.production]
routes = [
  { pattern = "mcp.your-domain.com/*", zone_name = "your-domain.com" }
]
```

## Remote MCP Configuration

### Claude Desktop Config
```json
{
  "mcpServers": {
    "wild-kratts-cloudflare": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-H", "Authorization: Bearer YOUR_TOKEN",
        "--data-binary", "@-",
        "https://your-worker.your-subdomain.workers.dev/mcp"
      ]
    }
  }
}
```

## Authentication & Security

### API Key Authentication
```javascript
// In worker.js
async function authenticate(request) {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid authorization header');
  }
  
  const token = authHeader.substring(7);
  // Validate token against your auth system
  return validateToken(token);
}
```

### Rate Limiting
```javascript
// Rate limiting with KV storage
async function checkRateLimit(clientId, env) {
  const key = `rate_limit:${clientId}`;
  const current = await env.MCP_CACHE.get(key);
  
  if (current && parseInt(current) > 100) {
    throw new Error('Rate limit exceeded');
  }
  
  await env.MCP_CACHE.put(key, (parseInt(current) || 0) + 1, {
    expirationTtl: 3600 // 1 hour
  });
}
```

## Monitoring & Analytics

### Wrangler Analytics
```bash
# View analytics
wrangler analytics

# Tail logs in real-time
wrangler tail

# View deployment history
wrangler deployments list
```

### Custom Metrics
```javascript
// In worker.js
export default {
  async fetch(request, env, ctx) {
    const start = Date.now();
    
    try {
      const response = await handleRequest(request, env);
      
      // Log metrics
      ctx.waitUntil(
        logMetrics(env, {
          status: response.status,
          duration: Date.now() - start,
          path: new URL(request.url).pathname
        })
      );
      
      return response;
    } catch (error) {
      // Log errors
      ctx.waitUntil(logError(env, error));
      throw error;
    }
  }
};
```

## Cost & Limits

### Free Tier
- **100,000 requests/day**
- **10ms CPU time per request**
- **128MB memory**
- **Global edge deployment**

### Paid Plans
- **Workers Paid**: $5/month for 10M requests
- **Workers Unbound**: $0.50/million requests
- **Enterprise**: Custom pricing with SLA

## Advantages of Cloudflare

1. **Global Edge**: Deploy to 200+ locations worldwide
2. **Zero Cold Starts**: Workers start instantly
3. **Official MCP Support**: Built for remote MCP servers
4. **Enterprise Security**: DDoS protection, WAF included
5. **Unlimited Bandwidth**: No data transfer charges
6. **99.99% Uptime**: Enterprise-grade reliability

## Troubleshooting

### Common Issues
```bash
# Debug locally
wrangler dev --local

# Check logs
wrangler tail --format pretty

# Validate configuration
wrangler validate
```

### Performance Tips
- Use KV storage for caching
- Implement request deduplication
- Use Durable Objects for stateful operations
- Optimize bundle size with tree-shaking

Cloudflare Workers provide the most scalable and performant option for remote MCP server hosting!