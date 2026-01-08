# nodes.py
from langchain_google_genai import ChatGoogleGenerativeAI

from .state import ChatState
from .tools import web_search
from .utils import (
    get_user_history,
    save_user_message,
    cache_search,
    cache_set,
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
)

SYSTEM_PROMPT = """
You are an AI news assistant.
Use the provided web search results when available to answer the user's query, make sure the news is latest to date.
Answer concisely.
After answering, suggest 3 related follow-up topics.
"""


# ---------- Nodes ----------

async def check_cache_node(state: ChatState) -> ChatState:
    hits = cache_search(state["query"], threshold=0.95)
    if hits:
        state["answer"] = hits[0].get("response", "")
        state["is_cached"] = True
    return state


async def load_memory_node(state: ChatState) -> ChatState:
    history = get_user_history(state["user_id"], state.get("chat_id"))
    if history:
        state.setdefault("messages", [])
        state["messages"].append(
            {"role": "system", "content": f"Previous conversation:\n{history}"}
        )
    return state


from .pubsub import publish_event

async def search_node(state: ChatState) -> ChatState:
    await publish_event(
        state["user_id"],
        {
            "type": "search_start",
            "query": state["query"],
            "chat_id": state.get("chat_id"),
        }
    )

    results = await web_search(state["query"])
    state["search_results"] = results

    await publish_event(
        state["user_id"],
        {
            "type": "search_results",
            "results": results,
            "chat_id": state.get("chat_id"),
        }
    )

    return state


from .pubsub import publish_event

async def generate_node(state: ChatState) -> ChatState:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(state.get("messages", []))

    if state.get("search_results"):
        messages.append(
            {
                "role": "system",
                "content": "Search results:\n" + "\n".join(state["search_results"]),
            }
        )

    messages.append({"role": "user", "content": state["query"]})

    final_text = ""

    async for chunk in llm.astream(messages):
        token = chunk.content or ""
        final_text += token
        try:
            print(f"[generate_node] token chunk={repr(token)[:200]}")
        except Exception:
            pass

        await publish_event(
            state["user_id"],
            {
                "type": "token",
                "value": token,
                "chat_id": state.get("chat_id"),
            }
        )

    followups = [
        "Latest updates on this topic",
        "Key companies involved",
        "Why this matters in the next 6 months",
    ]

    await publish_event(
        state["user_id"],
        {
            "type": "done",
            "chat_id": state.get("chat_id"),
        }
    )

    state["answer"] = final_text
    state["follow_up_topics"] = followups

    save_user_message(state["user_id"], state.get("chat_id"), "User", state["query"])
    save_user_message(state["user_id"], state.get("chat_id"), "AI", final_text)
    cache_set(prompt=state["query"], response=final_text)

    return state
