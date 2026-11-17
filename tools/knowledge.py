import re

from langchain_core.tools import tool

from rag.retrieve import retrieve

THRESHOLD = 1.12

# 域外黑名单：明显不属于水泵房设备运维的话题才拒答。
# 其余（含"停电恢复 / 历史数据 / 三点复测"这类不含专业词的合法问题）一律放行，
# 交给检索距离阈值兜底——避免白名单误杀合法问题（此前 Q17/Q22/Q24 因此被误拒答）。
OUT_OF_DOMAIN_TERMS = (
    # 餐饮 / 生活
    "食堂", "开饭", "午饭", "晚饭", "早饭", "点餐", "吃饭",
    # 人事 / 行政
    "年假", "请假", "放假", "考勤", "工资", "薪资", "招聘", "社保", "公积金",
    # 公司事务 / 闲聊
    "年终总结", "团建", "年会", "福利",
    "天气", "股票", "游戏", "电影", "音乐", "新闻", "明星",
    # 通用无关请求
    "写诗", "翻译", "画画", "写代码",
)

# 编码型 token：E03 / TEMP-001 / PUMP-X201 这类"字母+数字"标识符
_TOKEN_RE = re.compile(r"[A-Z]{1,5}[-_]?\d{2,4}")


def _in_domain(query: str) -> bool:
    """黑名单排除：命中域外话题返回 False 拒答，否则放行给阈值判定。"""
    q = query.upper()
    return not any(t.upper() in q for t in OUT_OF_DOMAIN_TERMS)


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