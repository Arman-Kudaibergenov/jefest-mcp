# SDD: <title>

## Context
Why this task exists. What problem it solves.

## Environment
- Project: <name>, path: <path>
- Platform: <if 1C: version, server, port>
- DB: <if applicable>
- Skills: skill1, skill2, skill3
- RLM: load context for <project> (optional)

## Compatibility
- OS: win32 | linux | any
- Platform: 1c-8.3.24 | python | powershell | any
- Required tools: Bash, Read, Write, Edit
- Profile: balanced (budget | balanced | quality)

## Approach
How to solve it. Why this approach over alternatives.

## Files
- `path/to/file` — NEW | EDIT | DELETE — what changes

## Atomic Tasks
1. Create worktree: `git worktree add .worktrees/dispatch-<id> -b dispatch/<id>`
2. cd `.worktrees/dispatch-<id>`
3. <actual work step>
4. <actual work step>

## Acceptance
- Concrete verifiable condition
- Another verifiable condition

## Finalize
1. Commit all changes: `git add -A && git commit -m "feat: <description> per SDD <sdd-name>"`
2. Push worktree branch: `for remote in $(git remote); do git push $remote dispatch/<id>; done`
3. Merge to master (from project root): `git -C <project-path> merge dispatch/<id>`
4. Push master: `cd <project-path> && for remote in $(git remote); do git push $remote master; done`
5. Verify completion: `powershell.exe -NoProfile -File "C:/Users/Arman/workspace/Jefest/scripts/verify-completion.ps1" -SddPath "<path-to-this-sdd>"`
6. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-<project>.json` with status, tasks_done, tasks_failed, tasks_skipped, escalations
7. Remove worktree: `git -C <project-path> worktree remove .worktrees/dispatch-<id>`
8. /exit
