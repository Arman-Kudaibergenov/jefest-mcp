# SDD: jefest-mcp Project Skeleton + Docker + MCP Server

## Context
Jefest is a cross-project orchestrator for Claude Code. Currently PowerShell scripts on Windows.
Goal: package as a Docker container with MCP interface. Open source (Apache 2.0) + Docker image.
User does `docker-compose up` → adds to `.mcp.json` → gets dispatch/SDD/skills tools.

This SDD creates the project skeleton: Docker setup, MCP server, config, models, RLM client,
and basic tools (health, list_skills, registry_lookup, list_projects). The dispatch pipeline
(core/) will be implemented in a follow-up SDD.

## Environment
- Project: jefest-mcp, path: C:\Users\Arman\workspace\jefest-mcp
- Platform: Python 3.12, Docker
- Skills: python-patterns, docker-expert, workflow-automation
- RLM: load context for Jefest

## Compatibility
- OS: any (Docker)
- Platform: python
- Required tools: Bash, Read, Write, Edit
- Profile: quality

## Approach
1. Create all project files from scratch (new project, empty repo)
2. Python MCP server using `mcp` library (PyPI: `mcp`)
3. RLM embedded via supervisord (rlm-toolkit[all] + rlm-server)
4. Claude CLI installed via npm (@anthropic-ai/claude-code) for future dispatch
5. Copy templates from Jefest, copy skills from ~/.claude/skills/

Key patterns:
- `mcp` library: `from mcp.server import Server; server = Server("jefest")`
- Tools registered with `@server.tool()` decorator
- Async handlers, Pydantic models for I/O
- Config via env vars (ANTHROPIC_API_KEY, JEFEST_REGISTRY, etc.)

## Files
- `VERSION` — NEW — "0.1.0"
- `LICENSE` — NEW — Apache 2.0 full text
- `requirements.txt` — NEW — Python deps
- `Dockerfile` — NEW — Multi-stage: python:3.12-slim + nodejs + claude CLI + rlm-toolkit
- `docker-compose.yml` — NEW — Service definition, volumes, env
- `.env.example` — NEW — Example env vars
- `supervisord.conf` — NEW — RLM (port 8200) + Jefest MCP (port 8300)
- `entrypoint.sh` — NEW — Start supervisord
- `jefest/__init__.py` — NEW — Package init with version
- `jefest/server.py` — NEW — MCP server entry point, tool registration
- `jefest/config.py` — NEW — Env vars, paths, constants
- `jefest/models.py` — NEW — Pydantic models (DispatchResult, ValidationResult, etc.) + ExitCode enum
- `jefest/rlm_client.py` — NEW — Async HTTP client for localhost:8200 RLM
- `jefest/tools/__init__.py` — NEW — Empty
- `jefest/tools/skills.py` — NEW — list_skills() tool
- `jefest/tools/registry.py` — NEW — registry_lookup(), list_projects() tools
- `jefest/tools/admin.py` — NEW — health(), update_check() tools
- `jefest/tools/sdd.py` — NEW — create_sdd(), write_sdd() tools (template-based)
- `jefest/tools/status.py` — NEW — Stub: get_dispatch_status(), list_dispatches(), get_result() (return "not implemented yet")
- `jefest/tools/dispatch.py` — NEW — Stub: dispatch(), cancel_dispatch() (return "not implemented yet")
- `jefest/tools/validate.py` — NEW — Stub: validate_sdd() (return "not implemented yet")
- `jefest/core/__init__.py` — NEW — Empty
- `jefest/core/registry_loader.py` — NEW — YAML parser + project lookup
- `templates/agent-system-prompt.md` — NEW — Copy from C:\Users\Arman\workspace\Jefest\templates\agent-system-prompt.md
- `templates/sdd-template.md` — NEW — Copy from C:\Users\Arman\workspace\Jefest\templates\sdd-template.md
- `templates/sdd-checklist.md` — NEW — Copy from C:\Users\Arman\workspace\Jefest\templates\sdd-checklist.md
- `registry.yaml.example` — NEW — Example registry with 2 sample projects
- `README.md` — NEW — Setup instructions, quick start
- `.gitignore` — NEW — Python + Docker ignores

## Atomic Tasks

1. Create worktree: `git worktree add .worktrees/dispatch-skeleton -b dispatch/skeleton`
2. cd `.worktrees/dispatch-skeleton`

3. Create `VERSION` with content "0.1.0"

4. Create `.gitignore`:
```
__pycache__/
*.pyc
.env
/data/
*.egg-info/
dist/
build/
.venv/
```

5. Create `LICENSE` — full Apache 2.0 text

