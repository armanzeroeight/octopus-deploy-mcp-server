#!/usr/bin/env python3

import sys
from typing import Literal
from cyclopts import App
from .server import OctopusDeployServer

app = App(
    name="octopus-deploy-mcp",
    help="Octopus Deploy MCP Server - Interact with Octopus Deploy via Model Context Protocol",
    version="1.0.0"
)


@app.default
def main(
    transport: Literal["stdio", "http"] = "stdio",
):
    """Start the Octopus Deploy MCP server.
    
    Parameters
    ----------
    transport
        Transport mechanism to use for communication.
    """
    try:
        # Print startup message to stderr so it doesn't interfere with stdio transport
        print("Starting Octopus Deploy MCP Server...", file=sys.stderr)
        print(f"Transport: {transport}", file=sys.stderr)
        
        # Create and run the server
        octopus_server = OctopusDeployServer()
        octopus_server.run(transport=transport)
        
    except KeyboardInterrupt:
        print("\nShutting down Octopus Deploy MCP Server...", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    app()