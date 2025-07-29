"""Deployment-related Octopus Deploy tools."""

from typing import Optional
from .base_tools import BaseOctopusTools


class DeploymentTools(BaseOctopusTools):
    """Tools for managing Octopus Deploy deployments."""
    
    def setup_deployment_tools(self) -> None:
        """Register deployment-related tools with the MCP server."""
        
        @self.server.mcp.tool()
        def deploy_release(project_name: str, environment_name: str, release_version: str = None, space_name: str = "Default") -> str:
            """Deploy a release to an environment for a specific project.
            
            Args:
                project_name: The name of the project to deploy
                environment_name: The name of the environment to deploy to
                release_version: The version of the release to deploy (optional, uses latest if not specified)
                space_name: The name of the space to deploy in (optional, defaults to "Default")
            """
            self.logger.info(f"Starting deployment for project '{project_name}' to environment '{environment_name}' in space '{space_name}'")
            
            if not project_name or not environment_name:
                self.logger.error("Missing required parameters: project_name and environment_name")
                return self._error_response("project_name and environment_name are required")
            
            # Get space by name
            space = self._get_space(space_name)
            if not space:
                return self._json_response({"error": f"Space '{space_name}' not found"})
            
            self.logger.debug(f"Looking up project '{project_name}' in space '{space_name}'")
            project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
            if not project:
                self.logger.error(f"Project '{project_name}' not found in space '{space_name}'")
                return self._error_response(f"Project '{project_name}' not found in {space_name} space")
            
            space_id = space["Id"]
            self.logger.debug(f"Using space ID: {space_id}")
            
            # Get releases
            self.logger.debug(f"Fetching releases for project '{project_name}'")
            releases_response = self._get_project_releases(space_id, project["Id"])
            if "error" in releases_response:
                self.logger.error(f"Failed to get releases for project '{project_name}': {releases_response.get('error')}")
                return self._json_response(releases_response)
            
            releases = releases_response.get("Items", [])
            if not releases:
                self.logger.error(f"No releases found for project '{project_name}'")
                return self._error_response(f"No releases found for project '{project_name}'")
            
            self.logger.debug(f"Found {len(releases)} releases for project '{project_name}'")
            
            # Find the release
            release = self._find_release(releases, release_version)
            if not release:
                self.logger.error(f"Release version '{release_version}' not found for project '{project_name}'")
                return self._error_response(f"Release version '{release_version}' not found for project '{project_name}'")
            
            self.logger.info(f"Using release version '{release.get('Version')}' (ID: {release.get('Id')})")
            
            # Get environment
            self.logger.debug(f"Looking up environment '{environment_name}' in space '{space_name}'")
            environment = self._get_by_name(f"{space_id}/environments/all", environment_name)
            if not environment:
                self.logger.error(f"Environment '{environment_name}' not found in space '{space_name}'")
                return self._error_response(f"Environment '{environment_name}' not found in {space_name} space")
            
            self.logger.info(f"Deploying to environment '{environment.get('Name')}' (ID: {environment.get('Id')})")
            
            # Create deployment
            deployment_data = {
                "ReleaseId": release.get("Id"),
                "EnvironmentId": environment.get("Id")
            }
            
            self.logger.info(f"Creating deployment with data: {deployment_data}")
            deployment_response = self._make_request(f"{space_id}/deployments", method="POST", data=deployment_data)
            if "error" in deployment_response:
                self.logger.error(f"Failed to create deployment: {deployment_response.get('error')}")
             
            
            result = {
                "success": True,
                "message": "Deployment has been initiated successfully. This does not guarantee the deployment completed successfully.",
                "next_step": "Use the check_deployment_status tool to monitor the actual deployment progress and final status.",
                "space": {"id": space.get("Id"), "name": space.get("Name")},
                "project": {"id": project.get("Id"), "name": project.get("Name")},
                "release": {"id": release.get("Id"), "version": release.get("Version")},
                "environment": {"id": environment.get("Id"), "name": environment.get("Name")},
                "deployment": {
                    "id": deployment_response.get("Id"),
                    "name": deployment_response.get("Name"),
                    "state": deployment_response.get("State"),
                    "created": deployment_response.get("Created"),
                    "task_id": deployment_response.get("TaskId")
                }
            }
            
            return self._json_response(result)

        @self.server.mcp.tool()
        def check_deployment_status(project_name: str, release_version: str = "", environment_name: str = "", space_name: str = "Default") -> str:
            """Check the deployment status of a release across environments.
            
            Args:
                project_name: The name of the project to check
                release_version: The version of the release to check (optional, uses latest if not specified)
                environment_name: The name of the environment to check (optional, checks all environments if not specified)
                space_name: The name of the space (default: "Default")
            """
            if not project_name:
                return self._error_response("project_name is required")
            
            # Handle empty strings as None
            release_version = release_version.strip() if release_version else None
            environment_name = environment_name.strip() if environment_name else None
            
            # Get space by name
            space = self._get_space(space_name)
            if not space:
                return self._json_response({"error": f"Space '{space_name}' not found"})
            
            # Get project by name within the space
            project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
            if not project:
                return self._error_response(f"Project '{project_name}' not found in {space_name} space")
            
            space_id = space["Id"]
            
            # Get releases
            releases_response = self._get_project_releases(space_id, project["Id"])
            if "error" in releases_response:
                return self._json_response(releases_response)
            
            releases = releases_response.get("Items", [])
            if not releases:
                return self._error_response(f"No releases found for project '{project_name}'")
            
            # Find the release
            release = self._find_release(releases, release_version)
            if not release:
                return self._error_response(f"Release version '{release_version}' not found for project '{project_name}'")
            
            # Get environments to check
            environments_to_check = self._get_environments_to_check(space_id, environment_name)
            if not environments_to_check:
                return self._error_response(f"Environment '{environment_name}' not found in {space_name} space")
            
            # Get deployments for this release
            deployments_response = self._make_request(f"{space_id}/releases/{release['Id']}/deployments")
            if "error" in deployments_response:
                return self._json_response(deployments_response)
            
            deployments = deployments_response.get("Items", [])
            environment_statuses = self._build_environment_statuses(environments_to_check, deployments)
            
            result = {
                "success": True,
                "space": {"id": space.get("Id"), "name": space.get("Name")},
                "project": {"id": project.get("Id"), "name": project.get("Name")},
                "release": {"id": release.get("Id"), "version": release.get("Version")},
                "deployment_statuses": environment_statuses,
                "summary": {
                    "total_environments_checked": len(environments_to_check),
                    "deployed_count": len(environment_statuses),
                    "environments_with_deployments": len(environment_statuses)
                }
            }
            
            return self._json_response(result)
    
    def _get_environments_to_check(self, space_id: str, environment_name: Optional[str]) -> list:
        """Get list of environments to check for deployment status."""
        if environment_name:
            environment = self._get_by_name(f"{space_id}/environments/all", environment_name)
            return [environment] if environment else []
        
        # Get all environments
        environments_response = self._make_request(f"{space_id}/environments/all")
        if "error" in environments_response:
            return []
        
        return environments_response if isinstance(environments_response, list) else environments_response.get("Items", [])
    
    def _build_environment_statuses(self, environments: list, deployments: list) -> list:
        """Build deployment status for each environment."""
        environment_statuses = []
        
        for env in environments:
            env_id = env.get("Id")
            env_name = env.get("Name")
            
            # Find deployments for this environment
            env_deployments = [d for d in deployments if d.get("EnvironmentId") == env_id]
            
            if env_deployments:
                latest_deployment = env_deployments[0]  # Most recent
                deployment_status = self._get_deployment_status(latest_deployment)
                
                environment_statuses.append({
                    "environment": {"id": env_id, "name": env_name},
                    "deployment_status": deployment_status
                })
        
        return environment_statuses
    
    def _get_deployment_status(self, deployment: dict) -> dict:
        """Get detailed deployment status including task information."""
        task_id = deployment.get("TaskId")
        
        deployment_status = {
            "deployment_id": deployment.get("Id"),
            "state": None,
            "completed": False,
            "started": deployment.get("Created"),
            "completed_time": None,
            "duration": None,
            "task_id": task_id,
            "deployed_by": deployment.get("DeployedBy"),
            "comments": deployment.get("Comments", "")
        }
        
        # Get task details for enhanced information
        if task_id:
            task_response = self._make_request(f"tasks/{task_id}")
            if "error" not in task_response:
                deployment_status.update({
                    "state": task_response.get("State"),
                    "completed": task_response.get("IsCompleted", False),
                    "started": task_response.get("StartTime"),
                    "completed_time": task_response.get("CompletedTime"),
                    "duration": task_response.get("Duration")
                })
                
                if task_response.get("HasWarningsOrErrors", False):
                    deployment_status["error_message"] = task_response.get("ErrorMessage", "")
        
        return deployment_status