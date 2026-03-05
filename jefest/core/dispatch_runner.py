from __future__ import annotations

import asyncio
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from ..models import DispatchReport, ExitCode
from .sdd_parser import extract_project_path, extract_skills, parse_sdd, validate_sdd
from .state_manager import StateManager

log = logging.getLogger(__name__)

_MODEL_MAP = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

DEFAULT_TIMEOUT = 600  # 10 minutes


def _resolve_model(model: str) -> str:
    return _MODEL_MAP.get(model, model)


def _extract_result_json(stdout: str) -> dict[str, Any] | None:
    """Search stdout for a JSON block containing 'status' key."""
    lines = stdout.splitlines()
    # Scan backwards for lines that look like JSON objects
    for line in reversed(lines):
        stripped = line.strip()
        if stripped.startswith("{"):
            try:
                decoder = json.JSONDecoder()
                data, _ = decoder.raw_decode(stripped)
                if isinstance(data, dict) and "status" in data:
                    return data
            except json.JSONDecodeError:
                pass
    # Fallback: try full stdout as a single JSON object
    try:
        stripped = stdout.strip()
        if stripped.startswith("{"):
            data = json.loads(stripped)
            if isinstance(data, dict) and "status" in data:
                return data
    except json.JSONDecodeError:
        pass
    return None


