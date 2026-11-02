from typing import Any, Dict


try:
    from mcp.server.mcpserver import MCPServer as _Server
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server

from tools.social import fetch_trending_topics as _fetch

mcp = _Server(name="social_listening")


@mcp.tool()
def fetch_trending_topics(
   platform: str = "all", category: str = "general") -> Dict[str, Any]:
    """Fetch trending topics from social media platforms.

    Args:
        platform (str): The platform to fetch trends from. Options: "reddit", "news", or "all".
        category (str): The category of trends to fetch. Default is "general".

    Returns:
        Dict[str, Any]: A dictionary containing the fetched trends.
    """
    trends = _fetch(platform, category)
    return {"trends": trends}

if __name__ == "__main__":
    mcp.run(transport="stdio", port=8000, debug=True)
