from langgraph.graph import StateGraph, START, END
from state import GraphState
from nodes import (
    load_document,
    extract_toc,
    generate_draft,
    generate_demo_ideas,
    aggregate_post
)


def should_continue(state: GraphState):
    """
    Conditional edge logic to determine if we should continue generating posts or end.
    """
    current_index = state["current_index"]
    series_toc = state["series_toc"]
    
    if current_index < len(series_toc):
        return "continue"
    else:
        return "end"


def get_graph():
    """
    Constructs and compiles the LangGraph.
    """
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("load_document", load_document)
    workflow.add_node("extract_toc", extract_toc)
    workflow.add_node("generate_draft", generate_draft)
    workflow.add_node("generate_demo_ideas", generate_demo_ideas)
    workflow.add_node("aggregate_post", aggregate_post)

    # Add Edges
    workflow.add_edge(START, "load_document")
    workflow.add_edge("load_document", "extract_toc")
    workflow.add_edge("extract_toc", "generate_draft")
    workflow.add_edge("generate_draft", "generate_demo_ideas")
    workflow.add_edge("generate_demo_ideas", "aggregate_post")
    
    # Conditional Edge
    workflow.add_conditional_edges(
        "aggregate_post",
        should_continue,
        {
            "continue": "generate_draft",
            "end": END
        }
    )

    return workflow.compile()
