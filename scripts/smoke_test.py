"""
scripts/smoke_test.py
作用：W2 核心路径冒烟回归，一把跑完 P0-P5 六条路径
运行：先启动服务（uvicorn api.main:app --port 8000），再另开终端执行
     python scripts/smoke_test.py
     BASE_URL=http://127.0.0.1:8001 python scripts/smoke_test.py   # 换端口
退出码：全绿 0，有失败 1（以后接 CI 用得上）
依赖：pip install requests
"""
import json
import os
import sys

import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 30

results = []   # [(是否通过, 用例名, 详情)]


def check(name, fn):
    """执行一个用例并记录结果，单条失败不影响后续用例继续跑"""
    try:
        detail = fn()
        results.append((True, name, detail))
        print(f"✅ {name}  {detail}")
    except AssertionError as e:
        results.append((False, name, str(e)))
        print(f"❌ {name}  {e}")
    except Exception as e:
        results.append((False, name, f"{type(e).__name__}: {e}"))
        print(f"❌ {name}  {type(e).__name__}: {e}")


def p0_health():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200, f"状态码 {r.status_code}"
    return "服务在线"


def p1_chat():
    r = requests.post(f"{BASE_URL}/chat", json={"message": "你好，一句话介绍你自己"}, timeout=TIMEOUT)
    assert r.status_code == 200, f"状态码 {r.status_code}: {r.text[:120]}"
    data = r.json()
    # 后端 /chat 实际返回字段名是 reply
    answer = data.get("reply") or ""
    assert answer.strip(), f"answer 为空，返回体：{data}"
    return f"{len(answer)} 字"


def p2_memory():
    tid = "smoke-memory-001"
    requests.post(f"{BASE_URL}/chat", json={"message": "我叫小罗，请记住", "thread_id": tid}, timeout=TIMEOUT)
    r = requests.post(f"{BASE_URL}/chat", json={"message": "我叫什么名字？", "thread_id": tid}, timeout=TIMEOUT)
    assert r.status_code == 200, f"状态码 {r.status_code}"
    answer = r.json().get("reply") or ""
    assert "罗" in answer, f"没记住名字，回答：{answer[:100]}"
    return "跨请求记忆生效"


def p3_stream():
    frames = 0
    text = ""
    with requests.post(
        f"{BASE_URL}/chat/stream",
        json={"message": "用一句话说明什么是 SSE"},
        stream=True,          # 关键：不一次性收完，才能验证真的是流
        timeout=TIMEOUT,
    ) as r:
        assert r.status_code == 200, f"状态码 {r.status_code}"
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            assert line.startswith("data: "), f"帧格式不对：{line[:60]}"
            try:
                obj = json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                continue
            if obj.get("done"):
                break
            text += obj.get("token", "")
            frames += 1
    # 帧数必须大于 1：只有 1 帧说明被缓冲了，等于假流式
    assert frames > 1, f"只收到 {frames} 帧，可能被中间件缓冲了"
    assert text.strip(), "流式拼接后内容为空"
    return f"{frames} 帧 / 共 {len(text)} 字"


def p4_rag():
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "PUMP-X201 的告警阈值是多少？"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"状态码 {r.status_code}"
    answer = r.json().get("reply") or ""
    assert "[" in answer, f"没有引用标记，回答：{answer[:120]}"
    return "检索命中且带引用"


def p5_refuse():
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "今天北京天气怎么样"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200, f"状态码 {r.status_code}"
    answer = r.json().get("reply") or ""
    keywords = ("没有找到", "知识库", "无法回答", "未收录", "不在", "无法获取", "无法查询", "没有联网", "无法联网")
    assert any(k in answer for k in keywords), f"无关问题没被拒答：{answer[:120]}"
    return "正确拒答"


if __name__ == "__main__":
    print(f"回归目标：{BASE_URL}\n")
    check("P0 服务存活", p0_health)
    check("P1 单轮问答", p1_chat)
    check("P2 多轮记忆", p2_memory)
    check("P3 流式输出", p3_stream)
    check("P4 RAG 带引用", p4_rag)
    check("P5 无关问题拒答", p5_refuse)

    ok = sum(1 for r in results if r[0])
    print(f"\n{'=' * 46}\n通过 {ok}/{len(results)}")
    sys.exit(0 if ok == len(results) else 1)