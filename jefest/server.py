from __future__ import annotations
import asyncio
import logging
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.types as types

from .tools.skills import list_skills
from .tools.registry import registry_lookup, list_projects
from .tools.admin import health, update_check
from .tools.sdd import create_sdd, write_sdd
from .tools.dispatch import dispatch, cancel_dispatch
from .tools.validate import validate_sdd
from .tools.status import get_dispatch_status, list_dispatches, get_result
from .config import config

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

server = Server("jefest")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(name="health", description="Server health status and RLM availability", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="update_check", description="Check for new jefest-mcp releases", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="list_skills", description="List all available skills", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="registry_lookup", description="Search projects by name/type/role", inputSchema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}),
        types.Tool(name="list_projects", description="List all registered projects", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="create_sdd", description="Generate an SDD from template", inputSchema={"type": "object", "properties": {"project": {"type": "string"}, "title": {"type": "string"}, "context": {"type": "string"}, "approach": {"type": "string"}, "files": {"type": "string"}, "tasks": {"type": "string"}, "acceptance": {"type": "string"}, "skills": {"type": "string"}}, "required": ["project", "title", "context", "approach", "files", "tasks", "acceptance"]}),
        types.Tool(name="write_sdd", description="Write SDD content to workspace", inputSchema={"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}),
        types.Tool(name="dispatch", description="Dispatch SDD to agent (not yet implemented)", inputSchema={"type": "object", "properties": {"sdd_path": {"type": "string"}, "model": {"type": "string"}, "profile": {"type": "string"}, "force": {"type": "boolean"}}, "required": ["sdd_path"]}),
        types.Tool(name="cancel_dispatch", description="Cancel a running dispatch (not yet implemented)", inputSchema={"type": "object", "properties": {"dispatch_id": {"type": "string"}}, "required": ["dispatch_id"]}),
        types.Tool(name="validate_sdd", description="Validate SDD format (not yet implemented)", inputSchema={"type": "object", "properties": {"sdd_path": {"type": "string"}}, "required": ["sdd_path"]}),
        types.Tool(name="get_dispatch_status", description="Get dispatch status (not yet implemented)", inputSchema={"type": "object", "properties": {"dispatch_id": {"type": "string"}}, "required": ["dispatch_id"]}),
        types.Tool(name="list_dispatches", description="List recent dispatches (not yet implemented)", inputSchema={"type": "object", "properties": {"limit": {"type": "integer"}}}),
        types.Tool(name="get_result", description="Get dispatch result JSON (not yet implemented)", inputSchema={"type": "object", "properties": {"dispatch_id": {"type": "string"}}, "required": ["dispatch_id"]}),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    handlers = {
        "health": lambda a: health(),
        "update_check": lambda a: update_check(),
        "list_skills": lambda a: list_skills(),
        "registry_lookup": lambda a: registry_lookup(a["query"]),
        "list_projects": lambda a: list_projects(),
        "create_sdd": lambda a: create_sdd(**a),
        "write_sdd": lambda a: write_sdd(a["path"], a["content"]),
        "dispatch": lambda a: dispatch(**a),
        "cancel_dispatch": lambda a: cancel_dispatch(a["dispatch_id"]),
        "validate_sdd": lambda a: validate_sdd(a["sdd_path"]),
        "get_dispatch_status": lambda a: get_dispatch_status(a["dispatch_id"]),
        "list_dispatches": lambda a: list_dispatches(a.get("limit", 20)),
        "get_result": lambda a: get_result(a["dispatch_id"]),
    }
    fn = handlers.get(name)
    if not fn:
        raise ValueError(f"Unknown tool: {name}")
    import json
    result = await asyncio.to_thread(fn, arguments)
    return [types.TextContent(type="text", text=json.dumps(result, default=str))]


def main() -> None:
    import asyncio
    from mcp.server.stdio import stdio_server

    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, InitializationOptions(
                server_name="jefest",
                server_version="0.1.0",
                capabilities=server.get_capabilities(notification_options=None, experimental_capabilities={}),
            ))

    asyncio.run(run())


if __name__ == "__main__":
    main()
