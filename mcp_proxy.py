#!/usr/bin/env python3
"""
MCP Proxy for Wild Kratts Server
Converts stdio MCP protocol to HTTP calls for Railway deployment
"""

import sys
import json
import requests
import time

SERVER_URL = "https://web-production-347ab.up.railway.app/mcp"

def log_debug(message):
    """Log debug messages to stderr"""
    print(f"[MCP-PROXY] {message}", file=sys.stderr)

def handle_tools_list(request_id):
    """Handle tools/list method"""
    try:
        response = requests.post(
            SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/list",
                "params": {}
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.ok:
            return response.json()
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
            }
            
    except Exception as e:
        log_debug(f"Error in tools/list: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Request failed: {str(e)}"
            }
        }

def handle_tools_call(request_id, tool_name, arguments):
    """Handle tools/call method"""
    try:
        response = requests.post(
            SERVER_URL,
            json={
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.ok:
            return response.json()
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
            }
            
    except Exception as e:
        log_debug(f"Error in tools/call: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Request failed: {str(e)}"
            }
        }

def handle_initialize(request_id):
    """Handle initialize method"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "wild-kratts-mcp-server",
                "version": "1.0.0"
            }
        }
    }

def main():
    """Main proxy loop"""
    log_debug("Starting Wild Kratts MCP Proxy")
    log_debug(f"Server URL: {SERVER_URL}")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                log_debug(f"Received request: {request.get('method', 'unknown')}")
                
                method = request.get("method")
                request_id = request.get("id")
                params = request.get("params", {})
                
                if method == "initialize":
                    response = handle_initialize(request_id)
                    
                elif method == "tools/list":
                    response = handle_tools_list(request_id)
                    
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    response = handle_tools_call(request_id, tool_name, arguments)
                    
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                # Send response to stdout
                print(json.dumps(response), flush=True)
                log_debug(f"Sent response for: {method}")
                
            except json.JSONDecodeError as e:
                log_debug(f"JSON decode error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
            except Exception as e:
                log_debug(f"Unexpected error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        log_debug("Proxy interrupted by user")
    except Exception as e:
        log_debug(f"Fatal error: {e}")
        
    log_debug("MCP Proxy stopped")

if __name__ == "__main__":
    main()