# SDD: jefest-mcp Phase 2 — Core Dispatch Pipeline

## Context
Phase 1 delivered the MCP server skeleton with stubs for dispatch/validate/status tools. Phase 2 implements the core dispatch pipeline: SDD validation, agent dispatch via claude CLI, state tracking, and result collection. This is the heart of jefest-mcp — without it, the server is just a registry browser.

jefest-mcp runs in Docker (Python 3.12 + claude CLI via npm). No PowerShell available — all orchestration in Python.

## Environment
- Project: jefest-mcp, path: C:\Users\Arman\workspace\jefest-mcp
- Platform: Python 3.12
- Skills: python-patterns, security-audit, testing-patterns, workflow-automation
- RLM: load context for jefest-mcp

## Compatibility
- OS: any (Docker target: linux)
- Platform: python
- Required tools: Bash, Read, Write, Edit
- Profile: quality

## Approach

### Dispatch Architecture
1. **SDD Validator** (`jefest/core/sdd_parser.py`): Parse markdown SDD into structured sections. Validate required fields (Context, Environment, Approach, Files, Atomic Tasks, Acceptance). Return ValidationResult with exit codes matching ExitCode enum.

2. **Dispatch Runner** (`jefest/core/dispatch_runner.py`):
   - Read SDD, extract project info from Environment section
   - Load skills from SDD `Skills:` line → read SKILL.md files → inject into agent-system-prompt.md template
   - Build claude CLI command: `claude --model <model> --system-prompt <prompt-file> --max-turns 50 --no-user-input -p <task>`
   - Run as async subprocess with timeout (default 10 min)
   - Capture stdout/stderr, parse result-JSON from output
   - Write dispatch state to /data/dispatches/{id}.json

3. **State Manager** (`jefest/core/state_manager.py`):
   - JSON file per dispatch in /data/dispatches/
   - States: queued → running → completed | failed | timeout
   - Atomic writes (write to .tmp, rename)

4. **Tool Implementations**: Wire the core modules into MCP tool handlers.

### Key Design Decisions
- claude CLI called via `asyncio.create_subprocess_exec` (non-blocking)
- Skills loaded from /app/skills/ directory (mounted in Docker)
- Agent prompt assembled from template + skills + known-issues placeholders
- Result JSON extracted from claude stdout using regex `\{[^}]*"status"[^}]*\}`
- Dispatch ID = timestamp + project name hash (no UUID dependency)

## Files
- `jefest/core/sdd_parser.py` — NEW — parse SDD markdown, extract sections, validate
- `jefest/core/dispatch_runner.py` — NEW — async subprocess dispatch, skill injection, result collection
- `jefest/core/state_manager.py` — NEW — dispatch state CRUD (JSON files)
- `jefest/tools/dispatch.py` — EDIT — implement dispatch() and cancel_dispatch()
- `jefest/tools/validate.py` — EDIT — implement validate_sdd()
- `jefest/tools/status.py` — EDIT — implement get_dispatch_status(), list_dispatches(), get_result()
- `jefest/server.py` — EDIT — register new tools in handle_list_tools if needed

## Atomic Tasks
1. Create worktree: `git worktree add .worktrees/dispatch-phase2 -b dispatch/phase2`
2. cd `.worktrees/dispatch-phase2`
3. Create `jefest/core/sdd_parser.py`:
   - `parse_sdd(path: str) -> dict` — read file, split by `## ` headers, return {section_name: content}
   - `validate_sdd(parsed: dict) -> ValidationResult` — check required sections (Context, Environment, Approach, Files, Atomic Tasks, Acceptance, Finalize), check Skills line in Environment, check project path exists
   - `extract_skills(parsed: dict) -> list[str]` — parse `Skills:` line from Environment section
   - `extract_project_path(parsed: dict) -> str` — parse `path:` from Environment section
4. Create `jefest/core/state_manager.py`:
   - `StateManager(data_dir: Path)` class
   - `create(project: str, sdd_path: str, model: str) -> str` — create dispatch record, return dispatch_id
   - `update(dispatch_id: str, **kwargs)` — update fields (status, exit_code, result, finished_at)
   - `get(dispatch_id: str) -> dict | None` — read dispatch state
   - `list_recent(limit: int = 20) -> list[dict]` — scan dir, sort by mtime desc
   - Atomic write: write to .tmp file, os.replace() to final path
