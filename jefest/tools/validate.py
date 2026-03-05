from __future__ import annotations

from ..core.sdd_parser import extract_skills, parse_sdd
from ..core.sdd_parser import validate_sdd as _validate_sdd


def validate_sdd(sdd_path: str) -> dict:
    """Validate an SDD file against the schema."""
    try:
        parsed = parse_sdd(sdd_path)
    except (OSError, FileNotFoundError) as e:
        return {"valid": False, "exit_code": 1, "errors": [str(e)], "warnings": []}
    result = _validate_sdd(parsed)
    return result.model_dump()
