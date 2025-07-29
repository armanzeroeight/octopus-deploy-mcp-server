"""Configuration management for Octopus Deploy MCP server."""

import os
import sys
from typing import Optional
from dataclasses import dataclass


@dataclass
class OctopusDeployConfig:
    """Octopus Deploy configuration."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "OctopusDeployConfig":
        """Create config from environment variables with validation."""
        base_url = os.getenv("OCTOPUS_URL")
        api_key = os.getenv("OCTOPUS_API_KEY")
        
        # Validate required environment variables
        if not base_url or not api_key:
            missing = []
            if not base_url:
                missing.append("  OCTOPUS_URL: Octopus Deploy server URL (e.g., https://your-octopus.octopus.app)")
            if not api_key:
                missing.append("  OCTOPUS_API_KEY: Octopus Deploy API key")
            
            print("ERROR: Missing required environment variables for Octopus Deploy server:", file=sys.stderr)
            print("\n".join(missing), file=sys.stderr)
            print("\nPlease set these environment variables before starting the server.", file=sys.stderr)
            print("Example:", file=sys.stderr)
            if not base_url:
                print("  export OCTOPUS_URL='https://your-octopus.octopus.app'", file=sys.stderr)
            if not api_key:
                print("  export OCTOPUS_API_KEY='your_api_key_here'", file=sys.stderr)
            sys.exit(1)
        
        # Ensure base_url ends with /api
        base_url = base_url.rstrip('/')
        if not base_url.endswith('/api'):
            base_url += '/api'
        
        return cls(base_url=base_url, api_key=api_key)


class Settings:
    """Global settings manager."""
    
    def __init__(self):
        self.octopus_deploy = OctopusDeployConfig.from_env()


# Global settings instance
settings = Settings()
