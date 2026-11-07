"""
rag/retrieve.py  (v2 · 多知识库版)
作用：给定 query，在 Chroma 中检索最相关的 top_k 个 chunk
升级：支持跨库合并检索（默认全部知识库），或指定单个库
运行自测：python -m rag.retrieve
"""
import sys

import chromadb

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，强制 UTF-8 避免中文/emoji 报错

from rag.embed import embed

client = chromadb.PersistentClient(path="chroma_db")


def _all_collection_names() -> list[str]:
    """兼容不同 chromadb 版本的 collection 列表写法"""
    raw = client.list_collections()
    return [c if isinstance(c, str) else c.name for c in raw]


def retrieve(query: str, top_k: int = 3, kb: str = None) -> list[dict]:
    """
    kb=None        → 在全部知识库里合并检索，按距离统一排序
    kb="iot_manuals" → 只检索指定知识库
    返回 [{"text": ..., "source": ..., "kb": ..., "distance": ...}]
    """
    names = [kb] if kb else _all_collection_names()
    q_emb = embed([query])                    # query 也要走向量
    hits = []
    for name in names:
        coll = client.get_collection(name)
        if coll.count() == 0:                 # 防空库检索报错
            continue
        res = coll.query(
            query_embeddings=q_emb,
            n_results=min(top_k, coll.count()),
            include=["documents", "metadatas", "distances"],
        )
        for doc, meta, dist in zip(
                res["documents"][0], res["metadatas"][0],
                res["distances"][0]):
            hits.append({
                "text": doc,
                "source": meta.get("source", "?"),
                "kb": meta.get("kb", name),
                "distance": dist,
            })
    # 跨库合并：距离越小越相关，统一排序后取前 top_k
    hits.sort(key=lambda h: h["distance"])
    return hits[:top_k]


if __name__ == "__main__":
    q = "温度超过告警阈值怎么办"
    for i, h in enumerate(retrieve(q), 1):
        print(f"[{i}] (来自 {h['kb']}/{h['source']}, 距离 {h['distance']:.3f})")
        print(f"    {h['text'][:100]}...\n")