"""Octopus Deploy-specific MCP tools coordinator."""

from typing import TYPE_CHECKING
from .project_tools import ProjectTools
from .release_tools import ReleaseTools
from .deployment_tools import DeploymentTools

if TYPE_CHECKING:
    from ..server import OctopusDeployServer


class OctopusDeployTools:
    """Coordinator for all Octopus Deploy tool categories."""
    
    def __init__(self, server: "OctopusDeployServer"):
        self.server = server
        self.project_tools = ProjectTools(server)
        self.release_tools = ReleaseTools(server)
        self.deployment_tools = DeploymentTools(server)
    
    def setup_tools(self) -> None:
        """Register all Octopus Deploy tools with the MCP server."""
        self.project_tools.setup_project_tools()
        self.release_tools.setup_release_tools()
        self.deployment_tools.setup_deployment_tools()