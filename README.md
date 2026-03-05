# Jefest MCP Server

Cross-project orchestrator for Claude Code, packaged as a Docker container with MCP interface.

## Quick Start

```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and WORKSPACE_PATH
docker compose up -d
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | required | Anthropic API key |
| `WORKSPACE_PATH` | `./workspace` | Path to your projects |
| `JEFEST_PORT` | `8300` | Host port for MCP server |
| `JEFEST_DEFAULT_MODEL` | `sonnet` | Claude model for dispatch |
| `RLM_EMBEDDING_PROVIDER` | `fastembed` | RLM embedding backend |

## Adding to Claude Code

```json
{
  "mcpServers": {
    "jefest": {
      "url": "http://localhost:8300/mcp"
    }
  }
}
```

## MCP Tools

| Tool | Status | Description |
|---|---|---|
| `health` | stable | Server health + RLM status |
| `update_check` | stable | Check for new releases |
| `list_skills` | stable | List available skills |
| `registry_lookup` | stable | Search projects by query |
| `list_projects` | stable | List all registered projects |
| `create_sdd` | stable | Generate SDD from template |
| `write_sdd` | stable | Write SDD to workspace |
| `dispatch` | stub | Dispatch SDD to agent |
| `validate_sdd` | stub | Validate SDD format |
| `get_dispatch_status` | stub | Get dispatch status |
| `list_dispatches` | stub | List recent dispatches |
| `get_result` | stub | Get dispatch result |

## Custom Registry

```bash
cp registry.yaml.example workspace/registry.yaml
# Edit to add your projects
```

## Custom Skills

Mount a volume with SKILL.md files:
```yaml
volumes:
  - ./my-skills:/app/skills
```

## Development

```bash
pip install -e .
python -m jefest.server
```
