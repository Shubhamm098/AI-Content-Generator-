"""Real trend sources for the Culture Radar.

Sources (all free, no API keys):
  - Reddit top posts of the week (one combined RSS request; rank = popularity)
  - Google News RSS, India edition (popularity = rank in the feed)

Output shape is unchanged, so no graph/node code needs to change:
  {"id", "topic", "platform", "category", "volume", "url"}

If every live source fails (blocked network, no internet), it falls back to
the old hardcoded trends so the graph still runs.
"""
import re
import time
from html import unescape
from typing import Any, Dict, List
from urllib.parse import quote_plus

import feedparser
import httpx

# ---------- config: edit these to tune what the radar listens to ----------
SUBREDDITS = ["Baking", "cakedecorating", "food"]
NEWS_QUERIES = ["viral cake trend when:7d", "dessert trend when:7d", "bakery trend India when:7d"]
REDDIT_LIMIT = 15         # posts from the combined subreddit feed
NEWS_LIMIT = 6            # headlines per query
MAX_TRENDS = 12           # keep the LLM prompt small (free-tier friendly)
MAX_TOPIC_CHARS = 140
TIMEOUT = 8.0
# Reddit asks for a descriptive UA like "platform:app:version (by /u/username)".
# Put your own Reddit username here; generic UAs are often rejected with 403/429.
HEADERS = {"User-Agent": "python:living-brand-radar:0.1 (by /u/your_reddit_username)"}


# ---------- helpers ----------
def _clean(text: str) -> str:
    """Strip HTML/newlines and cap length. Scraped text goes into LLM prompts, so keep it tame."""
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_TOPIC_CHARS]


def _scale(items: List[Dict[str, Any]], key: str) -> None:
    """Rescale each source's raw popularity to 0-100000 so sources are comparable."""
    top = max((i[key] for i in items), default=0) or 1
    for i in items:
        i["volume"] = int(i[key] / top * 100_000)


# ---------- sources ----------
def _describe(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        return f"HTTP {e.response.status_code}"
    return type(e).__name__


def _fetch_reddit(category: str) -> List[Dict[str, Any]]:
    """ONE request for all subreddits (r/A+B+C combined feed).

    Reddit throttles unauthenticated clients by IP, so several quick requests
    trigger HTTP 429 (and the JSON endpoint is usually 403). A single combined
    RSS request avoids both. RSS has no scores, so rank in the feed = popularity.
    """
    combined = "+".join(SUBREDDITS)
    url = f"https://www.reddit.com/r/{combined}/top/.rss?t=week&limit={REDDIT_LIMIT}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        if r.status_code == 429:  # rate limited: wait once, then retry
            wait = min(float(r.headers.get("retry-after", 8)), 15.0)
            print(f"[social] reddit rate limited, waiting {wait:.0f}s and retrying")
            time.sleep(wait)
            r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        feed = feedparser.parse(r.content)
    except Exception as e:
        print(f"[social] reddit failed ({_describe(e)}), skipping reddit this cycle")
        return []

    out = [
        {
            "topic": _clean(e.get("title", "")),
            "platform": "reddit",
            "category": category,
            "url": e.get("link", ""),
            "raw": REDDIT_LIMIT - rank,
        }
        for rank, e in enumerate(feed.entries[:REDDIT_LIMIT])
    ]
    _scale(out, "raw")
    return out


def _fetch_news(category: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for q in NEWS_QUERIES:
        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            r = httpx.get(url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True)
            r.raise_for_status()
            feed = feedparser.parse(r.content)
        except Exception as e:
            print(f"[social] news '{q}' failed: {_describe(e)}")
            continue
        for rank, e in enumerate(feed.entries[:NEWS_LIMIT]):
            title = re.sub(r"\s+-\s+[^-]+$", "", e.get("title", ""))  # drop " - Publisher"
            out.append({
                "topic": _clean(title),
                "platform": "news",
                "category": category,
                "url": e.get("link", ""),
                "raw": NEWS_LIMIT - rank,  # no popularity number, so higher rank = bigger
            })
    _scale(out, "raw")
    return out


def _fallback(platform: str, category: str) -> List[Dict[str, Any]]:
    print("[social] all live sources failed, using hardcoded fallback trends")
    topics = [
        ("Viral tragedy news cycle meme", 120_000),
        ("Bento-box mini cakes with funny handwritten messages", 98_000),
        ("Birthday cake reveal reactions", 75_000),
        ("Guilt-free dessert 'cheat day' diet shaming trend", 60_000),
        ("Baking fails: cake that collapsed", 55_000),
    ]
    return [
        {"id": i, "topic": t, "platform": platform, "category": category, "volume": v, "url": ""}
        for i, (t, v) in enumerate(topics, start=1)
    ]


# ---------- public API ----------
def fetch_trending_topics(platform: str = "all", category: str = "general") -> List[Dict[str, Any]]:
    """platform: "reddit", "news" or "all"."""
    items: List[Dict[str, Any]] = []
    if platform in ("reddit", "all"):
        items += _fetch_reddit(category)
    if platform in ("news", "all"):
        items += _fetch_news(category)

    # drop empties and duplicate topics
    seen, unique = set(), []
    for i in items:
        key = i["topic"].lower()
        if i["topic"] and key not in seen:
            seen.add(key)
            unique.append(i)

    if not unique:
        return _fallback(platform, category)

    unique.sort(key=lambda i: i["volume"], reverse=True)
    unique = unique[:MAX_TRENDS]
    return [
        {"id": n, "topic": i["topic"], "platform": i["platform"], "category": i["category"],
         "volume": i["volume"], "url": i["url"]}
        for n, i in enumerate(unique, start=1)
    ]


if __name__ == "__main__":
    # Quick manual test:  python -m tools.social
    for t in fetch_trending_topics("all", "general"):
        print(f"{t['id']:>2} [{t['platform']:<6}] {t['volume']:>6}  {t['topic']}")