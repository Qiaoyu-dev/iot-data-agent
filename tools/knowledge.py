import re

from langchain_core.tools import tool

from rag.retrieve import retrieve

THRESHOLD = 1.12

DOMAIN_TERMS = (
    "泵", "温度", "传感器", "告警", "故障", "巡检", "冷却液", "轴承",
    "滤芯", "滤网", "压差", "校准", "保养", "润滑", "密封", "绝缘",
    "网关", "上报", "备件", "库存", "领用", "平台", "报表", "阈值",
    "TEMP-", "PUMP-", "E0", "LOTO", "UPS",
)

# 编码型 token：E03 / TEMP-001 / PUMP-X201 这类"字母+数字"标识符
_TOKEN_RE = re.compile(r"[A-Z]{1,5}[-_]?\d{2,4}")


def _in_domain(query: str) -> bool:
    q = query.upper()
    return any(t.upper() in q for t in DOMAIN_TERMS)


def _has_exact_hit(query: str, text: str) -> bool:
    """query 里的编码 token 出现在 text 里 → 精确命中，绕过距离阈值"""
    tokens = _TOKEN_RE.findall(query.upper())
    if not tokens:
        return False
    up = text.upper()
    return any(t in up for t in tokens)


def retrieve_contexts(query: str, top_k: int = 8, max_keep: int = 3) -> list[dict]:
    """检索 + 阈值/编码精确命中过滤 + 排序 + 截断，返回最终送入模型的 chunk 列表。

    这是「取上下文」的唯一生产逻辑：search_knowledge 和评测脚本都走它，避免两处漂移。
    """
    hits = retrieve(query, top_k=top_k)
    kept = [h for h in hits
            if h["distance"] < THRESHOLD or _has_exact_hit(query, h["text"])]
    # 精确命中的排最前，保证模型优先看到正确的那块
    kept.sort(key=lambda h: (0 if _has_exact_hit(query, h["text"]) else 1,
                             h["distance"]))
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