"""异步并发 + 超时重试实验室
运行：python tools/async_lab.py
实验1：串行 vs asyncio.gather 并发调 LLM，计时对比
实验2：httpx 异步客户端 + 超时 + 指数退避重试
"""
import asyncio
import os
import time
import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()  # 从 .env 读 DEEPSEEK_API_KEY
llm = ChatOpenAI(
    model="deepseek-chat", temperature=0.2,
    base_url="https://api.deepseek.com",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)

async def ask(q: str) -> str:
    resp = await llm.ainvoke(q)
    return resp.content

# ---------- 实验1：串行 vs 并发 ----------
async def demo_gather():
    qs = [
        "用一句话解释温度传感器",
        "用一句话解释湿度传感器",
        "用一句话解释压力传感器",
    ]
    t0 = time.perf_counter()
    for q in qs:
        await ask(q)                    # 串行：一个等一个
    serial = time.perf_counter() - t0

    t0 = time.perf_counter()
    await asyncio.gather(*(ask(q) for q in qs))  # 并发：一起发出去
    parallel = time.perf_counter() - t0

    print(f"串行耗时：{serial:.1f}s")
    print(f"并发耗时：{parallel:.1f}s")
    # 预期：并发 ≈ 最慢那一个的耗时，串行 ≈ 三个之和

# ---------- 实验2：超时 + 指数退避重试 ----------
async def demo_retry():
    for attempt in range(3):          # 最多试 3 次
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5.0)   # 5s 超时预算
            ) as client:
                r = await client.get("https://api.deepseek.com")
                print(f"请求成功，状态码 {r.status_code}")
                return
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            wait = 2 ** attempt               # 指数退避：1s → 2s → 4s
            print(f"第{attempt+1}次失败（{type(e).__name__}），{wait}s 后重试")
            await asyncio.sleep(wait)     # 异步 sleep，不阻塞事件循环
    print("三次都失败，放弃并上报")

if __name__ == "__main__":
    asyncio.run(demo_gather())
    print("-" * 40)
    asyncio.run(demo_retry())