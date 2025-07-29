#!/bin/bash

# Build script for Octopus Deploy MCP Server Docker image

set -e

echo "Building Octopus Deploy MCP Server Docker image..."

# Build the Docker image
docker build -t octopus-deploy-mcp:latest .

echo "✅ Docker image 'octopus-deploy-mcp:latest' built successfully!"
echo ""
echo "Add this configuration to your MCP client's mcp.json file:"
echo ""
echo '{'
echo '  "mcpServers": {'
echo '    "octopus-deploy": {'
echo '      "command": "docker",'
echo '      "args": ['
echo '        "run", "--rm", "-i",'
echo '        "-e", "OCTOPUS_URL",'
echo '        "-e", "OCTOPUS_API_KEY",'
echo '        "octopus-deploy-mcp:latest",'
echo '        "octopus-deploy-mcp", "--transport", "stdio"'
echo '      ],'
echo '      "env": {'
echo '        "OCTOPUS_URL": "https://your-octopus-server.com",'
echo '        "OCTOPUS_API_KEY": "your-api-key-here"'
echo '      }'
echo '    }'
echo '  }'
echo '}'
echo ""
echo "Remember to replace 'your-octopus-server.com' and 'your-api-key-here' with your actual values."
