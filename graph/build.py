from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    node_asset_generator,
    node_brand_safety,
    node_culture_radar,
    node_creative_director,
    node_human_gate,
    node_publisher
)

from graph.state import BrandState

def route_after_safety(state:BrandState) -> str:
    return "creative" if state["compliance_passed"] else END

def route_after_human(state: BrandState) -> str:
    return "publisher" if state["human_approval"] == "APPROVED" else END

def build_graph():
    g = StateGraph(BrandState)

    g.add_node("radar", node_culture_radar)
    g.add_node("safety", node_brand_safety)
    g.add_node("creative", node_creative_director)
    g.add_node("human", node_human_gate)
    g.add_node("publisher", node_publisher)
    g.add_node("assets", node_asset_generator)

    g.add_edge(START, "radar")
    g.add_edge("radar", "safety")
    g.add_conditional_edges("safety", route_after_safety, {"creative": "creative", END: END})
    g.add_edge("creative", "assets")
    g.add_edge("assets", "human")
    g.add_conditional_edges("human", route_after_human, {"publisher": "publisher", END: END})
    g.add_edge("publisher", END)

    return g.compile()