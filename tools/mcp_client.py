"""Tiny MCP client: launches an MCP server over stdio, calls one tool, returns the result."""
import asyncio
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parent.parent
TIMEOUT_SECONDS = 60
SOCIAL_SERVER = "mcp_servers.social_listening"


def _server_params(module: str) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", module],
        env=dict(os.environ),
        cwd=str(ROOT),
    )


def _session(read, write) -> ClientSession:
    return ClientSession(read, write, read_timeout_seconds=float(TIMEOUT_SECONDS))


def _attr(obj, *names, default=None):
    for n in names:
        v = getattr(obj, n, None)
        if v is not None:
            return v
    return default


async def _call_tool(module: str, tool: str, arguments: Dict[str, Any]) -> Any:
    async with stdio_client(_server_params(module)) as (read, write):
        async with _session(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)

            if _attr(result, "is_error", "isError", default=False):
                msg = result.content[0].text if result.content else "Unknown error"
                raise RuntimeError(f"Tool call failed: {msg}")

            structured = _attr(result, "structured_content", "structuredContent")
            if structured is not None:
                if isinstance(structured, dict):
                    return structured.get("result", structured)
                return structured

            if result.content and getattr(result.content[0], "text", None):
                return json.loads(result.content[0].text)
            return None


async def _list_tools(module: str):
    async with stdio_client(_server_params(module)) as (read, write):
        async with _session(read, write) as session:
            await session.initialize()
            return (await session.list_tools()).tools


def call_tool(module: str, tool: str, arguments: Dict[str, Any]) -> Any:
    return asyncio.run(
        asyncio.wait_for(_call_tool(module, tool, arguments), TIMEOUT_SECONDS)
    )


def list_tools(module: str):
    return asyncio.run(asyncio.wait_for(_list_tools(module), TIMEOUT_SECONDS))


def fetch_trending_topics(platform: str = "all", category: str = "general") -> List[Dict[str, Any]]:
    """Fetch trending topics from social media platforms."""
    data = call_tool(
        SOCIAL_SERVER,
        "fetch_trending_topics",
        {"platform": platform, "category": category},
    )
    if isinstance(data, list):
        return data
    return (data or {}).get("trends", [])


if __name__ == "__main__":
    for t in list_tools(SOCIAL_SERVER):
        args = list((t.input_schema or {}).get("properties", {}))
        print(f"{t.name}: {t.description}" + (f" (args: {', '.join(args)})" if args else ""))

    for t in fetch_trending_topics("all", "general")[:5]:
        print(f"{t['id']:>2} [{t['platform']:<6}] {t['volume']:>6}  {t['topic']}")