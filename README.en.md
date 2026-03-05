# Jefest MCP Server

Cross-project orchestrator for Claude Code. Dispatches SDD-based tasks to Sonnet agents across multiple projects. Available as Docker container (MCP server) or standalone PowerShell scripts.

[Русская версия](README.md) | Apache 2.0 License.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Opus (planner)                             │
│  Writes SDD → calls dispatch tool           │
└──────────────┬──────────────────────────────┘
               │ MCP tool call / PowerShell
┌──────────────▼──────────────────────────────┐
│  Jefest (orchestrator)                      │
│  Validates SDD, injects skills, launches    │
│  Sonnet agent in project worktree           │
└──────────────┬──────────────────────────────┘
               │ claude --permission-mode bypassPermissions
┌──────────────▼──────────────────────────────┐
│  Sonnet (executor)                          │
│  Reads SDD, executes atomic tasks, commits  │
│  Writes result-<project>.json, /exit        │
└─────────────────────────────────────────────┘
```

## Two Modes

| | Docker (MCP Server) | Standalone Scripts |
|---|---|---|
| Interface | MCP over HTTP | PowerShell CLI |
| Setup | `docker compose up -d` | Copy scripts |
| RLM | Embedded | Optional |
| OS | Linux container | Windows |
| Best for | Production, CI | Local dev, quick start |

---

## Mode 1: Docker (MCP Server)

### Quick Start

```bash
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and WORKSPACE_PATH
docker compose up -d
```

### Add to Claude Code

```json
{
  "mcpServers": {
    "jefest": {
      "url": "http://localhost:8300/mcp"
    }
  }
}
```

### Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Anthropic API key |
| `WORKSPACE_PATH` | `./workspace` | Path to your projects |
| `JEFEST_PORT` | `8300` | Host port for MCP server |
| `JEFEST_DEFAULT_MODEL` | `sonnet` | Claude model for dispatch |
| `RLM_EMBEDDING_PROVIDER` | `fastembed` | RLM embedding backend |

### MCP Tools

| Tool | Status | Description |
|---|---|---|
| `health` | stable | Server health + RLM status |
| `list_skills` | stable | List available skills |
| `registry_lookup` | stable | Search projects by query |
| `list_projects` | stable | List all registered projects |
| `create_sdd` | stable | Generate SDD from template |
| `write_sdd` | stable | Write SDD to workspace |
| `dispatch` | stub | Dispatch SDD to agent |
| `validate_sdd` | stub | Validate SDD format |
| `get_result` | stub | Get dispatch result |

### Custom Registry

```bash
cp registry.yaml.example workspace/registry.yaml
# Add your projects
```

### Custom Skills

```yaml
# docker-compose.yml
volumes:
  - ./my-skills:/app/skills
```

---

## Mode 2: Standalone Scripts

For users who don't want Docker. Pure PowerShell, no server required.

### Requirements

- Windows, PowerShell 5.1+
- [Claude Code CLI](https://github.com/anthropics/claude-code)
- Git
- Windows Terminal (optional)

### Setup

```powershell
# Copy standalone scripts to a convenient location
Copy-Item -Recurse standalone/ C:/tools/jefest/
```

### Write an SDD

```powershell
Copy-Item C:/tools/jefest/sdd-template.md myproject/openspec/specs/my-task-20260305.md
# Fill in: Context, Atomic Tasks, Acceptance, Finalize
```

Finalize section must include result-JSON step and `/exit`.

### Validate + Dispatch

```powershell
# Structural check
./standalone/validate-sdd.ps1 -SddPath myproject/openspec/specs/my-task.md

# Launch agent
./standalone/dispatch-lite.ps1 -ProjectPath C:/workspace/myproject -SddPath myproject/openspec/specs/my-task.md
```

### Options

```
-Model haiku|sonnet|opus    Claude model (default: sonnet)
-Profile budget|balanced    budget forces haiku model
-Force                      skip validation, override lock
-NewProject                 allow non-existent ProjectPath
```

### Monitor Results

```powershell
# Result written by agent at completion
Get-Content $env:TEMP/jefest-dispatch/result-myproject.json | ConvertFrom-Json

# Structural completion check
./standalone/verify-completion.ps1 -SddPath ... -ProjectPath ...
```

---

## Skills System

Skills inject domain knowledge into the agent system prompt. Reference them in the SDD:

```markdown
## Environment
- Skills: docker-expert, python-patterns, testing-patterns
```

Skills are loaded from:
1. `~/.claude/skills/<skill-name>/SKILL.md` (global)
2. `<project>/.claude/skills/<skill-name>/SKILL.md` (project-local)

Built-in skills in this repo (`skills/` directory):
- `docker-expert` — Docker on Proxmox/Linux
- `powershell-windows` — PowerShell patterns
- `workflow-automation` — CI/CD and automation
- `python-patterns` — Python infrastructure scripts
- `testing-patterns` — Unit/integration testing
- `security-audit` — OWASP security review
- `api-expert` — REST/GraphQL API design

For 1C-specific skills, see [1c-ai-development-kit](https://github.com/Arman-Kudaibergenov/1c-ai-development-kit).

---

## SDD Format

SDD (Software Design Document) is the contract between planner and executor.

```markdown
# SDD: <title>

## Context
## Environment
- Project: <name>, path: <path>
- Skills: skill1, skill2

## Atomic Tasks
1. Create worktree: git worktree add ...
2. ...

## Acceptance
- Verifiable condition

## Finalize
1. Commit + push
2. Write result-JSON
3. /exit
```

See `standalone/sdd-template.md` for full template.

---

## Development

```bash
pip install -e .
python -m jefest.server
```

---

## License

Apache 2.0. See [LICENSE](LICENSE).
