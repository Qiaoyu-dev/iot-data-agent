"""多轮对话验收：①追问设备详情 ②指代消解 ③会话隔离
运行（项目根目录）：python agent/memory_test.py
"""
from agent.graph import graph


def chat(thread_id: str, q: str):
    """发一句消息，返回 (最终回答, 调用过的工具名列表, 工具参数列表)。"""
    cfg = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"messages": [("user", q)]}, cfg)
    calls = [tc for m in result["messages"]
             for tc in getattr(m, "tool_calls", [])]
    return (result["messages"][-1].content,
            [c["name"] for c in calls],
            [c["args"] for c in calls])


# ===== 测试1+2：同一会话先问统计，再用"它"追问 =====
print("【测试1】多轮追问设备详情")
a1, c1, p1 = chat("t1", "TEMP-001 这周平均温度多少？")
print("  Q1 回答:", a1[:80], "\n  调用:", c1, p1)

print("\n【测试2】指代消解：追问'它'的异常点")
a2, c2, p2 = chat("t1", "那它的异常点有多少个？")
print("  Q2 回答:", a2[:80], "\n  调用:", c2, p2)
# 核心断言：工具参数必须是具体设备号，绝不能是"它"
ok2 = any(a.get("device_id") == "TEMP-001" for a in p2)
print("  ✅ 指代消解正确（参数=TEMP-001）" if ok2
      else "  ❌ 指代消解失败，检查 SYSTEM_PROMPT 第 5 条")

# ===== 测试3：跨工具追问（统计 → 知识），承接同一上下文 =====
print("\n【测试3】承接上文追问处置流程")
a3, c3, p3 = chat("t1", "温度超标了该怎么处理？")
print("  Q3 回答:", a3[:80], "\n  调用:", c3)
ok3 = "search_knowledge" in c3
print("  ✅ 正确路由到知识库" if ok3 else "  ❌ 应调 search_knowledge")

# ===== 测试4：新会话隔离，"它"无处可指 =====
print("\n【测试4】新 thread 会话隔离")
a4, c4, p4 = chat("t2", "它的平均温度呢？")
print("  Q4 回答:", a4[:120])
# 期望：回答里应体现"反问/请提供设备号"，而不是编一个 TEMP-001
print("  观察：是否反问了您指哪台设备（不应直接假设 TEMP-001）")