"""Hardcoded trend data. Replaced by the real social-listening MCP server later."""
from typing import Any, Dict, List


def fetch_trending_topics(platform: str = "reddit", category: str = "general") -> List[Dict[str, Any]]:
    return [
        {"id": 1, "topic": "Viral tragedy news cycle meme", "platform": platform,
         "category": category, "volume": 120_000, "sensitive": True},   # unsafe on purpose
        {"id": 2, "topic": "Monday coffee hits different", "platform": platform,
         "category": category, "volume": 98_000, "sensitive": True},
        {"id": 3, "topic": "Retro pixel-art glow-up challenge", "platform": platform,
         "category": category, "volume": 75_000, "sensitive": True},
    ]