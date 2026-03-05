from __future__ import annotations

_NOT_IMPLEMENTED = {"status": "not_implemented", "message": "Dispatch pipeline coming in next release"}


def dispatch(sdd_path: str, model: str = "sonnet", profile: str = "quality", force: bool = False) -> dict:
    """Dispatch an SDD to a Claude Code agent for execution. (Not yet implemented)"""
    return _NOT_IMPLEMENTED


def cancel_dispatch(dispatch_id: str) -> dict:
    """Cancel a running dispatch by ID. (Not yet implemented)"""
    return _NOT_IMPLEMENTED