class DispatchRunner:
    def __init__(self, config: Any, state_manager: StateManager, rlm_client: Any = None) -> None:
        self.config = config
        self.state_manager = state_manager
        self.rlm_client = rlm_client
        self._procs: dict[str, asyncio.subprocess.Process] = {}

    async def run(
        self,
        sdd_path: str,
        model: str = "sonnet",
        profile: str = "balanced",
        force: bool = False,
    ) -> DispatchReport:
        start = time.time()

        # Validate sdd_path is within WORKSPACE_PATH (path traversal guard)
        try:
            sdd_resolved = Path(sdd_path).resolve()
            workspace_resolved = self.config.WORKSPACE_PATH.resolve()
            if not sdd_resolved.is_relative_to(workspace_resolved):
                return DispatchReport(
                    dispatch_id="",
                    status="failed",
                    escalations=[f"sdd_path outside WORKSPACE_PATH: {sdd_path}"],
                )
        except (OSError, ValueError) as e:
            return DispatchReport(
                dispatch_id="",
                status="failed",
                escalations=[f"sdd_path validation error: {e}"],
            )

        # Parse and validate SDD
        try:
            parsed = parse_sdd(sdd_path)
        except (OSError, FileNotFoundError) as e:
            return DispatchReport(
                dispatch_id="",
                status="failed",
                escalations=[f"Failed to read SDD: {e}"],
            )

        validation = validate_sdd(parsed)
        if not validation.valid:
            return DispatchReport(
                dispatch_id="",
                status="failed",
                tasks_failed=[{"step": "validate_sdd", "error": "; ".join(validation.errors)}],
            )

        # Determine project name
        project_path = extract_project_path(parsed)
        project = Path(project_path).name if project_path else Path(sdd_path).stem

        # Create dispatch record
        dispatch_id = self.state_manager.create(project, sdd_path, model)

        # Load skills
        skill_names = extract_skills(parsed)
        skills_content = self._load_skills(skill_names)

        # Assemble system prompt
        prompt_content = self._assemble_prompt(skills_content)

        resolved_model = _resolve_model(model)

        log.info("Dispatching %s model=%s profile=%s", dispatch_id, resolved_model, profile)
        self.state_manager.update(
            dispatch_id,
            status="running",
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

        stdout_data = ""
        stderr_data = ""
        exit_code = -1
        prompt_file: str | None = None

        try:
            # Write temp prompt file inside try block to ensure cleanup
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8"
            ) as f:
                f.write(prompt_content)
                prompt_file = f.name

            task_message = (
                f"CRITICAL: First read and follow ALL instructions from file '{prompt_file}'. "
                f"Then execute: Read the SDD file at {sdd_path} and execute ALL steps including Finalize section."
            )

            cmd = [
                "claude",
                "--model", resolved_model,
                "--max-turns", "50",
                "--no-user-input",
                "-p", task_message,
            ]

            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                self._procs[dispatch_id] = proc
                self.state_manager.update(dispatch_id, pid=proc.pid)

                try:
                    stdout_bytes, stderr_bytes = await asyncio.wait_for(
                        proc.communicate(), timeout=DEFAULT_TIMEOUT
                    )
                    stdout_data = stdout_bytes.decode(errors="replace")
                    stderr_data = stderr_bytes.decode(errors="replace")
                    exit_code = proc.returncode or 0
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.communicate()
                    self.state_manager.update(dispatch_id, status="timeout", finished_at=_now())
                    return DispatchReport(
                        dispatch_id=dispatch_id,
                        status="timeout",
                        escalations=[f"Dispatch timed out after {DEFAULT_TIMEOUT}s"],
                    )
            except FileNotFoundError:
                self.state_manager.update(dispatch_id, status="failed", exit_code=-1, finished_at=_now())
                return DispatchReport(
                    dispatch_id=dispatch_id,
                    status="failed",
                    tasks_failed=[{"step": "subprocess", "error": "claude CLI not found in PATH"}],
                )
            finally:
                self._procs.pop(dispatch_id, None)
        finally:
            if prompt_file:
                try:
                    Path(prompt_file).unlink()
                except OSError:
                    pass

        # Parse result JSON from stdout
        result_data = _extract_result_json(stdout_data)
        final_status = "completed" if exit_code == 0 else "failed"

        self.state_manager.update(
            dispatch_id,
            status=final_status,
            exit_code=exit_code,
            result=result_data,
            finished_at=_now(),
            stdout_tail=stdout_data[-2000:],
            stderr_tail=stderr_data[-1000:],
        )

        # Log to RLM if available
        if self.rlm_client:
            try:
                await self.rlm_client.add_fact(
                    f"Dispatch {dispatch_id} for {project}: status={final_status} exit={exit_code}",
                    level="project",
                    domain="jefest-dispatch",
                )
            except Exception as e:
                log.warning("RLM log failed: %s", e)

        if result_data:
            return DispatchReport(
                dispatch_id=dispatch_id,
                status=result_data.get("status", final_status),
                tasks_done=result_data.get("tasks_done", []),
                tasks_failed=result_data.get("tasks_failed", []),
                tasks_skipped=result_data.get("tasks_skipped", []),
                escalations=result_data.get("escalations", []),
            )

        return DispatchReport(
            dispatch_id=dispatch_id,
            status=final_status,
            escalations=[] if exit_code == 0 else [f"Exit code {exit_code}; no result-JSON found in stdout"],
        )

    async def cancel(self, dispatch_id: str) -> bool:
        proc = self._procs.get(dispatch_id)
        if proc:
            proc.kill()
            self.state_manager.update(dispatch_id, status="failed", finished_at=_now())
            return True
        # Try by PID from state
        state = self.state_manager.get(dispatch_id)
        if state and state.get("pid"):
            try:
                import signal
                import os
                os.kill(state["pid"], signal.SIGTERM)
                self.state_manager.update(dispatch_id, status="failed", finished_at=_now())
                return True
            except (ProcessLookupError, PermissionError):
                pass
        return False

    def _load_skills(self, skill_names: list[str]) -> str:
        parts: list[str] = []
        skills_dir = Path(self.config.SKILLS_DIR).resolve()
        workspace = Path(self.config.WORKSPACE_PATH).resolve()
        for name in skill_names:
            skill_file = (skills_dir / name / "SKILL.md").resolve()
            # Validate path is within allowed directories
            try:
                if not (skill_file.is_relative_to(skills_dir) or skill_file.is_relative_to(workspace)):
                    log.error("Skill file path outside allowed dirs: %s", skill_file)
                    continue
            except ValueError:
                log.error("Skill file path resolution failed: %s", skill_file)
                continue
            if skill_file.exists():
                parts.append(f"### Skill: {name}\n\n{skill_file.read_text(encoding='utf-8')}\n")
            else:
                log.warning("Skill file not found: %s", skill_file)
        return "\n---\n\n".join(parts) if parts else ""

    def _assemble_prompt(self, skills_content: str) -> str:
        template_path = Path(self.config.TEMPLATES_DIR) / "agent-system-prompt.md"
        if not template_path.exists():
            log.warning("agent-system-prompt.md not found at %s", template_path)
            return skills_content

        template = template_path.read_text(encoding="utf-8")
        prompt = template.replace("{{SKILLS_PLACEHOLDER}}", skills_content)
        prompt = prompt.replace("{{KNOWN_ISSUES_PLACEHOLDER}}", "")
        return prompt


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
