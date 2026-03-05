# SDD: <title>

## Context
Why this task exists. What problem it solves.

## Environment
- Project: <name>, path: <path>
- Platform: <python | nodejs | 1c-8.3.24 | other>
- Skills: skill1, skill2

## Compatibility
- OS: win32 | linux | any
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
1. Commit: `git add -A && git commit -m "feat: <description> per SDD <sdd-name>"`
2. Push branch: `for remote in $(git remote); do git push $remote dispatch/<id>; done`
3. Merge to master: `git -C <project-path> merge dispatch/<id>`
4. Push master: `cd <project-path> && for remote in $(git remote); do git push $remote master; done`
5. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-<project>.json`
6. Remove worktree: `git -C <project-path> worktree remove .worktrees/dispatch-<id>`
7. /exit
