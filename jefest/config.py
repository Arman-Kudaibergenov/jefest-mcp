from __future__ import annotations
import os
from pathlib import Path


class Config:
    ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
    JEFEST_REGISTRY: str = os.environ.get("JEFEST_REGISTRY", "/workspace/registry.yaml")
    JEFEST_DEFAULT_MODEL: str = os.environ.get("JEFEST_DEFAULT_MODEL", "sonnet")
    JEFEST_PORT: int = int(os.environ.get("JEFEST_PORT", "8300"))
    RLM_URL: str = os.environ.get("RLM_URL", "http://localhost:8200")
    WORKSPACE_PATH: Path = Path(os.environ.get("WORKSPACE_PATH", "/workspace"))
    DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "/data"))
    TEMPLATES_DIR: Path = Path(os.environ.get("TEMPLATES_DIR", "/app/templates"))
    SKILLS_DIR: Path = Path(os.environ.get("SKILLS_DIR", "/app/skills"))


config = Config()
