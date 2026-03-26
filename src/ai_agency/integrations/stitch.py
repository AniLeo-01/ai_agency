"""Google Stitch API client for generating UI designs."""

import time

import httpx

STITCH_API_URL = "https://stitch.googleapis.com/mcp"
TIMEOUT_S = 180  # 3 minutes per request (design generation is slow)


class StitchClient:
    """Client for the Google Stitch JSON-RPC API."""

    def __init__(self, access_token: str = "", project_id: str = "", api_key: str = "") -> None:
        if not access_token and not api_key:
            raise ValueError(
                "Stitch credentials not configured. "
                "Set STITCH_API_KEY or STITCH_ACCESS_TOKEN in .env"
            )
        self.access_token = access_token
        self.api_key = api_key
        self.project_id = project_id
        self._client = httpx.Client(timeout=TIMEOUT_S)

    def _call(self, method: str, params: dict | None = None) -> dict:
        """Make a JSON-RPC call to the Stitch API."""
        body = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": int(time.time() * 1000),
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Goog-Api-Key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.access_token}"
            if self.project_id:
                headers["X-Goog-User-Project"] = self.project_id
        resp = self._client.post(
            STITCH_API_URL,
            json=body,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            err = data["error"]
            raise RuntimeError(f"Stitch API error: {err.get('message', err)}")
        return data.get("result", data)

    def _call_tool(self, tool_name: str, arguments: dict | None = None) -> dict:
        """Call a Stitch tool via tools/call."""
        return self._call("tools/call", {"name": tool_name, "arguments": arguments or {}})

    # --- Project management ---

    def list_projects(self) -> list:
        result = self._call_tool("list_projects")
        parsed = result
        if isinstance(result, dict) and "content" in result:
            import json
            for item in result["content"]:
                if item.get("type") == "text":
                    parsed = json.loads(item["text"])
                    break
        # API returns {"projects": [...]} — unwrap to flat list
        if isinstance(parsed, dict) and "projects" in parsed:
            return parsed["projects"]
        return parsed if isinstance(parsed, list) else []

    def create_project(self, title: str) -> dict:
        return self._call_tool("create_project", {"title": title})

    # --- Screen generation ---

    def generate_screen(self, prompt: str, project_id: str | None = None) -> dict:
        """Generate a new screen from a text prompt."""
        args = {"prompt": prompt}
        if project_id:
            args["projectId"] = project_id
        return self._call_tool("generate_screen_from_text", args)

    def list_screens(self, project_id: str) -> list:
        result = self._call_tool("list_screens", {"projectId": project_id})
        if isinstance(result, dict) and "content" in result:
            import json
            for item in result["content"]:
                if item.get("type") == "text":
                    return json.loads(item["text"])
        return result if isinstance(result, list) else []

    def get_screen(self, project_id: str, screen_id: str) -> dict:
        return self._call_tool("get_screen", {"projectId": project_id, "screenId": screen_id})

    def edit_screens(self, project_id: str, screen_ids: list[str], prompt: str) -> dict:
        """Edit existing screens with a new prompt."""
        return self._call_tool("edit_screens", {
            "projectId": project_id,
            "selectedScreenIds": screen_ids,
            "prompt": prompt,
        })

    def delete_screen(self, project_id: str, screen_id: str) -> dict:
        """Delete a screen from a project."""
        return self._call_tool("delete_screen", {
            "projectId": project_id,
            "screenId": screen_id,
        })

    # --- Content retrieval ---

    def fetch_screen_code(self, project_id: str, screen_id: str) -> str:
        """Get the HTML code for a generated screen."""
        screen_data = self.get_screen(project_id, screen_id)
        download_url = self._find_download_url(screen_data)
        if not download_url:
            raise RuntimeError("No code download URL found for this screen.")
        resp = self._client.get(download_url)
        resp.raise_for_status()
        return resp.text

    def fetch_screen_image(self, project_id: str, screen_id: str) -> bytes:
        """Get the screenshot image for a generated screen as bytes."""
        screen_data = self.get_screen(project_id, screen_id)
        image_url = self._find_image_url(screen_data)
        if not image_url:
            raise RuntimeError("No image URL found for this screen.")
        resp = self._client.get(image_url)
        resp.raise_for_status()
        return resp.content

    @staticmethod
    def _find_download_url(obj, _found=None) -> str | None:
        """Recursively find a downloadUrl in nested dicts/lists."""
        if not obj or not isinstance(obj, (dict, list)):
            return None
        if isinstance(obj, list):
            for item in obj:
                url = StitchClient._find_download_url(item)
                if url:
                    return url
            return None
        if "downloadUrl" in obj:
            return obj["downloadUrl"]
        for val in obj.values():
            url = StitchClient._find_download_url(val)
            if url:
                return url
        return None

    @staticmethod
    def _find_image_url(obj) -> str | None:
        """Recursively find an image URL in nested dicts/lists."""
        if not obj or not isinstance(obj, (dict, list)):
            return None
        if isinstance(obj, list):
            for item in obj:
                url = StitchClient._find_image_url(item)
                if url:
                    return url
            return None
        if isinstance(obj, dict):
            # Check screenshot.downloadUrl first
            screenshot = obj.get("screenshot")
            if isinstance(screenshot, dict) and "downloadUrl" in screenshot:
                return screenshot["downloadUrl"]
            # Check for image-like downloadUrl
            dl = obj.get("downloadUrl", "")
            if dl and (".png" in dl or ".jpg" in dl or "googleusercontent.com" in dl):
                return dl
            for val in obj.values():
                url = StitchClient._find_image_url(val)
                if url:
                    return url
        return None


def create_stitch_client() -> StitchClient:
    """Factory: create a StitchClient from environment config."""
    from ai_agency.config import get_stitch_api_key, get_stitch_project_id, get_stitch_token

    api_key = get_stitch_api_key()
    if api_key:
        return StitchClient(api_key=api_key)

    return StitchClient(
        access_token=get_stitch_token(),
        project_id=get_stitch_project_id(),
    )
