# state.py
from typing import TypedDict, List


class ChatState(TypedDict, total=False):
    # identity
    user_id: str
    chat_id: str
    query: str

    # conversation
    messages: List[dict]

    # tools
    search_results: List[str]

    # outputs
    answer: str
    follow_up_topics: List[str]

    # cache
    is_cached: bool

    # streaming (NEW)
    stream_id: str
