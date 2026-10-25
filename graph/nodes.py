"""Agent nodes. Each reads state, returns a small update, and logs a line."""
from pathlib import Path
from typing import List

from langgraph.types import interrupt
from pydantic import BaseModel, Field

from graph.llm import get_structured_llm
from graph.state import BrandState
from tools.social import fetch_trending_topics

GUIDELINES = (
    Path(__file__).resolve().parent.parent / "data" / "brand_guidelines.md"
).read_text(encoding="utf-8").strip()


# ---------- schemas ----------
class TrendVerdict(BaseModel):
    id: int = Field(description="Trend ID exactly as given")
    safe: bool
    reason: str = Field(description="One short sentence citing the guideline")


class SafetyReport(BaseModel):
    verdicts: List[TrendVerdict]


class Concept(BaseModel):
    id: int = Field(description="1, 2 or 3")
    title: str = Field(description="Short name for the concept")
    idea: str = Field(description="2-3 sentences: what the post shows and why it works")
    format: str = Field(description="e.g. meme image, short reel, carousel, photo + caption")
    hook_caption: str = Field(description="One-line caption in the brand voice")


class ConceptSet(BaseModel):
    concepts: List[Concept] = Field(description="Exactly 3 different concepts")


class ConceptChoice(BaseModel):
    best_id: int = Field(description="id of the strongest concept")
    reason: str = Field(description="One sentence on why it wins")


class Assets(BaseModel):
    captions: List[str] = Field(description="2 caption variations in the brand voice")
    image_prompt: str = Field(description="Prompt for a text-to-image model")


# ---------- nodes ----------
def node_culture_radar(state: BrandState) -> dict:
    trends = fetch_trending_topics("reddit", "general")
    return {
        "raw_trends": trends,
        "execution_log": [f"[radar] fetched {len(trends)} trends"],
    }


def node_brand_safety(state: BrandState) -> dict:
    trends = state["raw_trends"]
    trend_lines = "\n".join(f"- id={t['id']}: {t['topic']}" for t in trends)

    llm = get_structured_llm(SafetyReport)
    report: SafetyReport = llm.invoke(
        f"""You are a strict brand safety compliance officer.
For each trending topic below, decide if it is safe for the brand to engage with.
Judge ONLY against the brand guidelines. When unsure, mark it unsafe.
Give a short reason citing the guideline. Return one verdict per id.

Brand Guidelines:
{GUIDELINES}

Trending Topics:
{trend_lines}
"""
    )

    safe_ids = {v.id for v in report.verdicts if v.safe}
    safe = [t for t in trends if t["id"] in safe_ids]
    log = [
        f"[safety] id={v.id} {'SAFE' if v.safe else 'UNSAFE'}: {v.reason}"
        for v in report.verdicts
    ]

    if not safe:
        return {
            "compliance_passed": False,
            "filtered_trend": {},
            "execution_log": log + ["[safety] no safe trends, dropping cycle"],
        }

    chosen = max(safe, key=lambda t: t.get("volume", 0))  # most popular safe trend
    dropped = len(trends) - len(safe)
    return {
        "compliance_passed": True,
        "filtered_trend": chosen,
        "execution_log": log + [f"[safety] dropped {dropped} unsafe, picked '{chosen['topic']}'"],
    }


def node_creative_director(state: BrandState) -> dict:
    trend = state["filtered_trend"]

    # Pydantic model, NOT `dict`: LangChain cannot build a schema from a bare dict.
    llm = get_structured_llm(ConceptSet, temperature=0.7)
    result: ConceptSet = llm.invoke(
        f"""You are the creative director for a small homemade pastries and cakes brand.
The trend below already passed brand safety. Propose exactly 3 DIFFERENT content
concepts that blend this trend with our bakery, in our brand voice.

Brand Guidelines:
{GUIDELINES}

Trending Topic: {trend['topic']}
"""
    )

    concepts = [c.model_dump() for c in result.concepts]
    return {
        "concept_proposals": concepts,
        "execution_log": [f"[creative] proposed {len(concepts)} concepts: "
                          + ", ".join(c["title"] for c in concepts)],
    }


def node_concept_selector(state: BrandState) -> dict:
    concepts = state["concept_proposals"]

    llm = get_structured_llm(ConceptChoice)
    choice: ConceptChoice = llm.invoke(
        f"""You are a senior creative director. Pick the ONE concept that best fits the
brand guidelines and is most likely to engage our audience. Return only its id.

Brand Guidelines:
{GUIDELINES}

Concepts:
{concepts}
"""
    )

    chosen = next((c for c in concepts if c["id"] == choice.best_id), concepts[0])
    return {
        "selected_concept": chosen,
        "execution_log": [f"[selector] picked #{chosen['id']} '{chosen['title']}': {choice.reason}"],
    }


def node_asset_generator(state: BrandState) -> dict:
    concept = state["selected_concept"]

    llm = get_structured_llm(Assets, temperature=0.7)
    assets: Assets = llm.invoke(
        f"""You are the copywriter and art director for a small homemade pastries and cakes brand.
Write 2 caption variations and 1 image-generation prompt for the concept below.
Stay inside the brand guidelines and voice.

Brand Guidelines:
{GUIDELINES}

Concept: {concept}
"""
    )

    return {
        "generated_assets": assets.model_dump(),
        "execution_log": [f"[assets] generated {len(assets.captions)} captions + 1 image prompt"],
    }


def node_human_gate(state: BrandState) -> dict:
    # Pauses the graph. Needs a checkpointer + thread_id (see build.py / main.py).
    human_response = interrupt(
        {
            "task": "Review before publishing",
            "trend": state.get("filtered_trend", {}),
            "concept": state.get("selected_concept", {}),
            "assets": state.get("generated_assets", {}),
            "prompt": "Approve this post for publishing?",
        }
    )

    if isinstance(human_response, dict):
        approval = str(human_response.get("status", "REJECTED")).upper()
    else:
        approval = "APPROVED" if str(human_response).lower() in {"approved", "approve", "yes", "y", "true"} else "REJECTED"

    return {
        "human_approval": approval,
        "execution_log": [f"[human_gate] reviewed by human. Status: {approval}"],
    }


def node_publisher(state: BrandState) -> dict:
    caption = state["generated_assets"]["captions"][0]
    return {
        "execution_log": [f"[publisher] (fake) scheduled post: {caption}"],
    }