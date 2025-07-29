"""Test configuration and fixtures for Octopus Deploy MCP Server tests."""

import pytest
import os
from unittest.mock import Mock, patch
from src.octopus_deploy_mcp.server import OctopusDeployServer
from src.octopus_deploy_mcp.settings import OctopusDeployConfig


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'OCTOPUS_URL': 'https://test-octopus.octopus.app',
        'OCTOPUS_API_KEY': 'API-TEST123456789'
    }):
        yield


@pytest.fixture
def mock_config():
    """Mock Octopus Deploy configuration."""
    return OctopusDeployConfig(
        base_url='https://test-octopus.octopus.app/api',
        api_key='API-TEST123456789'
    )


@pytest.fixture
def octopus_server(mock_config):
    """Create an Octopus Deploy server instance for testing."""
    with patch('src.octopus_deploy_mcp.settings.settings') as mock_settings:
        mock_settings.octopus_deploy = mock_config
        server = OctopusDeployServer()
        # Override the config to use our mock
        server.config = mock_config.__dict__
        return server


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for API requests."""
    with patch('httpx.Client') as mock_client:
        yield mock_client


@pytest.fixture
def sample_space_data():
    """Sample space data for testing."""
    return {
        "Id": "Spaces-1",
        "Name": "Default",
        "Description": "Default space"
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "Id": "Projects-1",
        "Name": "TestProject",
        "Description": "Test project description",
        "ProjectGroupId": "ProjectGroups-1",
        "LifecycleId": "Lifecycles-1",
        "DeploymentProcessId": "deploymentprocess-Projects-1",
        "VariableSetId": "variableset-Projects-1"
    }


@pytest.fixture
def sample_release_data():
    """Sample release data for testing."""
    return {
        "Id": "Releases-1",
        "Version": "1.0.0",
        "ReleaseNotes": "Test release",
        "Assembled": "2024-01-01T10:00:00.000Z",
        "ChannelId": "Channels-1",
        "ProjectId": "Projects-1",
        "SelectedPackages": []
    }


@pytest.fixture
def sample_environment_data():
    """Sample environment data for testing."""
    return {
        "Id": "Environments-1",
        "Name": "Production",
        "Description": "Production environment"
    }


@pytest.fixture
def sample_deployment_data():
    """Sample deployment data for testing."""
    return {
        "Id": "Deployments-1",
        "Name": "Deploy TestProject release 1.0.0 to Production",
        "ReleaseId": "Releases-1",
        "EnvironmentId": "Environments-1",
        "TaskId": "ServerTasks-1",
        "State": "Success",
        "Created": "2024-01-01T10:00:00.000Z",
        "DeployedBy": "test-user",
        "Comments": ""
    }


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "Id": "ServerTasks-1",
        "State": "Success",
        "IsCompleted": True,
        "StartTime": "2024-01-01T10:00:00.000Z",
        "CompletedTime": "2024-01-01T10:05:00.000Z",
        "Duration": "00:05:00",
        "HasWarningsOrErrors": False,
        "ErrorMessage": ""
    }