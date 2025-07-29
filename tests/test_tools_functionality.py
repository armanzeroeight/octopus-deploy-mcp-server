"""High-level functionality tests for Octopus Deploy MCP tools."""

import pytest
import json
from unittest.mock import Mock, patch
from src.octopus_deploy_mcp.tools.project_tools import ProjectTools
from src.octopus_deploy_mcp.tools.release_tools import ReleaseTools
from src.octopus_deploy_mcp.tools.deployment_tools import DeploymentTools


class TestToolsFunctionality:
    """Test the core functionality of all tools without MCP registration complexity."""
    
    def test_project_tools_get_project_details(self, octopus_server, mock_httpx_client):
        """Test project details retrieval functionality."""
        # Sample data
        space_data = {"Id": "Spaces-1", "Name": "Default"}
        project_data = {"Id": "Projects-1", "Name": "TestProject", "Description": "Test project"}
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": []},  # releases (no active environments)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Create project tools and test directly
        project_tools = ProjectTools(octopus_server)
        
        # Test the underlying functionality by calling the method directly
        # We'll simulate what the MCP tool would do
        result = self._simulate_get_project_details(project_tools, "TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify response
        assert result_data["success"] is True
        assert result_data["space"]["name"] == "Default"
        assert result_data["project"]["name"] == "TestProject"
        assert result_data["active_environments"] == "There is no active environment with a release for this project"
    
    def test_release_tools_get_latest_release(self, octopus_server, mock_httpx_client):
        """Test latest release retrieval functionality."""
        # Sample data
        space_data = {"Id": "Spaces-1", "Name": "Default"}
        project_data = {"Id": "Projects-1", "Name": "TestProject"}
        release_data = {"Id": "Releases-1", "Version": "1.0.0", "ProjectId": "Projects-1"}
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Create release tools and test directly
        release_tools = ReleaseTools(octopus_server)
        
        # Test the underlying functionality
        result = self._simulate_get_latest_release(release_tools, "TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify response
        assert result_data["success"] is True
        assert result_data["latest_release"]["version"] == "1.0.0"
        assert result_data["project"]["name"] == "TestProject"
    
    def test_deployment_tools_deploy_release(self, octopus_server, mock_httpx_client):
        """Test deployment functionality."""
        # Sample data
        space_data = {"Id": "Spaces-1", "Name": "Default"}
        project_data = {"Id": "Projects-1", "Name": "TestProject"}
        release_data = {"Id": "Releases-1", "Version": "1.0.0", "ProjectId": "Projects-1"}
        environment_data = {"Id": "Environments-1", "Name": "Production"}
        deployment_data = {
            "Id": "Deployments-1",
            "ReleaseId": "Releases-1",
            "EnvironmentId": "Environments-1",
            "TaskId": "ServerTasks-1",
            "State": "Success"
        }
        
        # Mock API responses
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
            [environment_data],  # environments/all
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = deployment_data
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Create deployment tools and test directly
        deployment_tools = DeploymentTools(octopus_server)
        
        # Test the underlying functionality
        result = self._simulate_deploy_release(deployment_tools, "TestProject", "Production", "1.0.0", "Default")
        result_data = json.loads(result)
        
        # Verify response
        assert result_data["success"] is True
        assert "initiated successfully" in result_data["message"]
        assert result_data["deployment"]["id"] == "Deployments-1"
    
    def test_deployment_tools_check_status(self, octopus_server, mock_httpx_client):
        """Test deployment status checking functionality."""
        # Sample data
        space_data = {"Id": "Spaces-1", "Name": "Default"}
        project_data = {"Id": "Projects-1", "Name": "TestProject"}
        release_data = {"Id": "Releases-1", "Version": "1.0.0", "ProjectId": "Projects-1"}
        environment_data = {"Id": "Environments-1", "Name": "Production"}
        deployment_data = {
            "Id": "Deployments-1",
            "EnvironmentId": "Environments-1",
            "TaskId": "ServerTasks-1"
        }
        task_data = {"State": "Success", "IsCompleted": True}
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
            [environment_data],  # environments/all
            {"Items": [deployment_data]},  # deployments
            task_data,  # task details
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Create deployment tools and test directly
        deployment_tools = DeploymentTools(octopus_server)
        
        # Test the underlying functionality
        result = self._simulate_check_deployment_status(deployment_tools, "TestProject", "1.0.0", "Production", "Default")
        result_data = json.loads(result)
        
        # Verify response
        assert result_data["success"] is True
        assert len(result_data["deployment_statuses"]) == 1
        assert result_data["deployment_statuses"][0]["deployment_status"]["state"] == "Success"
    
    def test_error_handling_across_tools(self, octopus_server, mock_httpx_client):
        """Test that all tools handle API errors gracefully."""
        # Mock authentication failure
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Test each tool handles errors
        project_tools = ProjectTools(octopus_server)
        release_tools = ReleaseTools(octopus_server)
        deployment_tools = DeploymentTools(octopus_server)
        
        # Test project tools error handling
        result = self._simulate_get_project_details(project_tools, "TestProject", "Default")
        result_data = json.loads(result)
        assert "error" in result_data
        # The error could be either authentication failed or space not found depending on where it fails first
        assert "not found" in result_data["error"] or "Authentication failed" in result_data["error"]
        
        # Test release tools error handling
        result = self._simulate_get_latest_release(release_tools, "TestProject", "Default")
        result_data = json.loads(result)
        assert "error" in result_data
        assert "not found" in result_data["error"] or "Authentication failed" in result_data["error"]
        
        # Test deployment tools error handling
        result = self._simulate_deploy_release(deployment_tools, "TestProject", "Production", "1.0.0", "Default")
        result_data = json.loads(result)
        assert "error" in result_data
        assert "not found" in result_data["error"] or "Authentication failed" in result_data["error"]
    
    def test_complete_workflow_simulation(self, octopus_server, mock_httpx_client):
        """Test a complete workflow from project details to deployment."""
        # Sample data
        space_data = {"Id": "Spaces-1", "Name": "Default"}
        project_data = {"Id": "Projects-1", "Name": "MyApp"}
        release_data = {"Id": "Releases-1", "Version": "1.0.0", "ProjectId": "Projects-1"}
        environment_data = {"Id": "Environments-1", "Name": "Production"}
        deployment_data = {
            "Id": "Deployments-1",
            "ReleaseId": "Releases-1",
            "EnvironmentId": "Environments-1",
            "TaskId": "ServerTasks-1",
            "State": "Success"
        }
        task_data = {"State": "Success", "IsCompleted": True}
        
        # Mock all API responses for the workflow
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            # get_project_details calls
            [space_data], [project_data], {"Items": []},
            # get_latest_release calls
            [space_data], [project_data], {"Items": [release_data]},
            # deploy_release calls
            [space_data], [project_data], {"Items": [release_data]}, [environment_data],
            # check_deployment_status calls
            [space_data], [project_data], {"Items": [release_data]}, [environment_data], 
            {"Items": [deployment_data]}, task_data,
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = deployment_data
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Create tool instances
        project_tools = ProjectTools(octopus_server)
        release_tools = ReleaseTools(octopus_server)
        deployment_tools = DeploymentTools(octopus_server)
        
        # Step 1: Get project details
        result = self._simulate_get_project_details(project_tools, "MyApp", "Default")
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["project"]["name"] == "MyApp"
        
        # Step 2: Get latest release
        result = self._simulate_get_latest_release(release_tools, "MyApp", "Default")
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["latest_release"]["version"] == "1.0.0"
        
        # Step 3: Deploy release
        result = self._simulate_deploy_release(deployment_tools, "MyApp", "Production", "1.0.0", "Default")
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "initiated successfully" in result_data["message"]
        
        # Step 4: Check deployment status
        result = self._simulate_check_deployment_status(deployment_tools, "MyApp", "1.0.0", "Production", "Default")
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["deployment_statuses"][0]["deployment_status"]["state"] == "Success"
    
    # Helper methods to simulate the tool functions
    def _simulate_get_project_details(self, project_tools, project_name, space_name):
        """Simulate the get_project_details tool function."""
        if not project_name:
            return project_tools._json_response({"error": "project_name is required"})
        
        # Get space by name
        space = project_tools._get_space(space_name)
        if not space:
            return project_tools._json_response({"error": f"Space '{space_name}' not found"})
        
        # Get project by name within the space
        project = project_tools._get_by_name(f"{space['Id']}/projects/all", project_name)
        if not project:
            return project_tools._json_response({"error": f"Project '{project_name}' not found in space '{space_name}'"})
        
        # Get environments with active deployments for this project
        environments = project_tools._get_active_environments(space['Id'], project['Id'])
        
        if not environments:
            environments = "There is no active environment with a release for this project"
        
        result = {
            "success": True,
            "space": {"id": space.get("Id"), "name": space.get("Name")},
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
        
        return project_tools._json_response(result, indent=2)
    
    def _simulate_get_latest_release(self, release_tools, project_name, space_name):
        """Simulate the get_latest_release tool function."""
        if not project_name:
            return release_tools._error_response("project_name is required")
        
        # Get space by name
        space = release_tools._get_space(space_name)
        if not space:
            return release_tools._json_response({"error": f"Space '{space_name}' not found"})
        
        # Get project by name within the space
        project = release_tools._get_by_name(f"{space['Id']}/projects/all", project_name)
        if not project:
            return release_tools._error_response(f"Project '{project_name}' not found in {space_name} space")
        
        # Get releases
        releases_response = release_tools._get_project_releases(space["Id"], project["Id"])
        if "error" in releases_response:
            return release_tools._json_response(releases_response)
        
        releases = releases_response.get("Items", [])
        if not releases:
            return release_tools._error_response(f"No releases found for project '{project_name}'")
        
        latest_release = releases[0]  # First item is the latest
        
        result = {
            "success": True,
            "space": {"id": space.get("Id"), "name": space.get("Name")},
            "project": {"id": project.get("Id"), "name": project.get("Name")},
            "latest_release": {
                "id": latest_release.get("Id"),
                "version": latest_release.get("Version"),
                "release_notes": latest_release.get("ReleaseNotes", ""),
                "assembled": latest_release.get("Assembled"),
                "channel_id": latest_release.get("ChannelId"),
                "project_id": latest_release.get("ProjectId"),
                "selected_packages": latest_release.get("SelectedPackages", [])
            }
        }
        
        return release_tools._json_response(result)
    
    def _simulate_deploy_release(self, deployment_tools, project_name, environment_name, release_version, space_name):
        """Simulate the deploy_release tool function."""
        if not project_name or not environment_name:
            return deployment_tools._error_response("project_name and environment_name are required")
        
        # Get space by name
        space = deployment_tools._get_space(space_name)
        if not space:
            return deployment_tools._json_response({"error": f"Space '{space_name}' not found"})
        
        project = deployment_tools._get_by_name(f"{space['Id']}/projects/all", project_name)
        if not project:
            return deployment_tools._error_response(f"Project '{project_name}' not found in {space_name} space")
        
        space_id = space["Id"]
        
        # Get releases
        releases_response = deployment_tools._get_project_releases(space_id, project["Id"])
        if "error" in releases_response:
            return deployment_tools._json_response(releases_response)
        
        releases = releases_response.get("Items", [])
        if not releases:
            return deployment_tools._error_response(f"No releases found for project '{project_name}'")
        
        # Find the release
        release = deployment_tools._find_release(releases, release_version)
        if not release:
            return deployment_tools._error_response(f"Release version '{release_version}' not found for project '{project_name}'")
        
        # Get environment
        environment = deployment_tools._get_by_name(f"{space_id}/environments/all", environment_name)
        if not environment:
            return deployment_tools._error_response(f"Environment '{environment_name}' not found in {space_name} space")
        
        # Create deployment
        deployment_data = {
            "ReleaseId": release.get("Id"),
            "EnvironmentId": environment.get("Id")
        }
        
        deployment_response = deployment_tools._make_request(f"{space_id}/deployments", method="POST", data=deployment_data)
        if "error" in deployment_response:
            return deployment_tools._json_response(deployment_response)
        
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
        
        return deployment_tools._json_response(result)
    
    def _simulate_check_deployment_status(self, deployment_tools, project_name, release_version, environment_name, space_name):
        """Simulate the check_deployment_status tool function."""
        if not project_name:
            return deployment_tools._error_response("project_name is required")
        
        # Handle empty strings as None
        release_version = release_version.strip() if release_version else None
        environment_name = environment_name.strip() if environment_name else None
        
        # Get space by name
        space = deployment_tools._get_space(space_name)
        if not space:
            return deployment_tools._json_response({"error": f"Space '{space_name}' not found"})
        
        # Get project by name within the space
        project = deployment_tools._get_by_name(f"{space['Id']}/projects/all", project_name)
        if not project:
            return deployment_tools._error_response(f"Project '{project_name}' not found in {space_name} space")
        
        space_id = space["Id"]
        
        # Get releases
        releases_response = deployment_tools._get_project_releases(space_id, project["Id"])
        if "error" in releases_response:
            return deployment_tools._json_response(releases_response)
        
        releases = releases_response.get("Items", [])
        if not releases:
            return deployment_tools._error_response(f"No releases found for project '{project_name}'")
        
        # Find the release
        release = deployment_tools._find_release(releases, release_version)
        if not release:
            return deployment_tools._error_response(f"Release version '{release_version}' not found for project '{project_name}'")
        
        # Get environments to check
        environments_to_check = deployment_tools._get_environments_to_check(space_id, environment_name)
        if not environments_to_check:
            return deployment_tools._error_response(f"Environment '{environment_name}' not found in {space_name} space")
        
        # Get deployments for this release
        deployments_response = deployment_tools._make_request(f"{space_id}/releases/{release['Id']}/deployments")
        if "error" in deployments_response:
            return deployment_tools._json_response(deployments_response)
        
        deployments = deployments_response.get("Items", [])
        environment_statuses = deployment_tools._build_environment_statuses(environments_to_check, deployments)
        
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
        
        return deployment_tools._json_response(result)