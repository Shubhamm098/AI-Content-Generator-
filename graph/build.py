import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    node_asset_generator,
    node_brand_safety,
    node_concept_selector,
    node_creative_director,
    node_culture_radar,
    node_human_gate,
    node_publisher,
)
from graph.state import BrandState


def route_after_safety(state: BrandState) -> str:
    return "creative" if state["compliance_passed"] else END


def route_after_human(state: BrandState) -> str:
    return "publisher" if state["human_approval"] == "APPROVED" else END


def build_graph(db_path: str | None = None):
    g = StateGraph(BrandState)

    g.add_node("radar", node_culture_radar)
    g.add_node("safety", node_brand_safety)
    g.add_node("creative", node_creative_director)
    g.add_node("selector", node_concept_selector)
    g.add_node("assets", node_asset_generator)
    g.add_node("human_gate", node_human_gate)
    g.add_node("publisher", node_publisher)

    g.add_edge(START, "radar")
    g.add_edge("radar", "safety")
    g.add_conditional_edges("safety", route_after_safety, {"creative": "creative", END: END})
    g.add_edge("creative", "selector")
    g.add_edge("selector", "assets")
    g.add_edge("assets", "human_gate")
    g.add_conditional_edges("human_gate", route_after_human, {"publisher": "publisher", END: END})
    g.add_edge("publisher", END)

    # Persistent checkpointer: paused runs survive closing the terminal.
    # Tip: if your project lives in a OneDrive folder, point CHECKPOINT_DB at a
    # non-synced path (e.g. C:\\Users\\<you>\\living_brand.db) to avoid file-lock issues.
    path = db_path or os.getenv("CHECKPOINT_DB", "checkpoints.db")
    conn = sqlite3.connect(path, check_same_thread=False)
    return g.compile(checkpointer=SqliteSaver(conn))