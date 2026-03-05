from __future__ import annotations
import logging
from pathlib import Path
import yaml
from ..models import ProjectInfo

log = logging.getLogger(__name__)


class RegistryLoader:
    def __init__(self) -> None:
        self._projects: dict[str, ProjectInfo] = {}

    def load(self, path: str | Path) -> None:
        p = Path(path)
        if not p.exists():
            log.warning("Registry file not found: %s", p)
            return
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
            projects = data.get("projects", {}) if data else {}
            self._projects = {
                key: ProjectInfo(key=key, **vals)
                for key, vals in projects.items()
            }
        except Exception as e:
            log.error("Failed to load registry: %s", e)

    def lookup(self, query: str) -> list[ProjectInfo]:
        q = query.lower()
        return [
            p for p in self._projects.values()
            if q in p.key.lower() or q in p.type.lower() or q in p.role.lower()
        ]

    def list_projects(self) -> list[ProjectInfo]:
        return list(self._projects.values())

    def get_project(self, key: str) -> ProjectInfo | None:
        return self._projects.get(key)
