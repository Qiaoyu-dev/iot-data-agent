import chromadb
from rag.embed import embed

_client = chromadb.PersistentClient(path="chroma_db")
_coll = _client.get_or_create_collection("iot_docs")

def retrieve(query: str, top_k: int = 3) -> list:
    """检索最相关的运维文档块，返回带引用来源的列表"""
    if _coll.count() == 0:
        return []  # 库是空的，先跑 rag/build_index.py
    res = _coll.query(query_embeddings=embed([query]), n_results=top_k)
    hits = []
    for i in range(len(res["ids"][0])):
        hits.append({
            "text": res["documents"][0][i],
            "source": res["metadatas"][0][i]["source"],
            "distance": res["distances"][0][i],  # 越小越相关
        })
    return hits
