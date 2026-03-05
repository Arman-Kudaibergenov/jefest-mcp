from __future__ import annotations

from ..config import config
from ..core.state_manager import StateManager


def _get_state_manager() -> StateManager:
    return StateManager(config.DATA_DIR)


def get_dispatch_status(dispatch_id: str) -> dict:
    """Get the current status of a dispatch."""
    sm = _get_state_manager()
    state = sm.get(dispatch_id)
    if state is None:
        return {"error": f"Dispatch not found: {dispatch_id}"}
    return {
        "dispatch_id": state["dispatch_id"],
        "status": state["status"],
        "project": state.get("project", ""),
        "started_at": state.get("started_at", ""),
        "finished_at": state.get("finished_at", ""),
        "exit_code": state.get("exit_code"),
    }


def list_dispatches(limit: int = 20) -> dict:
    """List recent dispatches."""
    sm = _get_state_manager()
    items = sm.list_recent(limit=limit)
    return {
        "dispatches": [
            {
                "dispatch_id": d["dispatch_id"],
                "project": d.get("project", ""),
                "status": d["status"],
                "created_at": d.get("created_at", ""),
                "model": d.get("model", ""),
            }
            for d in items
        ],
        "total": len(items),
    }


def get_result(dispatch_id: str) -> dict:
    """Get the result JSON for a completed dispatch."""
    sm = _get_state_manager()
    state = sm.get(dispatch_id)
    if state is None:
        return {"error": f"Dispatch not found: {dispatch_id}"}
    return {
        "dispatch_id": dispatch_id,
        "status": state.get("status"),
        "result": state.get("result"),
        "exit_code": state.get("exit_code"),
        "finished_at": state.get("finished_at", ""),
    }
