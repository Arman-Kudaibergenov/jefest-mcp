from __future__ import annotations

from ..config import config
from ..core.dispatch_runner import DispatchRunner
from ..core.state_manager import StateManager


def _get_runner() -> DispatchRunner:
    state_manager = StateManager(config.DATA_DIR)
    return DispatchRunner(config, state_manager, rlm_client=None)


async def dispatch(sdd_path: str, model: str = "sonnet", profile: str = "quality", force: bool = False) -> dict:
    """Dispatch an SDD to a Claude Code agent for execution."""
    runner = _get_runner()
    report = await runner.run(sdd_path=sdd_path, model=model, profile=profile, force=force)
    return report.model_dump()


def cancel_dispatch(dispatch_id: str) -> dict:
    """Cancel a running dispatch by ID."""
    runner = _get_runner()
    cancelled = asyncio.run(runner.cancel(dispatch_id))
    return {"cancelled": cancelled, "dispatch_id": dispatch_id}
