# api/stream.py
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from news_agent.utils.redis_async import redis_async
from news_agent.utils.pubsub import channel

router = APIRouter()

@router.get("/api/stream/{user_id}")
async def stream(user_id: str):
    pubsub = redis_async.pubsub()
    await pubsub.subscribe(channel(user_id))

    async def event_generator():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
        finally:
            await pubsub.unsubscribe()
            await pubsub.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
