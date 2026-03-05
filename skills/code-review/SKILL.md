---
name: code-review
description: >
  This skill MUST be invoked when user says "review", "review diff", "check agent result", "code review".
  SHOULD also invoke after a dispatch agent completes work and Opus needs to review changes.
  Do NOT use for writing code — only for reviewing existing changes.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Code Review

Review agent work before merge. Goal: catch bugs, security issues, and scope creep. Keep feedback actionable with file:line references.

## Step 1 — Get the diff

```bash
# Between branches
git diff main..HEAD

# Staged only
git diff --staged

# Specific commit
git show <sha>
```

## Step 2 — Security checks

- Hardcoded credentials, tokens, API keys — reject immediately
- SQL/shell injection: user input passed to queries or subprocesses without sanitization
- File path traversal: user-controlled paths without normalization
- Secrets in logs or error messages

## Step 3 — Logic checks

- Off-by-one errors in loops and slices
- Null/None dereference without guard
- Error return values ignored
- Race conditions in concurrent code
- Incorrect boolean logic (especially negations)

## Step 4 — Scope check (critical for agents)

Agent must have done ONLY what was asked. Flag any:
- Refactoring not requested
- Added comments or docstrings not in task
- Renamed variables/functions beyond scope
- Extra features or "improvements"
- Modified files not mentioned in the task

## Step 5 — Style

- Consistent with surrounding code (indentation, naming, quotes)
- No dead code left behind
- No debug prints/console.logs committed

## Output format

```
APPROVE  — no issues found

REQUEST CHANGES:
- file.py:42  — hardcoded password "secret123"
- utils.js:17 — undefined variable `x` used before assignment
- config.py:8 — out of scope: renamed variable not requested in task
```

One line per issue. No prose. File:line mandatory.
