from __future__ import annotations
import time
import httpx
from pathlib import Path

_start_time = time.time()


def health() -> dict:
    """Return server health status including RLM availability."""
    version = Path("/app/VERSION").read_text().strip() if Path("/app/VERSION").exists() else "unknown"
    rlm_status = "ok"
    try:
        httpx.get("http://localhost:8200/health", timeout=2).raise_for_status()
    except Exception:
        rlm_status = "error"
    return {
        "status": "ok",
        "version": version,
        "rlm_status": rlm_status,
        "uptime_sec": int(time.time() - _start_time),
    }


def update_check() -> dict:
    """Check GitHub for the latest release and compare with current version."""
    current = Path("/app/VERSION").read_text().strip() if Path("/app/VERSION").exists() else "0.0.0"
    try:
        resp = httpx.get(
            "https://api.github.com/repos/OWNER/jefest-mcp/releases/latest",
            timeout=5,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        latest = resp.json().get("tag_name", current).lstrip("v")
    except Exception:
        latest = current
    return {"current": current, "latest": latest, "has_update": latest != current}
