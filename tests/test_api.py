"""
tests/test_api.py
接口集成测试：把 scripts/smoke_test.py 的 P0-P5 六条路径改写成 pytest。
前置：先启动后端 uvicorn api.main:app --port 8000，再跑 pytest。
运行：pytest tests/test_api.py -v
"""
import os
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def test_p0_health():
    r = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200


def test_p1_chat():
    r = requests.post(f"{BASE_URL}/chat", json={"message": "你好，一句话介绍你自己"}, timeout=30)
    assert r.status_code == 200
    assert r.json()["reply"].strip()


def test_p2_memory():
    tid = "pytest-memory-001"
    requests.post(f"{BASE_URL}/chat",
                   json={"message": "我叫小罗，请记住", "thread_id": tid}, timeout=30)
    r = requests.post(f"{BASE_URL}/chat",
                       json={"message": "我叫什么名字", "thread_id": tid}, timeout=30)
    assert "罗" in r.json()["reply"]


def test_p4_rag_with_citation():
    r = requests.post(f"{BASE_URL}/chat",
                       json={"message": "PUMP-X201 的告警阈值是多少？"}, timeout=30)
    assert r.status_code == 200
    assert "[" in r.json()["reply"]   # 检索命中且带 [编号] 引用


def test_p5_refuse():
    r = requests.post(f"{BASE_URL}/chat",
                       json={"message": "今天北京天气怎么样"}, timeout=30)
    keywords = ("没有找到", "知识库", "无法回答", "未收录", "不在", "无法获取")
    assert any(k in r.json()["reply"] for k in keywords)