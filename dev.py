#!/usr/bin/env python3
"""Development entry point for Octopus Deploy MCP Server.

Usage:
    fastmcp dev dev.py  # Development mode with auto-reload
    python dev.py       # Standalone mode
"""

from octopus_deploy_mcp.server import OctopusDeployServer

# Create server instance for FastMCP dev command
octopus_server = OctopusDeployServer()

# Setup tools immediately for FastMCP dev command
octopus_server.tools.setup_tools()

# Expose the FastMCP instance for the dev command
server = octopus_server.mcp