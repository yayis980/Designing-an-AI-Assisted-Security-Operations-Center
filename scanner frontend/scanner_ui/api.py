"""THE SWAP POINT.

This is the only file that gets data. While the backend does not exist it
returns the sample data after a short delay (so the loading state is real).
When the backend is ready, set these environment variables (or edit the
defaults below):

    SCANNER_USE_MOCK=false
    SCANNER_API_URL=http://localhost:8000/api

and the same calls will hit the real API.
"""

import json
import os
import time
import urllib.error
import urllib.request

from .mock_data import SERVERS

USE_MOCK = os.environ.get("SCANNER_USE_MOCK", "true").lower() != "false"
API_BASE = os.environ.get("SCANNER_API_URL", "http://localhost:8000/api").rstrip("/")


def fetch_servers() -> list:
    """Return a list of scanned servers (shape: see mock_data.py)."""
    if USE_MOCK:
        time.sleep(0.4)
        return SERVERS
    try:
        with urllib.request.urlopen(f"{API_BASE}/servers", timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach the backend at {API_BASE} ({exc.reason})")


def start_scan(target: str) -> dict:
    """Ask the backend to scan a new MCP server. Shape it however the backend wants."""
    if USE_MOCK:
        time.sleep(0.6)
        return {"ok": True, "message": f"Mock scan queued for {target}"}
    body = json.dumps({"target": target}).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}/scans",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach the backend at {API_BASE} ({exc.reason})")
