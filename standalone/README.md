# Jefest Standalone — Quick Start

Run Jefest dispatch without Docker, using PowerShell scripts directly.

## Requirements

- Windows with PowerShell 5.1+
- [Claude Code CLI](https://github.com/anthropics/claude-code) installed (`claude` on PATH)
- Git
- Windows Terminal (optional, for new-tab launch)

## Setup

```powershell
# 1. Copy standalone/ to your workspace tools directory
Copy-Item -Recurse standalone/ C:/tools/jefest/

# 2. Copy and configure registry
Copy-Item C:/tools/jefest/registry.yaml.example C:/tools/jefest/registry.yaml
# Edit registry.yaml to add your projects
```

## Usage

### 1. Write an SDD

Copy `sdd-template.md` and fill in your task:

```powershell
Copy-Item C:/tools/jefest/sdd-template.md myproject/openspec/specs/my-task-20260305.md
# Edit the SDD
```

Key sections:
- `## Context` — what and why
- `## Atomic Tasks` — numbered steps starting with worktree creation
- `## Finalize` — commit, push, result-JSON, /exit

### 2. Validate SDD

```powershell
./validate-sdd.ps1 -SddPath myproject/openspec/specs/my-task-20260305.md
```

### 3. Dispatch

```powershell
./dispatch-lite.ps1 -ProjectPath C:/workspace/myproject -SddPath myproject/openspec/specs/my-task-20260305.md
```

Options:
- `-Model haiku|sonnet|opus` — Claude model (default: sonnet)
- `-Profile budget|balanced|quality` — budget forces haiku
- `-Force` — skip validation, override active dispatch lock
- `-NewProject` — allow ProjectPath that doesn't exist yet

### 4. Monitor

The dispatched agent writes `$env:TEMP/jefest-dispatch/result-<project>.json` on completion.

```powershell
# Check result
Get-Content $env:TEMP/jefest-dispatch/result-myproject.json | ConvertFrom-Json

# Verify completion
./verify-completion.ps1 -SddPath myproject/openspec/specs/my-task-20260305.md -ProjectPath C:/workspace/myproject
```

## Skills

Place skill files at `~/.claude/skills/<skill-name>/SKILL.md`.
Reference them in SDD `## Environment` section: `Skills: docker-expert, python-patterns`.

dispatch-lite.ps1 auto-injects referenced skills into the agent system prompt.

## Files

| File | Purpose |
|------|---------|
| `dispatch-lite.ps1` | Main dispatcher — validates SDD, launches Claude Code |
| `validate-sdd.ps1` | Structural SDD checker |
| `verify-completion.ps1` | Post-execution result checker |
| `agent-system-prompt.md` | System prompt injected into agent |
| `sdd-template.md` | SDD template |
| `sdd-checklist.md` | SDD quality checklist |
| `registry.yaml.example` | Example project registry |
