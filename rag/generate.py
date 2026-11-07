"""
rag/generate.py
作用：检索生成端到端——retrieve 拿证据块，阈值过滤后拼进 prompt，
     DeepSeek 生成带来源引用的分析报告
运行：在仓库根目录执行  python -m rag.generate
依赖：langchain-openai；.env 配好 DEEPSEEK_API_KEY
"""
from langchain_openai import ChatOpenAI

from config.settings import DEEPSEEK_API_KEY   # 与 agent/graph.py 同样的读法
from rag.retrieve import retrieve

# 与任务一校准出的阈值保持一致
DISTANCE_THRESHOLD = 1.2

# DeepSeek 客户端（和 agent/graph.py 同款初始化方式）
llm = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY,
    temperature=0.2,        # 分析型任务要低随机性，减少自由发挥
)

SYSTEM = """你是工业运维分析助手。仅基于【资料】回答用户问题，规则：
1. 每个关键结论后面用 [编号] 标注引用来源，例如"告警阈值为 85°C[1]"
2. 资料没有覆盖的内容，明确写"现有资料未覆盖"，禁止编造
3. 输出结构：结论 → 依据 → 处置建议
"""


def answer(query: str, top_k: int = 3) -> str:
    """检索 + 过滤 + 生成，返回带引用的分析报告"""
    hits = retrieve(query, top_k=top_k)

    # ===== 闸门一：距离阈值过滤，宁可拒答不硬答 =====
    hits = [h for h in hits if h["distance"] < DISTANCE_THRESHOLD]
    if not hits:
        return ("【资料库未覆盖】没有找到与问题足够相关的文档，"
                "请补充运维文档或换一种问法。")

    # ===== 证据编号拼进 prompt，来源信息一并给（方便核对）=====
    context = "\n\n".join(
        f"[{i}]（来源：{h['kb']}/{h['source']}）\n{h['text']}"
        for i, h in enumerate(hits, 1)
    )
    messages = [
        ("system", SYSTEM),
        ("user", f"【资料】\n{context}\n\n【问题】{query}"),
    ]
    resp = llm.invoke(messages)

    # 答案后面附上来源清单，形成完整证据链
    refs = "\n".join(
        f"  [{i}] {h['kb']}/{h['source']}（距离 {h['distance']:.3f}）"
        for i, h in enumerate(hits, 1)
    )
    return f"{resp.content}\n\n—— 引用来源 ——\n{refs}"


if __name__ == "__main__":
    for q in ["TEMP-001 温度报警了，分析一下该怎么办",
              "食堂几点开饭"]:          # 顺便验证拒答机制
        print(f"\n{'='*20} {q} {'='*20}")
        print(answer(q))