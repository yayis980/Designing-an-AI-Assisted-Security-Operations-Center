"""The only file that talks to the backend.

Every piece of data in the UI comes from these two calls:

    fetch_servers()  ->  GET  /api/v1/servers/   (servers and their findings)
    start_scan(...)  ->  POST /api/v1/scans/     (ask for a new scan)

The backend address defaults to http://localhost:8000/api/v1. To point at a
different machine, set the SCANNER_API_URL environment variable.
"""

import json
import os
import urllib.error
import urllib.request

API_BASE = os.environ.get("SCANNER_API_URL", "http://localhost:8000/api/v1").rstrip("/")


def _backend_error(exc) -> RuntimeError:
    """Turn a network problem into a message the user can read."""
    if isinstance(exc, urllib.error.HTTPError):
        return RuntimeError(f"The backend returned an error (HTTP {exc.code}).")
    return RuntimeError(f"Could not reach the backend at {API_BASE} ({exc.reason})")


def fetch_servers() -> list:
    """Return the scanned servers, each with its findings."""
    try:
        with urllib.request.urlopen(f"{API_BASE}/servers/", timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise _backend_error(exc)


def start_scan(target: str) -> dict:
    """Ask the backend to scan a new MCP server."""
    body = json.dumps({"target": target}).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}/scans/",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise _backend_error(exc)
