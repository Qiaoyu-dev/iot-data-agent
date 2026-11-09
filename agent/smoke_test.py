"""冒烟测试：验证 Agent 工具路由是否符合预期。
运行：python -m agent.smoke_test
"""
from agent.graph import graph

# 三组验收用例：(问题, 期望行为)
CASES = [
    ("水泵房的温度告警阈值是多少？", "search_knowledge"),  # 知识类 → 应调检索
    ("TEMP-001 这周平均温度多少？有超标吗？", "sensor_stats"),  # 数据类 → 应调统计
    ("你好，简单介绍下你自己", None),                        # 闲聊类 → 不应调工具
]

for i, (q, expect) in enumerate(CASES, 1):
    # 每个用例独立的 thread_id：避免 MemorySaver 让三个用例共享历史、互相污染
    cfg = {"configurable": {"thread_id": f"smoke-{i}"}}
    result = graph.invoke({"messages": [("user", q)]}, cfg)

    # 扫描整段消息历史，收集实际调用过的工具名
    called = [
        tc["name"]
        for m in result["messages"]
        if getattr(m, "tool_calls", None)
        for tc in m.tool_calls
    ]
    ok = (called == [] and expect is None) or (expect in called)

    print(f"{'✅' if ok else '❌'} Q: {q}")
    print(f"   期望调用: {expect} ｜ 实际调用: {called or ['无']}")
    print(f"   最终回答: {result['messages'][-1].content[:120]}...\n")