6. Create `requirements.txt`:
```
mcp>=1.0.0
anthropic>=0.40.0
pydantic>=2.0.0
pyyaml>=6.0
httpx>=0.27.0
aiofiles>=24.0.0
supervisor>=4.2.0
```

7. Create `Dockerfile`:
- Base: python:3.12-slim
- Install: curl, git, nodejs, npm (via apt)
- Install: @anthropic-ai/claude-code (npm global)
- Install: requirements.txt (pip)
- Install: rlm-toolkit[all] (pip, separate layer for caching)
- Install: supervisor (pip)
- Copy jefest/, templates/, skills/
- Copy supervisord.conf, entrypoint.sh
- Create /data, /workspace dirs
- VOLUME ["/data", "/workspace"]
- EXPOSE 8300
- HEALTHCHECK on localhost:8300/health
- ENTRYPOINT ["./entrypoint.sh"]

8. Create `docker-compose.yml`:
```yaml
services:
  jefest:
    build: .
    container_name: jefest-mcp
    restart: unless-stopped
    ports:
      - "${JEFEST_PORT:-8300}:8300"
    volumes:
      - ${WORKSPACE_PATH:-./workspace}:/workspace
      - jefest-data:/data
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JEFEST_REGISTRY=${JEFEST_REGISTRY:-/workspace/registry.yaml}
      - JEFEST_DEFAULT_MODEL=${JEFEST_DEFAULT_MODEL:-sonnet}
      - RLM_EMBEDDING_PROVIDER=${RLM_EMBEDDING_PROVIDER:-fastembed}
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: 4G
volumes:
  jefest-data:
```

9. Create `.env.example`:
```
ANTHROPIC_API_KEY=sk-ant-...
WORKSPACE_PATH=./workspace
JEFEST_PORT=8300
JEFEST_DEFAULT_MODEL=sonnet
RLM_EMBEDDING_PROVIDER=fastembed
```

10. Create `supervisord.conf`:
- Program: rlm — command `rlm-server --host 0.0.0.0 --port 8200 --data-dir /data/rlm --embedding-provider %(ENV_RLM_EMBEDDING_PROVIDER)s`
- Program: jefest — command `python -m jefest.server`
- Both: autorestart=true, redirect_stderr=true, stdout_logfile=/data/logs/%(program_name)s.log
- Create log dirs in entrypoint

11. Create `entrypoint.sh`:
```bash
#!/bin/sh
set -e
mkdir -p /data/rlm /data/logs /data/temp
echo "Starting Jefest MCP Server + RLM"
exec supervisord -c /app/supervisord.conf -n
```

12. Create `jefest/__init__.py`:
```python
__version__ = "0.1.0"
```

