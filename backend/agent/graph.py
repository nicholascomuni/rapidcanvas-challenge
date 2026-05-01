from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import fetch_post_node, vision_node, analyze_node, search_node, synthesize_node


def should_run_vision(state: AgentState) -> str:
    if state.get("image_url"):
        return "vision"
    return "analyze"


def should_search_more(state: AgentState) -> str:
    if state.get("iteration_count", 0) < 2 and len(state.get("search_results", [])) < 3:
        return "search"
    return "synthesize"


builder = StateGraph(AgentState)
builder.add_node("fetch_post", fetch_post_node)
builder.add_node("vision", vision_node)
builder.add_node("analyze", analyze_node)
builder.add_node("search", search_node)
builder.add_node("synthesize", synthesize_node)

builder.set_entry_point("fetch_post")
builder.add_conditional_edges(
    "fetch_post",
    should_run_vision,
    {"vision": "vision", "analyze": "analyze"},
)
builder.add_edge("vision", "analyze")
builder.add_edge("analyze", "search")
builder.add_conditional_edges(
    "search",
    should_search_more,
    {"search": "search", "synthesize": "synthesize"},
)
builder.add_edge("synthesize", END)

graph = builder.compile()
