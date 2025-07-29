"""Integration tests for release tools functionality."""

import pytest
import json
from unittest.mock import Mock
from src.octopus_deploy_mcp.tools.release_tools import ReleaseTools


class TestReleaseToolsIntegration:
    """Test release tools high-level functionality."""
    
    @pytest.fixture
    def release_tools(self, octopus_server):
        """Create release tools instance."""
        return ReleaseTools(octopus_server)
    
    def test_get_latest_release_success_flow(self, release_tools, mock_httpx_client,
                                           sample_space_data, sample_project_data, sample_release_data):
        """Test successful latest release retrieval."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": [sample_release_data]},  # releases
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'get_latest_release':
                tool_func = tool.func
                break
        
        assert tool_func is not None, "get_latest_release tool should be registered"
        
        # Execute the tool
        result = tool_func("TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert result_data["space"]["name"] == "Default"
        assert result_data["project"]["name"] == "TestProject"
        assert result_data["latest_release"]["version"] == "1.0.0"
        assert result_data["latest_release"]["id"] == "Releases-1"
    
    def test_get_latest_release_no_releases(self, release_tools, mock_httpx_client,
                                          sample_space_data, sample_project_data):
        """Test latest release retrieval when no releases exist."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            {"Items": []},  # releases (empty)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'get_latest_release':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "No releases found for project 'TestProject'" in result_data["error"]
    
    def test_create_release_success_flow(self, release_tools, mock_httpx_client,
                                       sample_space_data, sample_project_data):
        """Test successful release creation."""
        # Mock API responses
        channel_data = {"Id": "Channels-1", "Name": "Default"}
        template_data = {"Packages": []}
        created_release = {
            "Id": "Releases-2",
            "Version": "1.1.0",
            "Assembled": "2024-01-01T11:00:00.000Z",
            "ChannelId": "Channels-1",
            "ProjectId": "Projects-1",
            "SelectedPackages": []
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            [channel_data],  # channels
            template_data,  # deployment process template
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = created_release
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'create_release':
                tool_func = tool.func
                break
        
        assert tool_func is not None, "create_release tool should be registered"
        
        # Execute the tool
        result = tool_func("TestProject", "1.1.0", "Default", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert "Release '1.1.0' created successfully" in result_data["message"]
        assert result_data["release"]["version"] == "1.1.0"
        assert result_data["release"]["id"] == "Releases-2"
    
    def test_create_release_channel_not_found(self, release_tools, mock_httpx_client,
                                            sample_space_data, sample_project_data):
        """Test release creation when channel is not found."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            [],  # channels (empty)
        ]
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'create_release':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "1.1.0", "NonExistentChannel", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "Channel 'NonExistentChannel' not found" in result_data["error"]
    
    def test_create_release_missing_parameters(self, release_tools):
        """Test release creation with missing required parameters."""
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'create_release':
                tool_func = tool.func
                break
        
        # Execute the tool with missing version
        result = tool_func("TestProject", "", "Default", "Default")
        result_data = json.loads(result)
        
        # Verify error response
        assert "error" in result_data
        assert "project_name and version are required" in result_data["error"]
    
    def test_create_release_with_packages(self, release_tools, mock_httpx_client,
                                        sample_space_data, sample_project_data):
        """Test release creation with package dependencies."""
        # Mock API responses
        channel_data = {"Id": "Channels-1", "Name": "Default"}
        template_data = {
            "Packages": [{
                "ActionName": "Deploy Package",
                "PackageReferenceName": "MyPackage",
                "FeedId": "Feeds-1",
                "PackageId": "MyApp"
            }]
        }
        package_versions = [{"Version": "1.0.5"}]
        created_release = {
            "Id": "Releases-2",
            "Version": "1.1.0",
            "Assembled": "2024-01-01T11:00:00.000Z",
            "ChannelId": "Channels-1",
            "ProjectId": "Projects-1",
            "SelectedPackages": [{
                "ActionName": "Deploy Package",
                "PackageReferenceName": "MyPackage",
                "Version": "1.0.5"
            }]
        }
        
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        mock_get_response.json.side_effect = [
            [sample_space_data],  # spaces/all
            [sample_project_data],  # projects/all
            [channel_data],  # channels
            template_data,  # deployment process template
            package_versions,  # package versions
        ]
        
        mock_post_response = Mock()
        mock_post_response.status_code = 201
        mock_post_response.json.return_value = created_release
        
        mock_httpx_client.return_value.__enter__.return_value.get.return_value = mock_get_response
        mock_httpx_client.return_value.__enter__.return_value.post.return_value = mock_post_response
        
        # Setup tools
        release_tools.setup_release_tools()
        
        # Get the registered tool function
        tool_func = None
        for tool in release_tools.server.mcp._tools:
            if tool.name == 'create_release':
                tool_func = tool.func
                break
        
        # Execute the tool
        result = tool_func("TestProject", "1.1.0", "Default", "Default")
        result_data = json.loads(result)
        
        # Verify response structure
        assert result_data["success"] is True
        assert len(result_data["release"]["selected_packages"]) == 1
        assert result_data["release"]["selected_packages"][0]["Version"] == "1.0.5"