"""Perform HTTP health checks without exposing sensitive request bodies."""
from datetime import datetime, timezone
from time import perf_counter
from urllib.parse import urlsplit
import requests


def validate_url(url: str) -> str:
    """Allow only public-facing HTTP(S) URLs for this local developer tool."""
    parsed = urlsplit(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a valid http:// or https:// URL")
    if parsed.username or parsed.password:
        raise ValueError("URLs with embedded credentials are not supported")
    return url.strip()


def check_endpoint(endpoint: dict, timeout: int = 8) -> dict:
    """Return one normalized result. HEAD/GET only, with no credentials."""
    url = validate_url(endpoint["url"])
    method = endpoint.get("method", "GET").upper()
    if method not in ("GET", "HEAD"):
        raise ValueError("Only GET and HEAD methods are supported")
    expected = int(endpoint.get("expected_status", 200))
    contains = endpoint.get("contains_text", "") or ""
    started = perf_counter()
    status = None
    error = ""
    healthy = False
    try:
        with requests.request(method, url, timeout=timeout, allow_redirects=True,
                              headers={"User-Agent": "PortfolioHealthMonitor/1.0"}) as response:
            status = response.status_code
            # Only read body if text assertion is requested.
            body_ok = not contains or (method == "GET" and contains in response.text[:100000])
            healthy = status == expected and body_ok
            if status != expected:
                error = f"Expected HTTP {expected}, received HTTP {status}"
            elif not body_ok:
                error = "Expected response text was not found"
    except requests.RequestException as exc:
        error = f"{type(exc).__name__}: {str(exc)[:180]}"
    return {"endpoint_id": endpoint["id"],
            "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status_code": status, "response_ms": round((perf_counter()-started)*1000, 1),
            "healthy": int(healthy), "error": error}