5. Create `jefest/core/dispatch_runner.py`:
   - `DispatchRunner(config, state_manager, rlm_client)` class
   - `async run(sdd_path: str, model: str = "sonnet", force: bool = False) -> DispatchReport`:
     a. Parse SDD via sdd_parser
     b. Validate SDD — return early with exit code on failure
     c. Extract skills, load SKILL.md files from config.SKILLS_DIR
     d. Read agent-system-prompt.md template, replace {{SKILLS_PLACEHOLDER}} with skill contents
     e. Write assembled prompt to temp file
     f. Build claude command: `claude --model {model} --system-prompt {prompt_file} --max-turns 50 --no-user-input -p "Execute SDD: {sdd_path}\n\nRead the SDD file first, then follow Atomic Tasks."`
     g. Run via `asyncio.create_subprocess_exec`, capture stdout+stderr
     h. Parse result-JSON from stdout (search for JSON block with "status" key)
     i. Update state with result
     j. Log to RLM if available
   - `async cancel(dispatch_id: str) -> bool` — kill subprocess by PID from state
6. Edit `jefest/tools/validate.py` — call `sdd_parser.parse_sdd()` + `sdd_parser.validate_sdd()`, return structured result
7. Edit `jefest/tools/dispatch.py` — instantiate DispatchRunner, call `runner.run()`, return DispatchReport as dict
8. Edit `jefest/tools/status.py` — instantiate StateManager, delegate to get/list_recent/get methods
9. Verify: `python -c "from jefest.core.sdd_parser import parse_sdd, validate_sdd; print('sdd_parser OK')"`
10. Verify: `python -c "from jefest.core.state_manager import StateManager; print('state_manager OK')"`
11. Verify: `python -c "from jefest.core.dispatch_runner import DispatchRunner; print('dispatch_runner OK')"`
12. Verify: `python -c "from jefest.server import server; print('server OK')"`

## Acceptance
- `parse_sdd()` correctly extracts all ## sections from a sample SDD file
- `validate_sdd()` returns EC_VAL_MISSING_SECTION when required section is absent
- `validate_sdd()` returns EC_OK for a valid SDD
- `extract_skills()` returns list of skill names from `Skills: skill1, skill2, skill3` line
- `StateManager.create()` writes JSON to /data/dispatches/ with correct fields
- `StateManager.get()` reads back the same data
- `StateManager.list_recent()` returns dispatches sorted by creation time desc
- `dispatch()` tool no longer returns `_NOT_IMPLEMENTED`
- `validate_sdd()` tool no longer returns `{"status": "not_implemented"}`
- `get_dispatch_status()` tool no longer returns `{"status": "not_implemented"}`
- All imports succeed without errors: `python -c "from jefest.server import server"`

## Finalize
1. Commit all changes: `git add -A && git commit -m "feat: core dispatch pipeline — SDD parser, dispatch runner, state manager per SDD jefest-mcp-phase2-dispatch-20260305"`
2. Push worktree branch: `for remote in $(git remote); do git push $remote dispatch/phase2; done`
3. Merge to master (from project root): `git -C "C:/Users/Arman/workspace/jefest-mcp" merge dispatch/phase2`
4. Push master: `cd "C:/Users/Arman/workspace/jefest-mcp" && for remote in $(git remote); do git push $remote master; done`
5. Verify completion: `powershell.exe -NoProfile -File "C:/Users/Arman/workspace/Jefest/scripts/verify-completion.ps1" -SddPath "C:/Users/Arman/workspace/jefest-mcp/openspec/specs/jefest-mcp-phase2-dispatch-20260305.md" -ProjectPath "C:/Users/Arman/workspace/jefest-mcp"`
6. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-jefest-mcp.json` with status, tasks_done, tasks_failed, tasks_skipped, escalations
7. Remove worktree: `git -C "C:/Users/Arman/workspace/jefest-mcp" worktree remove .worktrees/dispatch-phase2`
8. /exit
