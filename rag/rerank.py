"""
rag/rerank.py
作用：BGE Reranker 精排封装 —— 把「向量粗召回」的候选按 query 相关性重新打分排序。
原理：向量召回是「双塔」（query、doc 各算向量再比），快但粗；
      rerank 用「交叉编码器」把 query 和 doc 拼成一句话过完整模型，慢但准。
      所以召回多拿候选（top_k=20），rerank 重排后取最准的前几个。
运行自测：python -m rag.rerank
"""
from FlagEmbedding import FlagReranker

# 首次调用 rerank() 时才加载模型（约 1.1GB，从 HuggingFace 下载后走本地缓存）
# 中文手册场景用 bge-reranker-v2-m3（多语言，中文效果好）
# use_fp16=False：没有独显时用 CPU 跑，慢一点但稳；有 CUDA 可改 True 提速
_reranker = None


def _get_reranker():
    """懒加载：import 本模块时不联网、不加载模型，第一次 rerank() 才初始化。"""
    global _reranker
    if _reranker is None:
        _reranker = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False)
    return _reranker


def rerank(query: str, docs: list[str]) -> list[tuple[int, float]]:
    """对候选文档重排，返回 [(原始下标, 相关性得分), ...]，得分从高到低。"""
    if not docs:
        return []
    pairs = [[query, d] for d in docs]
    scores = _get_reranker().compute_score(pairs, normalize=True)  # normalize=True → 0~1
    if isinstance(scores, float):   # 单个 doc 时 compute_score 可能返回标量
        scores = [scores]
    # 按得分降序，但保留原始下标，方便调用方回填到原 hit 上
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return ranked


if __name__ == "__main__":
    q = "水泵机组保养周期是多久"
    docs = [
        "设备应每运行 2000 小时更换润滑油。",
        "温度超过 85 摄氏度触发告警。",
    ]
    for i, s in rerank(q, docs):
        print(f"[{i}] {s:.3f}  {docs[i]}")