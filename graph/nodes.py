"""Stub nodes. Each reads state, returns a small update, and logs a line."""
from graph.state import BrandState
from tools.social import fetch_trending_topics


def node_culture_radar(state: BrandState) -> dict:
    trends = fetch_trending_topics("reddit", "general")
    return {
        "raw_trends": trends,
        "execution_log": [f"[radar] fetched {len(trends)} trends"],
    }


def node_brand_safety(state: BrandState) -> dict:
    # STUB rule: first trend not flagged as sensitive wins. Replace with an LLM judge later.
    safe = [t for t in state["raw_trends"] if not t.get("sensitive")]
    if not safe:
        return {
            "compliance_passed": False,
            "filtered_trend": {},
            "execution_log": ["[safety] no safe trends, dropping cycle"],
        }
    chosen = safe[0]
    dropped = len(state["raw_trends"]) - len(safe)
    return {
        "compliance_passed": True,
        "filtered_trend": chosen,
        "execution_log": [f"[safety] dropped {dropped} unsafe, picked '{chosen['topic']}'"],
    }


def node_creative_director(state: BrandState) -> dict:
    topic = state["filtered_trend"]["topic"]
    concepts = [
        {"id": i, "idea": f"Concept {i}: brand x '{topic}'"} for i in (1, 2, 3)
    ]
    return {
        "concept_proposals": concepts,
        "selected_concept": concepts[0],
        "execution_log": [f"[creative] proposed {len(concepts)} concepts, selected #1"],
    }


def node_asset_generator(state: BrandState) -> dict:
    concept = state["selected_concept"]["idea"]
    return {
        "generated_assets": {
            "captions": [f"Caption A for {concept}", f"Caption B for {concept}"],
            "image_prompt": f"Meme-style image for: {concept}",
        },
        "execution_log": ["[assets] generated 2 captions + 1 image prompt"],
    }


def node_human_gate(state: BrandState) -> dict:
    # STUB: auto-approve. Becomes a LangGraph interrupt() later.
    return {
        "human_approval": "APPROVED",
        "execution_log": ["[human_gate] auto-approved (stub)"],
    }


def node_publisher(state: BrandState) -> dict:
    caption = state["generated_assets"]["captions"][0]
    return {
        "execution_log": [f"[publisher] (fake) scheduled post: {caption}"],
    }