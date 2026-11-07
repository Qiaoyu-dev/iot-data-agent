"""
api/main.py
作用：FastAPI 入口，把 Agent 图暴露成 HTTP 接口
     POST /chat   发消息给 Agent（自动选择调工具）
     GET  /health 健康检查
运行：在仓库根目录执行  uvicorn api.main:app --reload --port 8000
     （--reload：改代码自动重启，开发期神器）
文档：起服务后浏览器打开 http://localhost:8000/docs 看自动生成的接口文档
"""
from fastapi import FastAPI
from pydantic import BaseModel

from agent.graph import graph   # 11.3 建好的 LangGraph 主图

app = FastAPI(title="IoT Data Agent", version="0.1.0")


class ChatRequest(BaseModel):
    """请求体：pydantic 自动校验，缺字段直接返回 422"""
    message: str
    thread_id: str = "default"   # 会话ID：同一 id 共享对话记忆


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@app.get("/health")
def health():
    """健康检查：部署/联调时先 curl 它确认服务活着"""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """核心接口：把用户消息交给 Agent 图，返回最终回答"""
    # thread_id 交给 MemorySaver：同一 thread_id 的多轮对话有记忆
    config = {"configurable": {"thread_id": req.thread_id}}
    result = graph.invoke(
        {"messages": [("user", req.message)]},
        config=config,
    )
    # messages 列表最后一条就是 Agent 的最终回答
    reply = result["messages"][-1].content
    return ChatResponse(reply=reply, thread_id=req.thread_id)