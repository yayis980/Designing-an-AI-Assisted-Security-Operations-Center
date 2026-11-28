import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

# Load environment variables from project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)

def require_scanner_api_key(
    supplied_key: str | None = Depends(api_key_header),
) -> None:
    """Allow access only with the configured SOC API key."""

    expected_key = os.getenv("SOC_API_KEY")

    # Never permit access if authentication is unconfigured
    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Scanner API authentication is not configured.",
        )

    if (
        not supplied_key
        or not secrets.compare_digest(
            supplied_key.encode("utf-8"),
            expected_key.encode("utf-8"),
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )

    