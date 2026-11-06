"""
rag/search_test.py
作用：用 4 组梯度 query 批量测试检索效果，
     观察距离分数分布，校准"相关性阈值"
运行：在仓库根目录执行  python rag/search_test.py
"""
from rag.retrieve import retrieve

# 梯度测试集：从"文档明确覆盖"到"完全无关"
QUERIES = [
    "温度超过告警阈值怎么办",      # ① 手册有完整处置流程 → 应强命中
    "E02 故障码怎么处理",           # ② 故障码表里有 → 应命中
    "传感器读数不准了",             # ③ 边缘相关（漂移/校准）→ 观察分数
    "食堂中午几点开饭",             # ④ 完全无关 → 距离应明显偏大
]

# L2 距离阈值：起始经验值，跑完后根据你的实际分数分布调整
THRESHOLD = 1.2

for q in QUERIES:
    hits = retrieve(q, top_k=3)
    print(f"\n=== {q} ===")
    for i, h in enumerate(hits, 1):
        # 距离小于阈值判相关，大于阈值标记弃用
        flag = "✅ 采纳" if h["distance"] < THRESHOLD else "❌ 弃用"
        preview = h["text"].replace("\n", " ")[:40]
        print(f"  [{i}] 距离 {h['distance']:.3f} {flag}")
        print(f"      ({h['kb']}/{h['source']}) {preview}...")