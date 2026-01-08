import json
from .redis_async import redis_async

CHANNEL_PREFIX = "agent-stream"

def channel(user_id: str) -> str:
    return f"{CHANNEL_PREFIX}:{user_id}"

async def publish_event(user_id: str, payload: dict):
    data = json.dumps(payload)
    try:
        # Lightweight debug logging to help trace streaming
        print(f"[pubsub] publish -> channel={channel(user_id)} payload={data}")
    except Exception:
        pass

    await redis_async.publish(
        channel(user_id),
        data,
    )
