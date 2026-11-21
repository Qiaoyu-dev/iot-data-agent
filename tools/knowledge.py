import logging

from langchain_core.tools import tool

from rag.retrieve import retrieve

from rag.rerank import rerank
from tools.domain import _has_exact_hit, _in_domain

THRESHOLD = 1.12

logger = logging.getLogger(__name__)

# 粗召回候选数：先多拿，交给 rerank 精排
RECALL_K = 20

def retrieve_contexts(query: str, top_k: int = 8, max_keep: int = 3) -> list[dict]:
    """检索 + 阈值过滤 + Rerank 精排 + 截断，返回最终送入模型的 chunk 列表。
    这是「取上下文」的唯一生产逻辑：search_knowledge 和评测脚本都走它，改一处全局生效。
    """
    hits = retrieve(query, top_k=RECALL_K)          # ① 粗召回：向量多拿候选
    kept = [h for h in hits
            if h["distance"] < THRESHOLD or _has_exact_hit(query, h["text"])]  # ② 阈值兜底（保留拒答）
    if len(kept) > 1:                                 # ③ Rerank 精排：语义重排
        try:
            ranked = rerank(query, [h["text"] for h in kept])
        except Exception as exc:                       # 模型未安装/下载失败时退回距离排序
            logger.warning("rerank 不可用，按向量距离排序：%s", exc)
            ranked = None
        if ranked:
            for idx, score in ranked:
                kept[idx]["score"] = score
    # ④ 精确命中（编码 token）仍排最前，其余按 rerank 分降序
    kept.sort(key=lambda h: (0 if _has_exact_hit(query, h["text"]) else 1,
                             -h.get("score", 0.0)))
    return kept[:max_keep]


@tool
def search_knowledge(query: str) -> str:
    """检索水泵房运维知识库（设备手册 + 巡检报告）。"""
    if not _in_domain(query):
        return ("该问题不属于水泵房设备运维范畴，知识库中没有相关资料。"
                "请如实告知用户你只能回答设备运维相关问题，不要编造。")

    kept = retrieve_contexts(query)
    if not kept:
        return ("知识库中未找到与该问题相关的资料（检索结果全部低于相关阈值）。"
                "请如实告知用户无法从现有资料中回答，不要编造内容。")

    lines = []
    for i, h in enumerate(kept, 1):
        src = f"{h['kb']}/{h['source']}"
        lines.append(f"[{i}]（来源：{src}，距离 {h['distance']:.3f}）\n{h['text']}")
    return "\n\n".join(lines)
