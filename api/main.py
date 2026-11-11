"""IoT 数据分析 Agent · FastAPI 异步入口 v2
运行：uvicorn api.main:app --reload
改动：路由全部 async 化；graph.invoke → graph.ainvoke；新增 SSE 流式端点
"""
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessageChunk
from agent.graph import graph

app = FastAPI(title="IoT 数据分析 Agent")

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

# ---------- 健康检查 ----------
@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------- 一次性回答（异步版） ----------
@app.post("/chat")
async def chat(req: ChatRequest):
    # 同步 graph.invoke 会阻塞事件循环，必须用 ainvoke（async 版）
    result = await graph.ainvoke(
        {"messages": [("user", req.message)]},
        config={"configurable": {"thread_id": req.thread_id}},
    )
    return {"reply": result["messages"][-1].content}

# ---------- SSE 流式回答（逐字返回） ----------
@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    async def event_gen():
        # astream(stream_mode="messages") 逐 token 产出 (消息块, 元数据)
        async for chunk, _meta in graph.astream(
            {"messages": [("user", req.message)]},
            config={"configurable": {"thread_id": req.thread_id}},
            stream_mode="messages",
        ):
            # 只转发 AI 回答的 token；工具结果(ToolMessage)等不流向用户
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                # SSE 协议格式：每帧 "data: ...\n\n"
                # json.dumps 保证中文/换行/引号不会撑破 SSE 帧
                yield f"data: {json.dumps({'token': chunk.content}, ensure_ascii=False)}\n\n"
        yield 'data: {"done": true}\n\n'  # 结束帧：前端收到它就收尾
    return StreamingResponse(event_gen(), media_type="text/event-stream")