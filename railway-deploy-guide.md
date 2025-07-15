# 🚀 Deploy Wild Kratts MCP Server to Railway

This guide will walk you through deploying your MCP server to Railway in minutes.

## ✅ Prerequisites

- GitHub account
- Railway account (sign up at [railway.app](https://railway.app))
- This project files

## 🔧 Project Setup (Already Done!)

Your project is already configured with:
- ✅ `server_http.py` - HTTP-enabled MCP server
- ✅ `requirements.txt` - Dependencies including FastAPI
- ✅ `railway.toml` - Railway configuration
- ✅ Health check endpoint at `/health`

## 🚀 Deploy Steps

### Step 1: Push to GitHub

```bash
# Initialize git repo (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Prepare Wild Kratts MCP Server for Railway deployment"

# Add remote (replace with your GitHub repo)
git remote add origin https://github.com/YOURUSERNAME/YOURREPO.git

# Push to GitHub
git push -u origin main
```

### Step 2: Connect to Railway

1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will automatically:
   - ✅ Detect Python
   - ✅ Install dependencies
   - ✅ Use the railway.toml configuration
   - ✅ Deploy your server!

### Step 3: Monitor Deployment

Watch the build logs in Railway dashboard:
- Build usually takes 1-2 minutes
- Look for "Deployment successful" message
- Your server will be available at: `https://your-project-name.railway.app`

## 🔗 Test Your Deployment

### Quick Health Check
```bash
curl https://your-project-name.railway.app/health
```

### Test MCP Tools
```bash
# List available tools
curl https://your-project-name.railway.app/tools

# Test products search
curl https://your-project-name.railway.app/test/products

# Test episodes query
curl https://your-project-name.railway.app/test/episodes
```

## 🌐 Your MCP Server Endpoints

Once deployed, your server provides:

| Endpoint | Description |
|----------|-------------|
| `/` | Service information |
| `/health` | Health check (for Railway) |
| `/tools` | List available MCP tools |
| `/mcp` | MCP protocol endpoint |
| `/test/products` | Test products API |
| `/test/episodes` | Test episodes API |

## 🔧 Configure MCP Client

### For Claude Desktop

Add to `~/.claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "wild-kratts-railway": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "--data-binary", "@-",
        "https://YOUR-PROJECT-NAME.railway.app/mcp"
      ]
    }
  }
}
```

### For Development/Testing

```python
import requests

# Test MCP call
response = requests.post(
    "https://your-project-name.railway.app/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_wild_kratts_products",
            "arguments": {"searchTerm": "plush"}
        }
    }
)
print(response.json())
```

## 📊 Monitor Your Server

### Railway Dashboard
- View logs: Click "View Logs" in Railway dashboard
- Monitor usage: Check metrics tab
- Environment variables: Settings → Variables

### CLI Monitoring
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs

# Check status
railway status
```

## 🔄 Update Your Server

Simply push to GitHub:
```bash
git add .
git commit -m "Update MCP server"
git push origin main
```

Railway will automatically redeploy!

## 🛠️ Troubleshooting

### Common Issues

1. **Build fails**: Check Python version in requirements.txt
2. **Health check fails**: Ensure `/health` endpoint returns 200
3. **MCP calls fail**: Check server logs for errors

### Debug Commands
```bash
# View detailed logs
railway logs --tail

# Check environment variables
railway variables

# SSH into container (if needed)
railway shell
```

## 💰 Cost

- **Free tier**: $5/month in credits
- **Usage**: ~$0.10/day for light usage
- **Scaling**: Automatic based on traffic

## 🎉 Success!

Your Wild Kratts MCP Server is now live on Railway! 

**Your server URL**: `https://your-project-name.railway.app`

The server provides:
- 🗺️ Maps functionality
- 🧸 Wild Kratts products search
- 📺 Episode information
- 🔄 Auto-updates from GitHub
- 📈 Built-in monitoring

Ready to integrate with Claude Desktop, Cursor, or any MCP-compatible client!