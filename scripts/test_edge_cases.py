"""
scripts/test_edge_cases.py
作用：周一联调边界用例自动化（7 条自动化 + 3 条手工故障用例）
运行：1) 先启动后端：uvicorn api.main:app --port 8000
     2) python scripts/test_edge_cases.py
退出码：全绿 0，有失败 1（以后接 CI 用）
依赖：pip install requests
"""
import os
import sys

import requests

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = 60

# (用例名, 请求体, 期望状态码)
CASES = [
    ("1 空消息",        {"message": "", "thread_id": "t1"},                      422),
    ("2 超长消息",      {"message": "a" * 5000, "thread_id": "t1"},             422),
    ("3 纯空白",        {"message": "   ", "thread_id": "t1"},                  422),
    ("4 特殊字符",      {"message": "温度🔥<script>alert(1)</script>", "thread_id": "t1"}, 200),
    ("5 缺thread_id",   {"message": "TEMP-001 温度多少"},                    200),
    ("6 thread_id超长", {"message": "hi", "thread_id": "x" * 100},           422),
    ("7 字段名写错",    {"msg": "hi"},                                     422),
]

# 错误响应必须带的三个字段
REQUIRED_KEYS = ("code", "message", "request_id")

# 响应体里绝不能出现的东西（出现即等于把堆栈漏给前端）
LEAK_MARKERS = ("Traceback", "site-packages", "File \"")


def run():
    passed = failed = 0
    for name, body, expect in CASES:
        try:
            r = requests.post(f"{BASE}/chat", json=body, timeout=TIMEOUT)
        except requests.exceptions.ConnectionError:
            print("❌ 连不上后端，先启动：uvicorn api.main:app --port 8000")
            return False

        problems = []

        # 断言 1：状态码符合预期
        if r.status_code != expect:
            problems.append(f"状态码 {r.status_code}，期望 {expect}")

        # 断言 2：错误响应必须是统一结构
        if r.status_code >= 400:
            try:
                data = r.json()
            except ValueError:
                data = {}
                problems.append("错误响应不是 JSON")
            for k in REQUIRED_KEYS:
                if k not in data:
                    problems.append(f"缺字段 {k}")

        # 断言 3：绝不能把堆栈泄漏给前端
        for marker in LEAK_MARKERS:
            if marker in r.text:
                problems.append(f"响应体泄漏堆栈（含 {marker}）")

        # 断言 4：每个响应都该带 X-Request-Id 响应头
        if "X-Request-Id" not in r.headers:
            problems.append("响应头缺 X-Request-Id")

        ok = not problems
        tag = "✅" if ok else "❌"
        detail = "" if ok else " | " + "; ".join(problems)
        print(f"{tag} {name}: {r.status_code}{detail}")
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\n{'=' * 46}")
    print(f"自动化用例：{passed} 通过 / {failed} 失败（共 {len(CASES)} 条）")
    print("手工用例 8/9/10（后端未启动 / 超时 / SSE 断流）见验收卡 4-1、4-3、4-4")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run() else 1)