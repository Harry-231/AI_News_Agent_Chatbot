# utils.py
import json
import os
import redis
from dotenv import load_dotenv
from langcache import LangCache

load_dotenv()

# ---------------- Redis ----------------

REDIS_URL = os.getenv("REDIS_URL")
redis_client = redis.Redis.from_url(REDIS_URL) if REDIS_URL else None


def _chat_key(user_id: str, chat_id: str | None = None) -> str:
    suffix = chat_id or "default"
    return f"chat:{user_id}:{suffix}"


def get_user_history(user_id: str, chat_id: str | None = None, limit: int = 6) -> str:
    if not redis_client or not user_id:
        return ""

    try:
        items = redis_client.lrange(_chat_key(user_id, chat_id), 0, limit - 1)
        history_lines = []
        for raw in reversed(items):
            try:
                decoded = raw.decode()
            except Exception:
                decoded = str(raw)
            try:
                obj = json.loads(decoded)
                role = obj.get("role", "User")
                content = obj.get("content", "")
                history_lines.append(f"{role}: {content}")
            except Exception:
                history_lines.append(decoded)
        return "\n".join(history_lines)
    except Exception:
        return ""


def save_user_message(user_id: str, chat_id: str | None, role: str, content: str):
    if not redis_client or not user_id:
        return

    try:
        redis_client.lpush(
            _chat_key(user_id, chat_id),
            json.dumps({"role": role, "content": content}),
        )
        redis_client.ltrim(_chat_key(user_id, chat_id), 0, 19)
    except Exception:
        pass


# ---------------- LangCache ----------------

lang_cache = None
try:
    lang_cache = LangCache(
        server_url=os.getenv("LANGCACHE_SERVER_URL"),
        cache_id=os.getenv("CACHE_ID"),
        api_key=os.getenv("LANGCACHE_API_KEY"),
    )
except Exception:
    lang_cache = None


def cache_search(prompt: str, threshold: float = 0.95):
    if not lang_cache:
        return None

    res = lang_cache.search(prompt=prompt, similarity_threshold=threshold)
    hits = getattr(res, "hits", None)
    return hits if hits else None


def cache_set(prompt: str, response: str) -> bool:
    if not lang_cache:
        return False
    try:
        lang_cache.set(prompt=prompt, response=response)
        return True
    except Exception:
        return False
