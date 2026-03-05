from __future__ import annotations

import re
from pathlib import Path

from ..models import ExitCode, ValidationResult

REQUIRED_SECTIONS = [
    "Context",
    "Environment",
    "Approach",
    "Files",
    "Atomic Tasks",
    "Acceptance",
    "Finalize",
]


def parse_sdd(path: str) -> dict[str, str]:
    """Read SDD markdown file, split by ## headers, return {section_name: content}."""
    text = Path(path).read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines(keepends=True):
        match = re.match(r"^##\s+(.+)", line)
        if match:
            if current_name is not None:
                sections[current_name] = "".join(current_lines).strip()
            current_name = match.group(1).strip()
            current_lines = []
        else:
            if current_name is not None:
                current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "".join(current_lines).strip()

    return sections


def validate_sdd(parsed: dict[str, str]) -> ValidationResult:
    """Validate parsed SDD sections. Returns ValidationResult."""
    errors: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in parsed:
            errors.append(f"Missing required section: {section}")

    if errors:
        return ValidationResult(
            valid=False,
            exit_code=ExitCode.EC_VAL_MISSING_SECTION,
            errors=errors,
            warnings=warnings,
        )

    # Check Skills line in Environment section
    env = parsed.get("Environment", "")
    if "Skills:" not in env:
        errors.append("No Skills: line in Environment (agent will lack domain knowledge)")

    # Check project path exists
    project_path = extract_project_path(parsed)
    if project_path and not Path(project_path).exists():
        warnings.append(f"Project path does not exist: {project_path}")

    if errors:
        return ValidationResult(
            valid=False,
            exit_code=ExitCode.EC_VAL_MISSING_SECTION,
            errors=errors,
            warnings=warnings,
        )

    return ValidationResult(
        valid=True,
        exit_code=ExitCode.EC_OK,
        errors=[],
        warnings=warnings,
    )


def extract_skills(parsed: dict[str, str]) -> list[str]:
    """Parse Skills: line from Environment section, return list of skill names."""
    env = parsed.get("Environment", "")
    for line in env.splitlines():
        if line.strip().startswith("Skills:"):
            skills_part = line.split(":", 1)[1].strip()
            return [s.strip() for s in skills_part.split(",") if s.strip()]
    return []


def extract_project_path(parsed: dict[str, str]) -> str:
    """Parse path: from Environment section."""
    env = parsed.get("Environment", "")
    for line in env.splitlines():
        match = re.match(r"^\s*-?\s*[Pp]ath:\s*(.+)", line)
        if match:
            return match.group(1).strip()
    return ""
