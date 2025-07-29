"""High-level integration tests for the complete MCP server functionality."""

import pytest
import json
from unittest.mock import Mock, patch
from src.octopus_deploy_mcp.server import OctopusDeployServer


class TestMCPServerIntegration:
    """Test complete MCP server integration scenarios."""
    
    def test_server_tool_registration_complete(self, octopus_server):
        """Test that all expected tools are registered with the MCP server."""
        # Setup all tools
        octopus_server.tools.setup_tools()
        
        # Get registered tool names
        registered_tools = [tool.name for tool in octopus_server.mcp._tools]
        
        # Verify all expected tools are registered
        expected_tools = [
            'get_project_details',
            'get_latest_release',
            'create_release',
            'deploy_release',
            'check_deployment_status'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in registered_tools, f"Tool '{expected_tool}' should be registered"
        
        assert len(registered_tools) == len(expected_tools), "All tools should be registered"
    
    def test_complete_deployment_workflow(self, octopus_server, mock_httpx_client):
        """Test a complete deployment workflow from project details to deployment status."""
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
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": []},  # releases (no active environments)
            
            # get_latest_release calls
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
            
            # deploy_release calls
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
            [environment_data],  # environments/all
            
            # check_deployment_status calls
            [space_data],  # spaces/all
            [project_data],  # projects/all
            {"Items": [release_data]},  # releases
            [environment_data],  # environments/all
            {"Items": [deployment_data]},  # deployments
            task_data,  # task details
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = deployment_data
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup all tools
        octopus_server.tools.setup_tools()
        
        # Get tool functions
        tools = {tool.name: tool.func for tool in octopus_server.mcp._tools}
        
        # Step 1: Get project details
        project_result = tools['get_project_details']("MyApp", "Default")
        project_data_result = json.loads(project_result)
        assert project_data_result["success"] is True
        assert project_data_result["project"]["name"] == "MyApp"
        
        # Step 2: Get latest release
        release_result = tools['get_latest_release']("MyApp", "Default")
        release_data_result = json.loads(release_result)
        assert release_data_result["success"] is True
        assert release_data_result["latest_release"]["version"] == "1.0.0"
        
        # Step 3: Deploy release
        deploy_result = tools['deploy_release']("MyApp", "Production", "1.0.0", "Default")
        deploy_data_result = json.loads(deploy_result)
        assert deploy_data_result["success"] is True
        assert "initiated successfully" in deploy_data_result["message"]
        
        # Step 4: Check deployment status
        status_result = tools['check_deployment_status']("MyApp", "1.0.0", "Production", "Default")
        status_data_result = json.loads(status_result)
        assert status_data_result["success"] is True
        assert len(status_data_result["deployment_statuses"]) == 1
        assert status_data_result["deployment_statuses"][0]["deployment_status"]["state"] == "Success"
    
    def test_error_propagation_across_tools(self, octopus_server, mock_httpx_client):
        """Test that errors are properly propagated across different tools."""
        # Mock authentication failure
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup all tools
        octopus_server.tools.setup_tools()
        
        # Get tool functions
        tools = {tool.name: tool.func for tool in octopus_server.mcp._tools}
        
        # Test each tool handles authentication failure
        for tool_name, tool_func in tools.items():
            if tool_name == 'get_project_details':
                result = tool_func("TestProject", "Default")
            elif tool_name == 'get_latest_release':
                result = tool_func("TestProject", "Default")
            elif tool_name == 'create_release':
                result = tool_func("TestProject", "1.0.0", "Default", "Default")
            elif tool_name == 'deploy_release':
                result = tool_func("TestProject", "Production", "1.0.0", "Default")
            elif tool_name == 'check_deployment_status':
                result = tool_func("TestProject", "1.0.0", "Production", "Default")
            
            result_data = json.loads(result)
            assert "error" in result_data, f"Tool {tool_name} should handle authentication error"
            assert "Authentication failed" in result_data["error"], f"Tool {tool_name} should show auth error"
    
    def test_cross_space_operations(self, octopus_server, mock_httpx_client):
        """Test operations across different Octopus Deploy spaces."""
        # Sample data for different spaces
        spaces = [
            {"Id": "Spaces-1", "Name": "Development"},
            {"Id": "Spaces-2", "Name": "Production"}
        ]
        
        dev_project = {"Id": "Projects-1", "Name": "MyApp"}
        prod_project = {"Id": "Projects-2", "Name": "MyApp"}
        
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            spaces,  # spaces/all (Development)
            [dev_project],  # Development projects
            {"Items": []},  # Development releases
            
            spaces,  # spaces/all (Production)
            [prod_project],  # Production projects
            {"Items": []},  # Production releases
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup all tools
        octopus_server.tools.setup_tools()
        
        # Get tool function
        tools = {tool.name: tool.func for tool in octopus_server.mcp._tools}
        
        # Test project details in Development space
        dev_result = tools['get_project_details']("MyApp", "Development")
        dev_data = json.loads(dev_result)
        assert dev_data["success"] is True
        assert dev_data["space"]["name"] == "Development"
        
        # Test project details in Production space
        prod_result = tools['get_project_details']("MyApp", "Production")
        prod_data = json.loads(prod_result)
        assert prod_data["success"] is True
        assert prod_data["space"]["name"] == "Production"
    
    def test_server_handles_network_failures(self, octopus_server, mock_httpx_client):
        """Test server behavior when network requests fail."""
        # Mock network failure
        mock_httpx_client.return_value.__enter__.return_value.get.side_effect = Exception("Connection timeout")
        
        # Setup all tools
        octopus_server.tools.setup_tools()
        
        # Get tool function
        tools = {tool.name: tool.func for tool in octopus_server.mcp._tools}
        
        # Test that network failures are handled gracefully
        result = tools['get_project_details']("TestProject", "Default")
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "Unexpected error" in result_data["error"] or "Failed to connect" in result_data["error"]
    
    @patch('src.octopus_deploy_mcp.server.OctopusDeployServer.run')
    def test_server_startup_and_shutdown(self, mock_run, octopus_server):
        """Test server startup and shutdown process."""
        # Test that server can be started
        octopus_server.run("stdio")
        mock_run.assert_called_once_with(transport="stdio")
        
        # Verify tools are set up before running
        assert octopus_server.tools is not None
        assert len(octopus_server.mcp._tools) > 0