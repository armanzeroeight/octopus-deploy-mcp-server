# Octopus Deploy MCP Server Tests

This directory contains comprehensive tests for the Octopus Deploy MCP Server, focusing on high-level functionality rather than small unit tests.

## Test Structure

### Core Test Files

- **`test_basic_functionality.py`** - Basic infrastructure tests to verify imports, server creation, and response formatting
- **`test_tools_functionality.py`** - Comprehensive high-level tests for all tool functionality including complete workflows
- **`test_server_initialization.py`** - Tests for server initialization, configuration, and error handling
- **`conftest.py`** - Test configuration and fixtures

### Test Coverage

The tests cover the following high-level scenarios:

#### Project Tools
- ✅ Project details retrieval with active environments
- ✅ Project details when no active environments exist
- ✅ Error handling for missing projects/spaces
- ✅ API authentication failure handling

#### Release Tools
- ✅ Latest release retrieval
- ✅ Release creation with package dependencies
- ✅ Error handling for missing releases/channels
- ✅ API error propagation

#### Deployment Tools
- ✅ Release deployment to environments
- ✅ Deployment status checking across environments
- ✅ Latest release deployment (when version not specified)
- ✅ Error handling for missing environments/releases

#### Integration Scenarios
- ✅ Complete deployment workflow (project → release → deploy → status)
- ✅ Cross-space operations
- ✅ Error propagation across all tools
- ✅ Network failure handling
- ✅ Authentication failure handling

#### Server Infrastructure
- ✅ Server initialization with valid configuration
- ✅ Configuration validation and normalization
- ✅ Tool registration and setup
- ✅ Environment variable handling

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Basic functionality tests
python -m pytest tests/test_basic_functionality.py -v

# High-level tool functionality tests
python -m pytest tests/test_tools_functionality.py -v

# Server initialization tests
python -m pytest tests/test_server_initialization.py -v
```

### Run Individual Tests
```bash
# Test complete workflow
python -m pytest tests/test_tools_functionality.py::TestToolsFunctionality::test_complete_workflow_simulation -v

# Test project details
python -m pytest tests/test_tools_functionality.py::TestToolsFunctionality::test_project_tools_get_project_details -v
```

## Test Philosophy

These tests focus on:

1. **High-level functionality** - Testing complete user workflows rather than individual methods
2. **Integration scenarios** - Ensuring tools work together properly
3. **Error handling** - Verifying graceful failure modes
4. **Real-world usage** - Testing scenarios that actual users would encounter

The tests use mocked HTTP responses to simulate Octopus Deploy API interactions without requiring a live server.

## Test Data

Tests use realistic sample data structures that match the Octopus Deploy API format:
- Spaces, Projects, Releases, Environments, Deployments
- Proper ID relationships and data structures
- Realistic error responses and status codes

## Fixtures

- `octopus_server` - Mocked server instance with test configuration
- `mock_httpx_client` - HTTP client mock for API requests
- Sample data fixtures for all Octopus Deploy entities

## Dependencies

- pytest >= 7.0.0
- unittest.mock (built-in)
- All project dependencies for the MCP server