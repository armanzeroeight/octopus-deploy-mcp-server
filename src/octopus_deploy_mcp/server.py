"""Octopus Deploy MCP Server."""

from fastmcp import FastMCP
from typing import Dict, Any
from .tools import OctopusDeployTools
from .settings import settings


class OctopusDeployServer:
    """MCP Server for Octopus Deploy integration."""
    
    def __init__(self):
        """Initialize the Octopus Deploy server."""
        self.mcp = FastMCP("Octopus Deploy MCP Server")
        self.config = settings.octopus_deploy.__dict__
        self.tools = OctopusDeployTools(self)
    
    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.
        
        Args:
            transport: Transport type (default: stdio)
        """
        self.tools.setup_tools()
        self.mcp.run(transport=transport)