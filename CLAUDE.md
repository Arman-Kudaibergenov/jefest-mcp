# Jefest MCP Server

## Project
Cross-project orchestrator for Claude Code, packaged as Docker container with MCP interface.
Open source (Apache 2.0). Includes embedded RLM (rlm-toolkit).

## Stack
- Python 3.12, mcp library, anthropic SDK, pydantic, httpx, pyyaml
- Docker: python:3.12-slim + nodejs (for claude CLI) + supervisord
- RLM: rlm-toolkit[all] with FastEmbed (CPU)

## Structure
- `jefest/` — Python package (MCP server + tools + core logic)
- `templates/` — agent prompts, SDD templates
- `skills/` — SKILL.md files for domain knowledge injection
- `openspec/specs/` — SDD specifications

## Rules
- Code and comments in English
- All Python, follow PEP 8
- Use async/await for all I/O
- Pydantic models for all tool inputs/outputs
- Config via environment variables (see config.py)
