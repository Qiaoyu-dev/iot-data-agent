# api/errors.py —— 统一异常响应与请求日志
# 目标：任何错误都返回同一结构 {code, message, request_id}，前端只认这一套
import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# 日志格式：时间 | 级别 | 模块 | 内容。统一格式才能用 grep 检索
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("iot-agent")


def install_error_handlers(app: FastAPI) -> None:
    """挂载中间件与全局异常处理器，main.py 里调用一次即可"""

    # ---- 中间件：给每个请求发一个 request_id，并记录耗时 ----
    # request_id 是联调排障的命根子：前端提示里带上它，后端日志里搜它，一眼定位
    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        rid = uuid.uuid4().hex[:8]
        request.state.request_id = rid
        t0 = time.perf_counter()
        response = await call_next(request)
        cost_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            f"rid={rid} {request.method} {request.url.path} "
            f"-> {response.status_code} {cost_ms:.0f}ms"
        )
        response.headers["X-Request-Id"] = rid   # 响应头带回，前端可读
        return response

    # ---- 异常处理器 1：参数校验失败（422） ----
    @app.exception_handler(RequestValidationError)
    async def on_validation_error(request: Request, exc: RequestValidationError):
        rid = getattr(request.state, "request_id", "-")
        logger.warning(f"rid={rid} 参数校验失败: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": "输入不合法（消息需 1-500 字，不能为纯空白）",
                     "detail": exc.errors(), "request_id": rid},
        )

    # ---- 异常处理器 2：兜底所有未捕获异常（500） ----
    # 关键：日志里记完整堆栈，返回给前端只给一句人话 + request_id
    @app.exception_handler(Exception)
    async def on_unhandled_error(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", "-")
        logger.exception(f"rid={rid} 未捕获异常: {exc}")   # exception 会带完整堆栈
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务内部错误，请稍后重试",
                     "request_id": rid},
        )
