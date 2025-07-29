"""Basic functionality tests to verify the test setup works."""

import pytest
import json
from unittest.mock import Mock, patch
from src.octopus_deploy_mcp.server import OctopusDeployServer


class TestBasicFunctionality:
    """Basic tests to verify test infrastructure works."""
    
    def test_imports_work(self):
        """Test that all imports work correctly."""
        from src.octopus_deploy_mcp.server import OctopusDeployServer
        from src.octopus_deploy_mcp.tools.coordinator import OctopusDeployTools
        from src.octopus_deploy_mcp.tools.project_tools import ProjectTools
        from src.octopus_deploy_mcp.tools.release_tools import ReleaseTools
        from src.octopus_deploy_mcp.tools.deployment_tools import DeploymentTools
        
        assert OctopusDeployServer is not None
        assert OctopusDeployTools is not None
        assert ProjectTools is not None
        assert ReleaseTools is not None
        assert DeploymentTools is not None
    
    def test_server_creation_with_mocked_env(self, octopus_server):
        """Test that server can be created with mocked environment."""
        assert octopus_server is not None
        assert octopus_server.mcp is not None
        assert octopus_server.config is not None
        assert octopus_server.tools is not None
    
    def test_json_response_formatting(self, octopus_server):
        """Test JSON response formatting works correctly."""
        tools = octopus_server.tools.project_tools
        
        test_data = {"success": True, "message": "Test"}
        result = tools._json_response(test_data)
        
        # Verify it's valid JSON
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["message"] == "Test"
    
    def test_error_response_formatting(self, octopus_server):
        """Test error response formatting works correctly."""
        tools = octopus_server.tools.project_tools
        
        result = tools._error_response("Test error message")
        parsed = json.loads(result)
        
        assert "error" in parsed
        assert parsed["error"] == "Test error message"
    
    def test_base_tools_headers(self, octopus_server):
        """Test that base tools generate correct headers."""
        tools = octopus_server.tools.project_tools
        headers = tools._get_headers()
        
        assert "X-Octopus-ApiKey" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        # API key should exist (we can't easily mock the tools' internal config)
        assert len(headers["X-Octopus-ApiKey"]) > 0