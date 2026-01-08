# agent.py
import os
from langgraph.graph import StateGraph, END
from .utils.state import ChatState
from .utils.nodes import (
    check_cache_node,
    load_memory_node,
    search_node,
    generate_node,
)

# ---------------- Graph ----------------

graph = StateGraph(ChatState)

graph.add_node("check_cache", check_cache_node)
graph.add_node("load_memory", load_memory_node)
graph.add_node("search", search_node)
graph.add_node("generate", generate_node)

graph.set_entry_point("check_cache")

graph.add_conditional_edges(
    "check_cache",
    lambda s: "cached" if s.get("is_cached") else "continue",
    {
        "cached": END,
        "continue": "load_memory",
    },
)

graph.add_edge("load_memory", "search")
graph.add_edge("search", "generate")
graph.add_edge("generate", END)

app = graph.compile()


async def run_chat(message: str, user_id: str, chat_id: str | None = None) -> dict:
    thread_id = chat_id or "default"
    state: ChatState = {
        "query": message,
        "user_id": user_id,
        "chat_id": thread_id,
        "messages": [],
        "stream_id": f"{user_id}:{thread_id}",
    }

    result = await app.ainvoke(state)

    return {
        "answer": result.get("answer", ""),
        "search_results": result.get("search_results", []),
        "follow_up_topics": result.get("follow_up_topics", []),
        "cached": result.get("is_cached", False),
        "chat_id": thread_id,
    }
