"""Hardcoded trend data. Replaced by the real social-listening MCP server later."""
from typing import Any, Dict, List


def fetch_trending_topics(platform: str = "reddit", category: str = "general") -> List[Dict[str, Any]]:
    return [
        {"id": 1, "topic": "Viral tragedy news cycle meme", "platform": platform,
         "category": category, "volume": 120_000, "sensitive": True},   # unsafe on purpose
        {"id": 2, "topic": "Bento-box mini cakes with funny handwritten messages", "platform": platform,
         "category": category, "volume": 98_000, "sensitive": False},
        {"id": 3, "topic": "Birthday cake reveal reactions", "platform": platform,
         "category": category, "volume": 75_000, "sensitive": False},
        {"id": 4, "topic": "Guilt-free dessert 'cheat day' diet shaming trend", "platform": platform,
         "category": category, "volume": 60_000, "sensitive": True},    # tests the diet-culture rule
        {"id": 5, "topic": "Baking fails: cake that collapsed", "platform": platform,
         "category": category, "volume": 55_000, "sensitive": False},
    ]