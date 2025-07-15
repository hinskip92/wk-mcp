# Deploy to Render

Render provides the simplest Python deployment with zero configuration required and excellent FastAPI support.

## Prerequisites
- GitHub account
- Render account (free tier available)
- Python MCP server in GitHub repository

## Quick Deploy (Web Interface)

### 1. Connect Repository
1. Visit [render.com](https://render.com)
2. Sign up/login with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Render auto-detects Python!

### 2. Configure Service

**Basic Settings:**
- **Name**: `wild-kratts-mcp-server`
- **Region**: `Oregon (US West)` or closest to you
- **Branch**: `main`
- **Runtime**: `Python 3` (auto-detected)

**Build & Deploy:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python server.py`

### 3. Environment Variables
Add these in Render dashboard:
```
PYTHON_VERSION=3.12.4
PORT=10000
ENVIRONMENT=production
```

## Advanced Configuration

### render.yaml (Infrastructure as Code)
```yaml
services:
  - type: web
    name: wild-kratts-mcp-server
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python server.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.4
      - key: ENVIRONMENT
        value: production
    autoDeploy: true
    repo: https://github.com/yourusername/your-repo.git
    branch: main
```

### Update server.py for Render
```python
import os

# Render requires binding to 0.0.0.0 and PORT env var
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    # For HTTP server (if needed for health checks)
    # app.run(host="0.0.0.0", port=port)
    
    # For MCP server (stdio-based)
    asyncio.run(main())
```

## Custom Domain

### Free Subdomain
Render provides: `your-service-name.onrender.com`

### Custom Domain (Paid plans)
1. Go to service dashboard
2. Click "Settings" → "Custom Domains"
3. Add your domain
4. Update DNS records:
```
CNAME: your-domain.com → your-service.onrender.com
```

## Database Integration

### Add PostgreSQL
```yaml
# In render.yaml
databases:
  - name: wild-kratts-db
    plan: free
    databaseName: wild_kratts
    user: admin

services:
  - type: web
    # ... other config
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: wild-kratts-db
          property: connectionString
```

### Add Redis
```yaml
# In render.yaml  
services:
  - type: redis
    name: wild-kratts-cache
    plan: free
    maxmemoryPolicy: allkeys-lru
```

## Health Checks

### Add Health Endpoint
```python
# In server.py
from fastapi import FastAPI
import asyncio

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Wild Kratts MCP Server"}

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    # Handle MCP requests if needed
    pass

# Run both FastAPI and MCP server
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    
    # Option 1: HTTP server only
    uvicorn.run(app, host="0.0.0.0", port=port)
    
    # Option 2: Both HTTP and MCP (requires threading)
    # import threading
    # mcp_thread = threading.Thread(target=lambda: asyncio.run(main()))
    # mcp_thread.start()
    # uvicorn.run(app, host="0.0.0.0", port=port)
```

## Monitoring & Logs

### View Logs
```bash
# Install Render CLI
npm install -g @render/cli

# Login and view logs
render login
render logs --service-id srv-xxxxx --tail
```

### Web Interface
1. Go to service dashboard
2. Click "Logs" tab
3. Use filters and search

## Deployment Options

### Manual Deploy
```bash
# Using Render CLI
render deploy --service-id srv-xxxxx

# Or trigger via Git
git push origin main  # Auto-deploys if enabled
```

### Deploy from CLI
```bash
# Create new service
render create-service \
  --type web \
  --name wild-kratts-mcp \
  --env python \
  --repo https://github.com/user/repo \
  --branch main \
  --build-command "pip install -r requirements.txt" \
  --start-command "python server.py"
```

## Auto-Deploy Configuration

### GitHub Integration
1. Connect GitHub account
2. Enable "Auto-Deploy" in service settings
3. Choose branches to auto-deploy
4. Optional: Deploy previews for PRs

### Deploy Hooks
```bash
# Webhook URL for external triggers
curl -X POST https://api.render.com/deploy/srv-xxxxx?key=your-key
```

## Environment Management

### Multiple Environments
```yaml
# render.yaml with multiple services
services:
  - type: web
    name: wild-kratts-mcp-staging
    env: python
    # ... staging config
    
  - type: web
    name: wild-kratts-mcp-production
    env: python
    # ... production config
```

### Secrets Management
```bash
# Set environment variables via CLI
render config set --service-id srv-xxxxx KEY=value

# Or use dashboard Environment tab
```

## Scaling & Performance

### Scaling Options
- **Free**: 1 instance, 512MB RAM, shared CPU
- **Starter**: $7/month, 1GB RAM, shared CPU
- **Standard**: $25/month, 2GB RAM, 1 CPU
- **Pro**: $85/month, 4GB RAM, 2 CPU

### Auto-Scaling (Paid plans)
```yaml
# In render.yaml
services:
  - type: web
    # ... other config
    scaling:
      minInstances: 1
      maxInstances: 10
      targetCPUPercent: 70
```

## Cost Optimization

### Free Tier Benefits
- **750 hours/month** free compute
- **100GB bandwidth/month**
- **PostgreSQL database** (90 days, then $7/month)
- **Static sites** unlimited

### Sleep Mode
Free services sleep after 15 minutes of inactivity:
```python
# Keep-alive ping (if needed)
import requests
import schedule
import time

def ping_service():
    requests.get("https://your-service.onrender.com/health")

schedule.every(10).minutes.do(ping_service)
```

## Troubleshooting

### Common Issues

1. **Build Failures**
```bash
# Check Python version
python --version

# Verify requirements.txt
pip install -r requirements.txt

# Check build logs in dashboard
```

2. **Port Binding**
```python
# Ensure server binds to correct port
port = int(os.environ.get("PORT", 8000))
```

3. **Memory Limits**
```python
# Optimize memory usage
import gc
gc.collect()  # Force garbage collection
```

### Debug Commands
```bash
# SSH into container (paid plans only)
render ssh --service-id srv-xxxxx

# Download logs
render logs --service-id srv-xxxxx --download
```

## MCP Integration

### For HTTP-based MCP
```json
{
  "mcpServers": {
    "wild-kratts-render": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "--data-binary", "@-",
        "https://your-service.onrender.com/mcp"
      ]
    }
  }
}
```

### For stdio MCP (Local proxy)
```python
# proxy_server.py - Run locally to bridge HTTP to stdio
import subprocess
import requests

def proxy_mcp_request(data):
    # Forward to Render service
    response = requests.post(
        "https://your-service.onrender.com/mcp",
        json=data
    )
    return response.json()
```

## Backup & Monitoring

### Database Backups (Paid plans)
```bash
# Automatic daily backups enabled
# Manual backup
render db backup --database-id databaseid
```

### Uptime Monitoring
Use Render's built-in monitoring or external services:
- UptimeRobot
- Pingdom  
- StatusPage

Render provides the simplest deployment experience with excellent Python support and generous free tier!