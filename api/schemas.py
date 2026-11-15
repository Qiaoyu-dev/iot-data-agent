"""API 请求/响应模型（Pydantic v2）

字段契约集中在这里：路由层只负责收发 JSON，校验规则、字段名、描述都在本文件。
前端（web/app.py）和测试（scripts/*）都以这里的字段名为准，改字段名时先改这里。
"""
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints


class ChatRequest(BaseModel):
    """对话入参：空消息、超长消息、纯空白在校验层就拒绝，不进业务逻辑"""
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)] = Field(
        description="用户提问，1-500 字"
    )
    thread_id: str = Field(default="default", max_length=64, description="会话隔离键")


class ChatResponse(BaseModel):
    """一次性回答（POST /chat）的响应体"""
    reply: str = Field(description="模型回答文本")


class HealthResponse(BaseModel):
    """健康检查（GET /health）的响应体"""
    status: str = Field(description="服务状态，固定为 ok")
