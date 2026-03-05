from __future__ import annotations
from pathlib import Path
from ..config import config


def create_sdd(
    project: str,
    title: str,
    context: str,
    approach: str,
    files: str,
    tasks: str,
    acceptance: str,
    skills: str = "",
) -> str:
    """Generate an SDD document by filling placeholders in the template."""
    template_path = config.TEMPLATES_DIR / "sdd-template.md"
    if not template_path.exists():
        return f"# SDD: {project} — {title}\n\nTemplate not found at {template_path}."
    template = template_path.read_text(encoding="utf-8")
    replacements = {
        "{{PROJECT}}": project,
        "{{TITLE}}": title,
        "{{CONTEXT}}": context,
        "{{APPROACH}}": approach,
        "{{FILES}}": files,
        "{{TASKS}}": tasks,
        "{{ACCEPTANCE}}": acceptance,
        "{{SKILLS}}": skills,
    }
    for key, val in replacements.items():
        template = template.replace(key, val)
    return template


def write_sdd(path: str, content: str) -> dict:
    """Write SDD content to /workspace/{path}."""
    target = config.WORKSPACE_PATH / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"written": True, "path": str(target)}
