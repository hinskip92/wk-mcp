# Deploy to Railway

Railway offers the easiest deployment for MCP servers with built-in git integration and automatic deployments.

## Prerequisites
- GitHub account
- Railway account (free tier available)
- Project pushed to GitHub

## Quick Deploy

### 1. Connect Repository
```bash
# Push your project to GitHub first
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/your-repo.git
git push -u origin main
```

### 2. Deploy to Railway

**Option A: Web Interface**
1. Visit [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys!

**Option B: CLI**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### 3. Configure Environment
```bash
# Set environment variables if needed
railway variables set PYTHON_VERSION=3.12
railway variables set PORT=8000
```

## Configuration Files

### railway.json
```json
{
  "deploy": {
    "numReplicas": 1,
    "sleepThreshold": "30m",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Procfile (optional)
```
web: python server.py
```

## Custom Build Configuration

### nixpacks.toml
```toml
[phases.setup]
nixPkgs = ["python312", "pip"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[phases.build]
cmds = ["echo 'Build complete'"]

[start]
cmd = "python server.py"
```

## Environment Variables
Railway automatically sets:
- `PORT` - Port to bind to
- `RAILWAY_ENVIRONMENT` - Environment name
- `RAILWAY_PROJECT_ID` - Project identifier

## Monitoring & Logs
```bash
# View logs
railway logs

# Monitor metrics
railway status

# Open deployed app
railway open
```

## Custom Domain
1. Go to Railway dashboard
2. Select your service
3. Click "Settings" → "Domains"
4. Add custom domain or use railway.app subdomain

## Scaling
```bash
# Scale replicas
railway config set replicas=3

# Upgrade plan for more resources
# Visit railway.app/pricing
```

## Troubleshooting

### Common Issues
1. **Build fails**: Check requirements.txt and Python version
2. **Port binding**: Ensure server binds to `os.environ.get("PORT", 8000)`
3. **Timeout**: Increase timeout in railway.json

### Debug Commands
```bash
railway shell  # SSH into container
railway ps     # Check running processes
railway logs --tail  # Live log streaming
```

## Cost Optimization
- **Free Tier**: $5/month in credits
- **Starter**: $5/month for more resources
- **Auto-sleep**: Apps sleep after 30min of inactivity
- **Usage-based**: Pay only for what you use

## MCP Integration
Railway works perfectly with MCP servers since they use stdio transport. Your deployed server can be accessed via:

```json
{
  "mcpServers": {
    "wild-kratts-server": {
      "command": "curl",
      "args": ["-X", "POST", "https://your-app.railway.app/mcp"],
      "env": {}
    }
  }
}
```

## Additional Features
- **Automatic HTTPS**: Free SSL certificates
- **Git Integration**: Auto-deploy on push
- **Preview Deployments**: Test branches automatically
- **Database Add-ons**: PostgreSQL, MySQL, Redis
- **Team Collaboration**: Share projects with team members

Railway is the most developer-friendly option for MCP server deployment!