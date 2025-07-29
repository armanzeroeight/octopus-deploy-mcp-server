"""Integration tests for deployment tools functionality."""

import pytest
import json
from unittest.mock import Mock
from src.octopus_deploy_mcp.tools.deployment_tools import DeploymentTools


class TestDeploymentToolsIntegration:
    """Test deployment tools high-level functionality."""
    
    @pytest.fixture
    def deployment_tools(self, octopus_server):
        """Create deployment tools instance."""
        return DeploymentTools(octopus_server)
    
    def test_deploy_release_success_flow(self, deployment_tools, mock_httpx_client,
                                       sample_space_data, sample_project_data, 
                                       sample_release_data, sample_environment_data, sample_deployment_data):
        """Test successful deployment flow."""
        # Mock API responses
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [sample_environment_data],  # environments/all
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = sample_deployment_data
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'deploy_release':
                tool_func = tool.func
                break
        
        assert tool_func is not None, "deploy_release tool should be registered"
        
        # Execute the tool
        result = tool_func("TestProject", "Production", "1.0.0", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert "Deployment has been initiated successfully" in result_data["message"]
        assert result_data["deployment"]["id"] == "Deployments-1"
        assert result_data["deployment"]["state"] == "Success"
        assert "check_deployment_status" in result_data["next_step"]
    
    def test_deploy_release_latest_version(self, deployment_tools, mock_httpx_client,
                                         sample_space_data, sample_project_data, 
                                         sample_release_data, sample_environment_data, sample_deployment_data):
        """Test deployment using latest release version."""
        # Mock API responses
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [sample_environment_data],  # environments/all
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = sample_deployment_data
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'deploy_release':
                tool_func = tool.func
                break
        
        # Execute the tool without specifying release version (should use latest)
        result = tool_func("TestProject", "Production", None, "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert result_data["release"]["version"] == "1.0.0"  # Latest version
    
    def test_deploy_release_environment_not_found(self, deployment_tools, mock_httpx_client,
                                                 sample_space_data, sample_project_data, sample_release_data):
        """Test deployment when environment is not found."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [],  # environments/all (empty)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'deploy_release':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "NonExistentEnvironment", "1.0.0", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "Environment 'NonExistentEnvironment' not found" in result_data["error"]
    
    def test_check_deployment_status_success_flow(self, deployment_tools, mock_httpx_client,
                                                 sample_space_data, sample_project_data, 
                                                 sample_release_data, sample_environment_data,
                                                 sample_deployment_data, sample_task_data):
        """Test successful deployment status check."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [sample_environment_data],  # environments/all
            {"Items": [sample_deployment_data]},  # deployments
            sample_task_data,  # task details
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'check_deployment_status':
                tool_func = tool.func
                break
        
        assert tool_func is not None, "check_deployment_status tool should be registered"
        
        # Execute the tool
        result = tool_func("TestProject", "1.0.0", "Production", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert result_data["release"]["version"] == "1.0.0"
        assert len(result_data["deployment_statuses"]) == 1
        assert result_data["deployment_statuses"][0]["environment"]["name"] == "Production"
        assert result_data["deployment_statuses"][0]["deployment_status"]["state"] == "Success"
        assert result_data["deployment_statuses"][0]["deployment_status"]["completed"] is True
    
    def test_check_deployment_status_all_environments(self, deployment_tools, mock_httpx_client,
                                                     sample_space_data, sample_project_data, 
                                                     sample_release_data, sample_deployment_data):
        """Test deployment status check across all environments."""
        # Multiple environments
        environments = [
            {"Id": "Environments-1", "Name": "Production"},
            {"Id": "Environments-2", "Name": "Staging"}
        ]
        
        # Deployments for both environments
        deployments = [
            {**sample_deployment_data, "EnvironmentId": "Environments-1"},
            {**sample_deployment_data, "Id": "Deployments-2", "EnvironmentId": "Environments-2"}
        ]
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            environments,  # environments/all
            {"Items": deployments},  # deployments
            {"State": "Success", "IsCompleted": True},  # task 1
            {"State": "Success", "IsCompleted": True},  # task 2
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'check_deployment_status':
                tool_func = tool.func
                break
        
        # Execute the tool without specifying environment (should check all)
        result = tool_func("TestProject", "1.0.0", "", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert result_data["summary"]["total_environments_checked"] == 2
        assert len(result_data["deployment_statuses"]) == 2
    
    def test_check_deployment_status_no_deployments(self, deployment_tools, mock_httpx_client,
                                                   sample_space_data, sample_project_data, 
                                                   sample_release_data, sample_environment_data):
        """Test deployment status check when no deployments exist."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [sample_environment_data],  # environments/all
            {"Items": []},  # deployments (empty)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'check_deployment_status':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "1.0.0", "Production", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert len(result_data["deployment_statuses"]) == 0
        assert result_data["summary"]["deployed_count"] == 0
    
    def test_deploy_release_missing_parameters(self, deployment_tools):
        """Test deployment with missing required parameters."""
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'deploy_release':
                tool_func = tool.func
                break
        
        # Execute the tool with missing environment
        result = tool_func("TestProject", "", "1.0.0", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "project_name and environment_name are required" in result_data["error"]
    
    def test_deployment_api_failure_handling(self, deployment_tools, mock_httpx_client,
                                           sample_space_data, sample_project_data, 
                                           sample_release_data, sample_environment_data):
        """Test deployment handling when API call fails."""
        # Mock API responses - deployment creation fails
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
            [sample_environment_data],  # environments/all
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 500
        mock_post_response.text = "Internal Server Error"
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup tools
        deployment_tools.setup_deployment_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in deployment_tools.server.mcp._tools:
            if tool.name == 'deploy_release':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "Production", "1.0.0", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "500" in result_data["error"]