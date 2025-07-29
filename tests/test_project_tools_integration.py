"""Integration tests for project tools functionality."""

import pytest
import json
from unittest.mock import Mock, patch
from src.octopus_deploy_mcp.tools.project_tools import ProjectTools


class TestProjectToolsIntegration:
    """Test project tools high-level functionality."""
    
    @pytest.fixture
    def project_tools(self, octopus_server):
        """Create project tools instance."""
        return ProjectTools(octopus_server)
    
    def test_get_project_details_success_flow(self, project_tools, mock_httpx_client, 
                                            sample_space_data, sample_project_data):
        """Test successful project details retrieval with all components."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": []},  # releases (no releases)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tools = project_tools.server.mcp.get_tools()
        tool_func = None
        for tool in tools:
            if tool.name == 'get_project_details':
                tool_func = project_tools.server.mcp.get_tool('get_project_details')
                break
        
        assert tool_func is not None, "get_project_details tool should be registered"
        
        # Execute the tool
        result = tool_func("TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert result_data["space"]["name"] == "Default"
        assert result_data["project"]["name"] == "TestProject"
        assert result_data["active_environments"] == "There is no active environment with a release for this project"
    
    def test_get_project_details_with_active_environments(self, project_tools, mock_httpx_client,
                                                        sample_space_data, sample_project_data):
        """Test project details retrieval with active environments."""
        # Mock API responses for project with deployments
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [{"Id": "Releases-1", "Version": "1.0.0"}]},  # releases
            {"Items": [{"EnvironmentId": "Environments-1"}]},  # deployments
            [{"Id": "Environments-1", "Name": "Production"}],  # environments/all
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in project_tools.server.mcp._tools:
            if tool.name == 'get_project_details':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert isinstance(result_data["active_environments"], list)
        assert len(result_data["active_environments"]) == 1
        assert result_data["active_environments"][0]["name"] == "Production"
    
    def test_get_project_details_space_not_found(self, project_tools, mock_httpx_client):
        """Test project details when space is not found."""
        # Mock empty spaces response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in project_tools.server.mcp._tools:
            if tool.name == 'get_project_details':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "NonExistentSpace")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "Space 'NonExistentSpace' not found" in result_data["error"]
    
    def test_get_project_details_project_not_found(self, project_tools, mock_httpx_client, sample_space_data):
        """Test project details when project is not found."""
        # Mock responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [],  # projects/all (empty)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in project_tools.server.mcp._tools:
            if tool.name == 'get_project_details':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("NonExistentProject", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "Project 'NonExistentProject' not found" in result_data["error"]
    
    def test_get_project_details_api_authentication_failure(self, project_tools, mock_httpx_client):
        """Test project details with API authentication failure."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in project_tools.server.mcp._tools:
            if tool.name == 'get_project_details':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "Authentication failed" in result_data["error"]
    
    def test_get_project_details_missing_parameters(self, project_tools):
        """Test project details with missing required parameters."""
        # Setup tools
        project_tools.setup_project_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in project_tools.server.mcp._tools:
            if tool.name == 'get_project_details':
                tool_func = tool.func
                break
        
        # Execute the tool with empty project name
        result = tool_func("", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "project_name is required" in result_data["error"]