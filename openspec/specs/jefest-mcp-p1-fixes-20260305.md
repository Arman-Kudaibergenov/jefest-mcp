# SDD: jefest-mcp P1 fixes — path traversal + async handlers

## Context
Code review of Phase 1 skeleton found two issues:
1. **CRITICAL**: `write_sdd` tool has no path validation — allows writing files outside workspace via `../../` traversal
2. **HIGH**: `handle_call_tool()` in server.py is `async def` but calls synchronous handler functions without `await`. MCP SDK expects async handlers to return properly.

## Environment
- Project: jefest-mcp, path: C:\Users\Arman\workspace\jefest-mcp
- Platform: Python 3.12
- Skills: python-patterns, security-audit, api-expert
- RLM: load context for jefest-mcp

## Compatibility
- OS: any
- Platform: python
- Required tools: Bash, Read, Write, Edit
- Profile: balanced

## Approach
1. Path traversal: resolve target path and validate it's within WORKSPACE_PATH using `Path.is_relative_to()`
2. Async handlers: the handler functions are sync and that's fine — but `handle_call_tool` should use `asyncio.to_thread()` for potentially blocking operations, or simply call them synchronously (which is fine for stdio transport since it's single-threaded). The real fix is ensuring `result = fn(arguments)` works correctly — since fns are sync, this already works. But we should make handlers consistent: either all async or all sync with proper wrapping.

Best approach: keep tool functions sync, wrap the call in `handle_call_tool` with `await asyncio.to_thread(fn, arguments)` for correctness in SSE transport. This is future-proof.

## Files
- `jefest/tools/sdd.py` — EDIT — add path traversal guard in `write_sdd()` and `create_sdd()`
- `jefest/server.py` — EDIT — wrap sync handler calls with `asyncio.to_thread()`
- `jefest/tools/dispatch.py` — EDIT — add path validation if any file writes exist

## Atomic Tasks
1. Create worktree: `git worktree add .worktrees/dispatch-p1-fixes -b dispatch/p1-fixes`
2. cd `.worktrees/dispatch-p1-fixes`
3. Fix `jefest/tools/sdd.py`: in `write_sdd()`, after computing `target = config.WORKSPACE_PATH / path`, add: `target = target.resolve()` then `if not target.is_relative_to(config.WORKSPACE_PATH.resolve()): return {"error": "Path traversal detected", "path": path}`. Apply same pattern to `create_sdd()` if it writes files.
4. Fix `jefest/server.py`: in `handle_call_tool()`, change `result = fn(arguments)` to `result = await asyncio.to_thread(fn, arguments)`. Add `import asyncio` at top if missing.
5. Review `jefest/tools/dispatch.py` for any file write operations — add path validation if found.
6. Run `python -c "from jefest.server import server; print('import OK')"` to verify no syntax errors.

## Acceptance
- `write_sdd("../../etc/test", "x")` returns error dict with "Path traversal detected", does NOT write file
- `write_sdd("project/openspec/test.md", "x")` succeeds (within workspace)
- `python -c "from jefest.server import server"` succeeds without errors
- `handle_call_tool` uses `asyncio.to_thread` for handler invocation
- No `..` path can escape WORKSPACE_PATH in any tool

## Finalize
1. Commit all changes: `git add -A && git commit -m "fix: path traversal guard + async handler wrapping per SDD jefest-mcp-p1-fixes-20260305"`
2. Push worktree branch: `for remote in $(git remote); do git push $remote dispatch/p1-fixes; done`
3. Merge to master (from project root): `git -C "C:/Users/Arman/workspace/jefest-mcp" merge dispatch/p1-fixes`
4. Push master: `cd "C:/Users/Arman/workspace/jefest-mcp" && for remote in $(git remote); do git push $remote master; done`
5. Verify completion: `powershell.exe -NoProfile -File "C:/Users/Arman/workspace/Jefest/scripts/verify-completion.ps1" -SddPath "C:/Users/Arman/workspace/jefest-mcp/openspec/specs/jefest-mcp-p1-fixes-20260305.md" -ProjectPath "C:/Users/Arman/workspace/jefest-mcp"`
6. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-jefest-mcp.json` with status, tasks_done, tasks_failed, tasks_skipped, escalations
7. Remove worktree: `git -C "C:/Users/Arman/workspace/jefest-mcp" worktree remove .worktrees/dispatch-p1-fixes`
8. /exit
