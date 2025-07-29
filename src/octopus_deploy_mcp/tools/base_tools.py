"""Base class for Octopus Deploy tools with common functionality."""

import json
import httpx
import logging
from typing import Dict, Any, Optional


class BaseOctopusTools:
    """Base class with common Octopus Deploy API functionality."""
    
    def __init__(self, server: "OctopusDeployServer"):
        self.server = server
        self.base_url = server.config.get("base_url", "").rstrip('/')
        self.api_key = server.config.get("api_key")
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests."""
        return {
            "X-Octopus-ApiKey": self.api_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Make a request to the Octopus Deploy API."""
        if not self.base_url or not self.api_key:
            return {"error": "Missing Octopus Deploy credentials. Please configure OCTOPUS_URL and OCTOPUS_API_KEY environment variables."}
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            with httpx.Client() as client:
                if method.upper() == "POST":
                    response = client.post(url, headers=headers, json=data)
                else:
                    response = client.get(url, headers=headers)
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 401:
                    return {"error": "Authentication failed. Please check your API key."}
                elif response.status_code == 404:
                    return {"error": "Resource not found."}
                else:
                    return {"error": f"API request failed with status {response.status_code}: {response.text}"}
                    
        except httpx.RequestError as e:
            return {"error": f"Failed to connect to Octopus Deploy API: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _get_by_name(self, uri: str, name: str) -> Optional[Dict[str, Any]]:
        """Get a resource by name from a collection endpoint."""
        resources = self._make_request(uri)
        if "error" in resources:
            return None
        
        items = resources if isinstance(resources, list) else resources.get("Items", [])
        return next((x for x in items if x.get('Name', '').lower() == name.lower()), None)
    
    def _get_space(self, space_name: str = "Default") -> Optional[Dict[str, Any]]:
        """Get space by name."""
        self.logger.debug(f"Looking up space: {space_name}")
        space = self._get_by_name("spaces/all", space_name)
        if not space:
            self.logger.error(f"Space '{space_name}' not found")
            return None
        self.logger.info(f"Found space: {space_name} (ID: {space['Id']})")
        return space
    
    def _get_project_by_name(self, project_name: str, space_name: str = "Default") -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Get project and space by project name. Returns (space, project) tuple."""
        space = self._get_space(space_name)
        if not space:
            return None, None
        
        project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
        return space, project
    
    def _get_project_releases(self, space_id: str, project_id: str) -> Dict[str, Any]:
        """Get releases for a project."""
        return self._make_request(f"{space_id}/projects/{project_id}/releases")
    
    def _find_release(self, releases: list, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find a specific release by version or return the latest."""
        if not releases:
            return None
        
        if version:
            return next((x for x in releases if x.get('Version') == version), None)
        return releases[0]  # Latest release
    
    def _json_response(self, data: Dict[str, Any], indent: int = 2) -> str:
        """Format response as JSON."""
        return json.dumps(data, indent=indent)
    
    def _error_response(self, message: str) -> str:
        """Format error response as JSON."""
        return self._json_response({"error": message})
    
    def _get_active_environments(self, space_id: str, project_id: str) -> list[Dict[str, Any]]:
        """Get environments that have active deployments for a specific project."""
        releases_response = self._make_request(f"{space_id}/projects/{project_id}/releases")
        if "error" in releases_response:
            self.logger.warning(f"Could not fetch releases: {releases_response.get('error', 'Unknown error')}")
            return []
        
        releases = releases_response.get("Items", [])
        if not releases:
            self.logger.info(f"No releases found for project {project_id}")
            return []
        
        # Get the latest release
        latest_release = releases[0]  # First item is the latest
        
        # Get deployments for this release
        deployments_response = self._make_request(f"{space_id}/releases/{latest_release['Id']}/deployments")
        if "error" in deployments_response:
            self.logger.warning(f"Could not fetch deployments for latest release: {deployments_response.get('error', 'Unknown error')}")
            return []
        
        deployments = deployments_response.get("Items", [])
        if not deployments:
            self.logger.info(f"No deployments found for latest release {latest_release.get('Version')}")
            return []
        
        # Get unique environment IDs from deployments
        env_ids_with_deployments = set()
        for deployment in deployments:
            env_id = deployment.get("EnvironmentId")
            if env_id:
                env_ids_with_deployments.add(env_id)
        
        self.logger.info(f"Found deployments in {len(env_ids_with_deployments)} environments for latest release: {env_ids_with_deployments}")
        
        # Get all environments
        environments_response = self._make_request(f"{space_id}/environments/all")
        if "error" in environments_response:
            self.logger.warning(f"Could not fetch environments: {environments_response.get('error', 'Unknown error')}")
            return []
        
        all_environments = environments_response if isinstance(environments_response, list) else environments_response.get("Items", [])
        
        # Filter to only environments with deployments
        active_environments = []
        for env in all_environments:
            env_id = env.get("Id")
            if env_id in env_ids_with_deployments:
                active_environments.append({
                    "id": env_id,
                    "name": env.get("Name")
                })
        
        self.logger.info(f"Filtered to {len(active_environments)} active environments")
        return active_environments
    