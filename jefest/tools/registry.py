from __future__ import annotations
from ..config import config
from ..core.registry_loader import RegistryLoader

_loader = RegistryLoader()


def _ensure_loaded() -> None:
    if not _loader.list_projects():
        _loader.load(config.JEFEST_REGISTRY)


def registry_lookup(query: str) -> list[dict]:
    """Search projects in the registry by name, type, or role."""
    _ensure_loaded()
    return [p.model_dump() for p in _loader.lookup(query)]


def list_projects() -> list[dict]:
    """List all projects in the registry."""
    _ensure_loaded()
    return [p.model_dump() for p in _loader.list_projects()]
