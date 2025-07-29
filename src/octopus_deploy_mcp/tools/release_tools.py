"""Release-related Octopus Deploy tools."""

from .base_tools import BaseOctopusTools


class ReleaseTools(BaseOctopusTools):
    """Tools for managing Octopus Deploy releases."""
    
    def setup_release_tools(self) -> None:
        """Register release-related tools with the MCP server."""
        
        @self.server.mcp.tool()
        def get_latest_release(project_name: str, space_name: str = "Default") -> str:
            """Get the latest release for a specific project.
            
            Args:
                project_name: The name of the project to get the latest release for
                space_name: The name of the space (default: "Default")
            """
            if not project_name:
                return self._error_response("project_name is required")
            
            # Get space by name
            space = self._get_space(space_name)
            if not space:
                return self._json_response({"error": f"Space '{space_name}' not found"})
            
            # Get project by name within the space
            project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
            if not project:
                return self._error_response(f"Project '{project_name}' not found in {space_name} space")
            
            # Get releases
            releases_response = self._get_project_releases(space["Id"], project["Id"])
            if "error" in releases_response:
                return self._json_response(releases_response)
            
            releases = releases_response.get("Items", [])
            if not releases:
                return self._error_response(f"No releases found for project '{project_name}'")
            
            latest_release = releases[0]  # First item is the latest
            
            result = {
                "success": True,
                "space": {
                    "id": space.get("Id"),
                    "name": space.get("Name")
                },
                "project": {
                    "id": project.get("Id"),
                    "name": project.get("Name")
                },
                "latest_release": {
                    "id": latest_release.get("Id"),
                    "version": latest_release.get("Version"),
                    "release_notes": latest_release.get("ReleaseNotes", ""),
                    "assembled": latest_release.get("Assembled"),
                    "channel_id": latest_release.get("ChannelId"),
                    "project_id": latest_release.get("ProjectId"),
                    "selected_packages": latest_release.get("SelectedPackages", [])
                }
            }
            
            return self._json_response(result)

        @self.server.mcp.tool()
        def create_release(project_name: str, version: str, channel_name: str = "Default", space_name: str = "Default") -> str:
            """Create a new release for a specific project.
            
            Args:
                project_name: The name of the project to create a release for
                version: The version number for the new release (e.g., "1.0.0.0")
                channel_name: The name of the channel to use (default: "Default")
                space_name: The name of the space (default: "Default")
            """
            if not project_name or not version:
                return self._error_response("project_name and version are required")
            
            # Get space by name
            space = self._get_space(space_name)
            if not space:
                return self._json_response({"error": f"Space '{space_name}' not found"})
            
            # Get project by name within the space
            project = self._get_by_name(f"{space['Id']}/projects/all", project_name)
            if not project:
                return self._error_response(f"Project '{project_name}' not found in {space_name} space")
            
            space_id = space["Id"]
            project_id = project["Id"]
            
            # Get channel by name
            channel = self._get_by_name(f"{space_id}/projects/{project_id}/channels", channel_name)
            if not channel:
                return self._error_response(f"Channel '{channel_name}' not found for project '{project_name}'")
            
            # Get project template to determine required packages
            template_response = self._make_request(f"{space_id}/deploymentprocesses/deploymentprocess-{project_id}/template?channel={channel['Id']}")
            if "error" in template_response:
                return self._json_response(template_response)
            
            # Build selected packages list
            selected_packages = []
            for package in template_response.get("Packages", []):
                # Get the latest version of each package
                package_response = self._make_request(f"{space_id}/feeds/{package['FeedId']}/packages/versions?packageId={package['PackageId']}&take=1")
                if "error" in package_response:
                    return self._json_response(package_response)
                
                packages = package_response if isinstance(package_response, list) else package_response.get("Items", [])
                if packages:
                    selected_package = packages[0]  # Latest version
                    selected_packages.append({
                        "ActionName": package["ActionName"],
                        "PackageReferenceName": package["PackageReferenceName"],
                        "Version": selected_package["Version"]
                    })
            
            # Create release JSON
            release_data = {
                "ChannelId": channel["Id"],
                "ProjectId": project_id,
                "Version": version,
                "SelectedPackages": selected_packages
            }
            
            # Create the release
            release_response = self._make_request(f"{space_id}/releases", method="POST", data=release_data)
            if "error" in release_response:
                return self._json_response(release_response)
            
            result = {
                "success": True,
                "message": f"Release '{version}' created successfully for project '{project_name}'",
                "space": {
                    "id": space.get("Id"),
                    "name": space.get("Name")
                },
                "project": {
                    "id": project.get("Id"),
                    "name": project.get("Name")
                },
                "channel": {
                    "id": channel.get("Id"),
                    "name": channel.get("Name")
                },
                "release": {
                    "id": release_response.get("Id"),
                    "version": release_response.get("Version"),
                    "assembled": release_response.get("Assembled"),
                    "channel_id": release_response.get("ChannelId"),
                    "project_id": release_response.get("ProjectId"),
                    "selected_packages": release_response.get("SelectedPackages", [])
                }
            }
            
            return self._json_response(result)

