# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install the package
RUN pip install --no-cache-dir .

# Create a non-root user for security
RUN useradd -m -u 1000 mcp && chown -R mcp:mcp /app
USER mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the application (though MCP typically uses stdio)
EXPOSE 8000

# Default command to run the MCP server using the installed script
CMD ["octopus-deploy-mcp"]