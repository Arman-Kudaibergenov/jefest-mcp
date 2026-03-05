from __future__ import annotations
from enum import IntEnum
from typing import Any
from pydantic import BaseModel


class ExitCode(IntEnum):
    EC_OK = 0
    EC_VAL_FORMAT = 1
    EC_VAL_MISSING_SECTION = 2
    EC_VAL_AMBIGUOUS = 3
    EC_VAL_WRONG_LOCATION = 16
    EC_EXEC_PARTIAL = 20
    EC_EXEC_FAIL = 21


class ProjectInfo(BaseModel):
    key: str
    path: str
    type: str = ""
    role: str = ""
    default_skills: list[str] = []


class SkillInfo(BaseModel):
    name: str
    description: str
    path: str
    source: str  # "built-in" | "project"


class SddContent(BaseModel):
    project: str
    title: str
    content: str


class DispatchResult(BaseModel):
    dispatch_id: str
    status: str
    exit_code: ExitCode = ExitCode.EC_OK
    output: str = ""
    errors: list[str] = []


class ValidationResult(BaseModel):
    valid: bool
    exit_code: ExitCode
    errors: list[str] = []
    warnings: list[str] = []


class DispatchStatus(BaseModel):
    dispatch_id: str
    status: str
    started_at: str = ""
    finished_at: str = ""


class DispatchReport(BaseModel):
    dispatch_id: str
    status: str
    tasks_done: list[str] = []
    tasks_failed: list[dict[str, Any]] = []
    tasks_skipped: list[str] = []
    escalations: list[str] = []
