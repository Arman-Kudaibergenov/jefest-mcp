from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_DISPATCH_STATES = ("queued", "running", "completed", "failed", "timeout")


def _make_dispatch_id(project: str) -> str:
    ts = int(time.time())
    h = hashlib.sha1(project.encode()).hexdigest()[:6]
    return f"{ts}-{h}"


class StateManager:
    def __init__(self, data_dir: Path) -> None:
        self.dispatches_dir = data_dir / "dispatches"
        self.dispatches_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, dispatch_id: str) -> Path:
        return self.dispatches_dir / f"{dispatch_id}.json"

    def _write(self, dispatch_id: str, data: dict[str, Any]) -> None:
        tmp = self._path(dispatch_id).with_suffix(".tmp")
        tmp.write_text(json.dumps(data, default=str, indent=2), encoding="utf-8")
        os.replace(tmp, self._path(dispatch_id))

    def create(self, project: str, sdd_path: str, model: str) -> str:
        dispatch_id = _make_dispatch_id(project)
        data: dict[str, Any] = {
            "dispatch_id": dispatch_id,
            "project": project,
            "sdd_path": sdd_path,
            "model": model,
            "status": "queued",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "started_at": "",
            "finished_at": "",
            "exit_code": None,
            "result": None,
            "pid": None,
        }
        self._write(dispatch_id, data)
        log.info("Created dispatch %s for project %s", dispatch_id, project)
        return dispatch_id

    def update(self, dispatch_id: str, **kwargs: Any) -> None:
        data = self.get(dispatch_id)
        if data is None:
            log.warning("update: dispatch %s not found", dispatch_id)
            return
        data.update(kwargs)
        self._write(dispatch_id, data)

    def get(self, dispatch_id: str) -> dict[str, Any] | None:
        p = self._path(dispatch_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            log.error("Failed to read dispatch %s: %s", dispatch_id, e)
            return None

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        files = sorted(
            self.dispatches_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        results = []
        for f in files[:limit]:
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
        return results
