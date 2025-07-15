#!/usr/bin/env python3
"""
Simple HTTP proxy for MCP over HTTPS
For use with Claude Code CLI
"""

import sys
import json
import urllib.request
import urllib.error

SERVER_URL = "https://web-production-347ab.up.railway.app/mcp"

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            
            # Create HTTP request
            req = urllib.request.Request(
                SERVER_URL,
                data=json.dumps(request).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            # Send request and get response
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read().decode()
                response_json = json.loads(response_data)
                
            # Output response
            print(json.dumps(response_json), flush=True)
            
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }
            print(json.dumps(error_response), flush=True)
            
        except urllib.error.URLError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": f"Network error: {e}"}
            }
            print(json.dumps(error_response), flush=True)
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": f"Error: {e}"}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()