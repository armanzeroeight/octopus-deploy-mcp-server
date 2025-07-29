"""Tests for server initialization and configuration."""

import pytest
import os
from unittest.mock import patch
from src.octopus_deploy_mcp.server import OctopusDeployServer
from src.octopus_deploy_mcp.settings import OctopusDeployConfig


class TestServerInitialization:
    """Test server initialization and configuration."""
    
    def test_server_creates_with_valid_config(self, octopus_server):
        """Test that server initializes correctly with valid environment variables."""
        server = octopus_server
        
        assert server is not None
        assert server.mcp is not None
        assert server.config is not None
        assert server.tools is not None
        assert server.config['base_url'] == 'https://test-octopus.octopus.app/api'
        assert server.config['api_key'] == 'API-TEST123456789'
    
    def test_server_fails_without_required_env_vars(self):
        """Test that server initialization fails without required environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit):
                OctopusDeployServer()
    
    def test_server_fails_with_missing_url(self):
        """Test that server initialization fails with missing OCTOPUS_URL."""
        with patch.dict(os.environ, {'OCTOPUS_API_KEY': 'test-key'}, clear=True):
            with pytest.raises(SystemExit):
                OctopusDeployServer()
    
    def test_server_fails_with_missing_api_key(self):
        """Test that server initialization fails with missing OCTOPUS_API_KEY."""
        with patch.dict(os.environ, {'OCTOPUS_URL': 'https://test.octopus.app'}, clear=True):
            with pytest.raises(SystemExit):
                OctopusDeployServer()
    
    def test_config_normalizes_base_url(self):
        """Test that configuration properly normalizes base URL."""
        with patch.dict(os.environ, {
            'OCTOPUS_URL': 'https://test-octopus.octopus.app/',
            'OCTOPUS_API_KEY': 'API-TEST123456789'
        }):
            config = OctopusDeployConfig.from_env()
            assert config.base_url == 'https://test-octopus.octopus.app/api'
    
    def test_config_adds_api_suffix(self):
        """Test that configuration adds /api suffix when missing."""
        with patch.dict(os.environ, {
            'OCTOPUS_URL': 'https://test-octopus.octopus.app',
            'OCTOPUS_API_KEY': 'API-TEST123456789'
        }):
            config = OctopusDeployConfig.from_env()
            assert config.base_url == 'https://test-octopus.octopus.app/api'
    
    def test_tools_are_properly_initialized(self, octopus_server):
        """Test that all tool categories are properly initialized."""
        tools = octopus_server.tools
        
        assert tools.project_tools is not None
        assert tools.release_tools is not None
        assert tools.deployment_tools is not None
        assert tools.server == octopus_server