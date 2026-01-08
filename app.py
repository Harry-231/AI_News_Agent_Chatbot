# app.py
import os
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from news_agent.agent import run_chat
from api.stream import router as stream_router

app = FastAPI(title="Deepkernels AI News Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)

# -------- Models --------

class ChatRequest(BaseModel):
    message: str
    user_id: str
    chat_id: str | None = None


# -------- Endpoint --------

@app.post("/api/chat")
async def chat(req: ChatRequest, response: Response):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if not req.user_id.strip():
        raise HTTPException(status_code=400, detail="User id is required")

    # Helps the frontend proxy confirm it's talking to the correct backend.
    response.headers["X-AI-News-Agent"] = "1"

    result = await run_chat(req.message, req.user_id, req.chat_id)

    return {
        "answer": result["answer"],
        "search_results": result["search_results"],
        "follow_up_topics": result["follow_up_topics"],
        "cached": result["cached"],
        "chat_id": result["chat_id"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
