"""Project-related Octopus Deploy tools."""

from .base_tools import BaseOctopusTools


class ProjectTools(BaseOctopusTools):
    """Tools for managing Octopus Deploy projects."""
    
    def setup_project_tools(self) -> None:
        """Register project-related tools with the MCP server."""
        
        @self.server.mcp.tool()
        def get_project_details(project_name: str, space_name: str = "Default") -> str:
            """Get details for a specific Octopus Deploy project.
            
            Args:
                project_name: The name of the project to retrieve
                space_name: The name of the space (default: "Default")
            """
            self.logger.info(f"Getting project details for '{project_name}' in space '{space_name}'")
            
            if not project_name:
                self.logger.error("project_name parameter is required but was not provided")
                return self._json_response({"error": "project_name is required"})
            
            # Get space by name
            space = self._get_space(space_name)
            if not space:
                return self._json_response({"error": f"Space '{space_name}' not found"})
            
            # Get project by name within the space
            self.logger.debug(f"Looking up project '{project_name}' in space '{space_name}'")
            project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
            if not project:
                self.logger.error(f"Project '{project_name}' not found in space '{space_name}'")
                return self._json_response({"error": f"Project '{project_name}' not found in space '{space_name}'"})
            
            self.logger.info(f"Found project: {project_name} (ID: {project['Id']})")
            
            # Get environments with active deployments for this project
            self.logger.debug(f"Getting active environments for project {project['Id']}")
            environments = self._get_active_environments(space['Id'], project['Id'])
            
            # Add environment message if there are no active deployments
            if not environments:
                self.logger.info(f"No active environments found for project '{project_name}', setting message")
                environments = "There is no active environment with a release for this project"
            else:
                self.logger.info(f"Found {len(environments)} active environments for project '{project_name}'")
            
            result = {
                "success": True,
                "space": {
                    "id": space.get("Id"),
                    "name": space.get("Name")
                },
                "project": {
                    "id": project.get("Id"),
                    "name": project.get("Name"),
                    "description": project.get("Description", ""),
                    "project_group_id": project.get("ProjectGroupId"),
                    "lifecycle_id": project.get("LifecycleId"),
                    "deployment_process_id": project.get("DeploymentProcessId"),
                    "variable_set_id": project.get("VariableSetId")
                },
                "active_environments": environments
            }
            
            self.logger.info(f"Successfully retrieved project details for '{project_name}'")
            return self._json_response(result, indent=2)