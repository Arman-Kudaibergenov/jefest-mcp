# SDD: jefest-mcp Phase 2 fixes — critical review findings

## Context
Code review of Phase 2 dispatch pipeline found 3 CRITICAL and 2 HIGH issues:
1. CRITICAL: `--system-prompt` flag passes string content, not file path. For large prompts (14KB+ with skills), must write to temp file and inject read instruction into first message (same pattern as Jefest dispatch-lite commit 5c4a6e7).
2. CRITICAL: sdd_path passed to claude CLI without path validation — allows traversal.
3. CRITICAL: `asyncio.run()` inside `asyncio.to_thread()` creates nested event loops. Fix: make dispatch tool handler async, use `await runner.run()` directly instead of through to_thread.
4. HIGH: temp file leak if error occurs before try block.
5. HIGH: JSON result regex `[^{}]*` breaks on nested objects. Use proper JSON extraction.
6. MEDIUM: Missing Skills should be error, not warning.
7. MEDIUM: `__import__("time")` instead of direct `time` import.
8. LOW: profile parameter accepted but ignored in dispatch tool.

## Environment
- Project: jefest-mcp, path: C:\Users\Arman\workspace\jefest-mcp
- Platform: Python 3.12
- Skills: python-patterns, security-audit
- RLM: load context for jefest-mcp

## Compatibility
- OS: any
- Platform: python
- Required tools: Bash, Read, Write, Edit
- Profile: balanced

## Approach
Fix all issues in-place. Key architectural change: dispatch tool handler becomes async (no more asyncio.run wrapper). System prompt delivered via file + instruction prefix (proven pattern from Jefest).

## Files
- `jefest/core/dispatch_runner.py` — EDIT — fix system prompt delivery, add path validation, fix temp file lifecycle, fix JSON parsing, fix time import
- `jefest/core/sdd_parser.py` — EDIT — change Skills warning to error
- `jefest/tools/dispatch.py` — EDIT — make handler async, pass profile param
- `jefest/server.py` — EDIT — dispatch handler needs special async treatment (no to_thread)

## Atomic Tasks
1. Create worktree: `git worktree add .worktrees/dispatch-p2-fixes -b dispatch/p2-fixes`
2. cd `.worktrees/dispatch-p2-fixes`
3. Fix `jefest/core/dispatch_runner.py`:
   a. CRITICAL #1: Remove `--system-prompt` flag. Instead, write assembled prompt to temp file. Prepend to task message: `"CRITICAL: First read and follow ALL instructions from file '{prompt_file}'. Then execute: {original_task}"`. Pass combined message as `-p` argument.
   b. CRITICAL #2: Add path validation for sdd_path — resolve and check `is_relative_to(config.WORKSPACE_PATH)`. Same for skill file paths in `_load_skills` — validate each resolved path is within SKILLS_DIR or WORKSPACE_PATH.
   c. HIGH #4: Move temp file creation inside the try block, or wrap entire method in try/finally that cleans up temp file.
   d. HIGH #5: Replace regex JSON extraction with: find last `{` before `"status"`, then use `json.JSONDecoder().raw_decode()` to parse properly. Alternative: scan stdout lines backwards, try `json.loads()` on each line that starts with `{`.
   e. Replace `__import__("time").strftime(...)` with `time.strftime(...)` (time already imported).
4. Fix `jefest/core/sdd_parser.py`:
   a. Change Skills missing from warning to error: `errors.append("No Skills: line in Environment (agent will lack domain knowledge)")`.
5. Fix `jefest/tools/dispatch.py`:
   a. Make `dispatch()` function `async def`.
   b. Replace `asyncio.run(runner.run(...))` with `await runner.run(...)`.
   c. Pass `profile` parameter to `runner.run()`.
6. Fix `jefest/server.py`:
   a. In `handle_call_tool`, for dispatch-related handlers that are now async, call them with `await fn(arguments)` instead of `await asyncio.to_thread(fn, arguments)`.
   b. Simple approach: check if handler result is a coroutine, if so await it: `result = fn(arguments); if asyncio.iscoroutine(result): result = await result`.
7. Verify: `python -c "from jefest.core.dispatch_runner import DispatchRunner; print('OK')"`
8. Verify: `python -c "from jefest.server import server; print('OK')"`

## Acceptance
- `dispatch_runner.py` does NOT use `--system-prompt` flag — uses file + instruction prefix instead
- sdd_path is validated against WORKSPACE_PATH before use
- skill file paths are validated before reading
- `dispatch()` in tools/dispatch.py is `async def` and uses `await runner.run()`
- No `asyncio.run()` call inside dispatch tool chain
- Missing Skills in SDD returns validation error (not warning)
- `python -c "from jefest.server import server"` succeeds
- No `__import__("time")` in codebase

## Finalize
1. Commit all changes: `git add -A && git commit -m "fix: critical review fixes — prompt delivery, path traversal, async, JSON parsing per SDD jefest-mcp-p2-fixes-20260305"`
2. Push worktree branch: `for remote in $(git remote); do git push $remote dispatch/p2-fixes; done`
3. Merge to master (from project root): `git -C "C:/Users/Arman/workspace/jefest-mcp" merge dispatch/p2-fixes`
4. Push master: `cd "C:/Users/Arman/workspace/jefest-mcp" && for remote in $(git remote); do git push $remote master; done`
5. Verify completion: `powershell.exe -NoProfile -File "C:/Users/Arman/workspace/Jefest/scripts/verify-completion.ps1" -SddPath "C:/Users/Arman/workspace/jefest-mcp/openspec/specs/jefest-mcp-p2-fixes-20260305.md" -ProjectPath "C:/Users/Arman/workspace/jefest-mcp"`
6. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-jefest-mcp.json`
7. Remove worktree: `git -C "C:/Users/Arman/workspace/jefest-mcp" worktree remove .worktrees/dispatch-p2-fixes`
8. /exit
