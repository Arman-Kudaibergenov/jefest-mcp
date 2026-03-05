from __future__ import annotations
import logging
from pathlib import Path
from ..config import config
from ..models import SkillInfo

log = logging.getLogger(__name__)


def list_skills() -> list[dict]:
    """List all available skills from built-in skills dir and workspace project skills."""
    results: list[SkillInfo] = []

    # Built-in skills
    skills_dir = config.SKILLS_DIR
    if skills_dir.exists():
        for skill_md in skills_dir.glob("*/SKILL.md"):
            name = skill_md.parent.name
            desc = _first_line(skill_md)
            results.append(SkillInfo(name=name, description=desc, path=str(skill_md), source="built-in"))

    # Project skills from /workspace/*/.claude/skills/
    workspace = config.WORKSPACE_PATH
    if workspace.exists():
        for skill_md in workspace.glob("*/.claude/skills/*/SKILL.md"):
            name = skill_md.parent.name
            desc = _first_line(skill_md)
            results.append(SkillInfo(name=name, description=desc, path=str(skill_md), source="project"))

    return [s.model_dump() for s in results]


def _first_line(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip().lstrip("#").strip()
            if line:
                return line
    except OSError as e:
        log.warning("Cannot read skill file %s: %s", path, e)
    return ""
