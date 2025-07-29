# Octopus Deploy MCP Server

A Model Context Protocol (MCP) server for interacting with Octopus Deploy. This server provides tools for managing projects, releases, and deployments through the MCP protocol.

## Features

- **Project Management**: List and query Octopus Deploy projects
- **Release Management**: Get latest releases and create new releases
- **Deployment Management**: Deploy releases and check deployment status
- **Multi-Space Support**: Work with different Octopus Deploy spaces
- **Docker Support**: Containerized deployment for easy integration

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/octopus-deploy-mcp.git
cd octopus-deploy-mcp
```

### 2. Build Docker Image

```bash
./scripts/build.sh
```

This will create a Docker image tagged as `octopus-deploy-mcp:latest`.

## MCP Configuration

Add the following configuration to your MCP client's `mcp.json` file:

```json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "octopus-api-key",
      "description": "Octopus Deploy API key",
      "password": true
    }
  ],
  "servers": {
    "octopus-deploy-mcp-server": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OCTOPUS_URL",
        "-e",
        "OCTOPUS_API_KEY",
        "octopus-deploy-mcp:latest",
        "octopus-deploy-mcp"
      ],
      "env": {
        "OCTOPUS_URL": "https://your-octopus-server.com",
        "OCTOPUS_API_KEY": "${input:octopus-api-key}"
      }
    }
  }
}
```

### Configuration Notes

- Replace `https://your-octopus-server.com` with your actual Octopus Deploy server URL (without `/api` suffix)
- The API key will be prompted securely when the MCP client starts
- The Docker image must be built locally using the build script

## Available Tools

### Project Tools
- `list_projects`: List all projects in a space
- `get_project_details`: Get detailed information about a specific project

### Release Tools
- `get_latest_release`: Get the latest release for a project
- `create_release`: Create a new release for a project

### Deployment Tools
- `deploy_release`: Deploy a release to an environment
- `check_deployment_status`: Check the status of deployments

## Development

### Local Setup (without Docker)

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Set up environment variables
cp .env.sh.example .env.sh
# Edit .env.sh with your Octopus Deploy credentials

# Run the server directly
source .env.sh

# Install the package in editable mode
uv pip install -e .
uv run octopus-deploy-mcp

# Or use fastmcp-cli tool for development
fastmcp dev dev.py
```

### Testing Docker Build

```bash
# Test the Docker image locally
./scripts/test-docker.sh
```

## Requirements

- Docker
- Your Octopus Deploy server URL
- Valid Octopus Deploy API key with appropriate permissions

## Troubleshooting

### Common Issues

1. **"Space 'Default' not found"**
   - Verify your Octopus server URL is correct
   - Check that your API key has access to the specified space
   - Ensure the space name exists (case-sensitive)

2. **"Authentication failed"**
   - Verify your API key is correct and hasn't expired
   - Check that the API key has the necessary permissions

3. **Docker build fails**
   - Ensure Docker is running
   - Check that you have sufficient disk space
   - Verify internet connectivity for downloading dependencies

### Debug Mode

The server automatically enables debug logging. Check the MCP client logs for detailed error information.

## Support

For issues and questions, please create an issue on GitHub.