13. Create `jefest/config.py`:
- Class `Config` with fields from env vars:
  - ANTHROPIC_API_KEY (required)
  - JEFEST_REGISTRY (default: /workspace/registry.yaml)
  - JEFEST_DEFAULT_MODEL (default: sonnet)
  - JEFEST_PORT (default: 8300)
  - RLM_URL (default: http://localhost:8200)
  - WORKSPACE_PATH (default: /workspace)
  - DATA_DIR (default: /data)
  - TEMPLATES_DIR (default: /app/templates)
  - SKILLS_DIR (default: /app/skills)
- Singleton pattern: `config = Config()`

14. Create `jefest/models.py`:
- Pydantic models: ProjectInfo, SkillInfo, SddContent, DispatchResult, ValidationResult, DispatchStatus, DispatchReport
- IntEnum ExitCode with values from Jefest exit-codes.ps1:
  EC_OK=0, EC_VAL_FORMAT=1, EC_VAL_MISSING_SECTION=2, EC_VAL_AMBIGUOUS=3, EC_VAL_WRONG_LOCATION=16, EC_EXEC_PARTIAL=20, EC_EXEC_FAIL=21

15. Create `jefest/rlm_client.py`:
- Class `RLMClient` with `httpx.AsyncClient`
- Methods: `search_facts(query, top_k)`, `add_fact(content, level, domain)`, `route_context(query)`, `start_session()`, `sync_state()`
- All methods send JSON-RPC 2.0 to RLM_URL/mcp
- Error handling: if RLM unreachable, return empty results (don't crash)

16. Create `jefest/core/__init__.py` — empty

17. Create `jefest/core/registry_loader.py`:
- Class `RegistryLoader`:
  - `load(path)` — read YAML, parse projects section
  - `lookup(query)` — search by name, key, type
  - `list_projects()` — return all
  - `get_project(key)` — return single ProjectInfo
- Use pyyaml. If registry file not found, return empty list.

18. Create `jefest/tools/__init__.py` — empty

19. Create `jefest/tools/skills.py`:
- `list_skills()` tool — scan SKILLS_DIR for */SKILL.md, also scan /workspace/*/. claude/skills/
- Return list of SkillInfo (name, description from first line of SKILL.md, path, source: built-in|project)

20. Create `jefest/tools/registry.py`:
- `registry_lookup(query: str)` — use RegistryLoader.lookup()
- `list_projects()` — use RegistryLoader.list_projects()
- Both return JSON-serializable results

21. Create `jefest/tools/admin.py`:
- `health()` — return {status: ok, version, rlm_status: ok|error, uptime_sec}
- `update_check()` — GET https://api.github.com/repos/OWNER/jefest-mcp/releases/latest, compare with VERSION file. Return {current, latest, has_update}

22. Create `jefest/tools/sdd.py`:
- `create_sdd(project, title, context, approach, files, tasks, acceptance, skills)` — read templates/sdd-template.md, fill placeholders, return markdown string
- `write_sdd(path, content)` — write content to /workspace/{path}, return {written: true, path}

23. Create stub `jefest/tools/dispatch.py`:
- `dispatch(sdd_path, model, profile, force)` — return {"status": "not_implemented", "message": "Dispatch pipeline coming in next release"}
- `cancel_dispatch(dispatch_id)` — same stub

24. Create stub `jefest/tools/validate.py`:
- `validate_sdd(sdd_path)` — return {"status": "not_implemented"}

25. Create stub `jefest/tools/status.py`:
- `get_dispatch_status(dispatch_id)` — stub
- `list_dispatches(limit)` — stub
- `get_result(dispatch_id)` — stub

26. Create `jefest/server.py`:
- Import all tools modules
- Create MCP Server instance
- Register all tools with `@server.tool()` decorators
- Main: `server.run(transport="streamable-http", host="0.0.0.0", port=8300)`
- Use `if __name__ == "__main__"` and also support `python -m jefest.server`
- Add `__main__.py` in jefest/ package for `python -m jefest.server`

27. Copy templates from Jefest:
- `cp C:\Users\Arman\workspace\Jefest\templates\agent-system-prompt.md templates/`
- `cp C:\Users\Arman\workspace\Jefest\templates\sdd-template.md templates/`
- `cp C:\Users\Arman\workspace\Jefest\templates\sdd-checklist.md templates/`
- Adapt paths: replace Windows-specific paths with generic /workspace/ references

28. Create `registry.yaml.example`:
```yaml
projects:
  my-webapp:
    path: /workspace/my-webapp
    type: nodejs
    role: Web application
    default_skills:
      - api-expert
      - testing-patterns
  my-api:
    path: /workspace/my-api
    type: python
    role: Backend API
    default_skills:
      - python-patterns
      - postgres-expert
```

29. Create `README.md`:
- Quick Start (docker-compose up)
- Configuration (.env)
- MCP tools reference (table)
- Adding to Claude Code (.mcp.json)
- Custom skills (mount volume)
- Custom registry (mount volume)
- Development (pip install -e .)

## Acceptance
- All files listed in Files section exist and have valid Python syntax (no import errors)
- `python -c "from jefest.server import server"` succeeds (imports work)
- `python -c "from jefest.config import config"` succeeds
- `python -c "from jefest.models import ExitCode, ProjectInfo"` succeeds
- `python -c "from jefest.rlm_client import RLMClient"` succeeds
- `python -c "from jefest.core.registry_loader import RegistryLoader"` succeeds
- registry.yaml.example is valid YAML
- Dockerfile has no syntax errors: `docker build --check .` or manual review
- All tool stubs have docstrings describing future behavior
- templates/ contains 3 files copied from Jefest

## Finalize
1. Commit all changes: `git add -A && git commit -m "feat: jefest-mcp project skeleton with MCP server, Docker, RLM integration per SDD jefest-mcp-skeleton-20260305"`
2. Push worktree branch: `for remote in $(git remote); do git push $remote dispatch/skeleton; done`
3. Merge to master (from project root): `git -C C:/Users/Arman/workspace/jefest-mcp merge dispatch/skeleton`
4. Push master: `cd C:/Users/Arman/workspace/jefest-mcp && for remote in $(git remote); do git push $remote master; done`
5. Write result-JSON: create `$env:TEMP/jefest-dispatch/result-jefest-mcp.json` with status, tasks_done, tasks_failed, tasks_skipped, escalations
6. Remove worktree: `git -C C:/Users/Arman/workspace/jefest-mcp worktree remove .worktrees/dispatch-skeleton`
7. /exit
