from langchain_core.tools import tool
from rag.retrieve import retrieve   # 复用 W1 写好的跨库检索，一行不改

# 与 W1 相同的距离阈值：L2 距离 < 1.2 才认为检索结果相关
# 这是防幻觉第一道闸门，改造后依然生效
THRESHOLD = 1.2


@tool
def search_knowledge(query: str) -> str:
    """检索水泵房运维知识库（设备手册 + 巡检报告）。

    适用场景：用户询问设备参数、告警阈值、巡检流程、故障码、
    处置步骤等【运维知识】时调用本工具。
    不适用：传感器实时数据统计（用 sensor_stats）、闲聊（直接回答）。

    Args:
        query: 用户的具体问题或检索关键词，尽量保留原话中的设备号/参数名。

    Returns:
        带 [编号] 和来源标注的资料片段；若无相关资料则返回明确的"未找到"说明。
    """
    # ① 跨库检索（iot_manuals + iot_reports 两库合并，按距离升序）
    hits = retrieve(query)

    # ② 阈值过滤：宁可拒答，不硬答（防幻觉第一闸门）
    # retrieve() 返回 dict 列表：{"text","source","kb","distance"}，用键访问而不是解包
    kept = [h for h in hits if h["distance"] < THRESHOLD]

    # ③ 没找到 → 明确告诉 LLM"没有资料"，它会如实拒答
    if not kept:
        return ("知识库中未找到与该问题相关的资料（检索结果全部低于相关阈值）。"
                "请如实告知用户无法从现有资料中回答，不要编造内容。")

    # ④ 格式化成带 [编号] 的文本，LLM 生成回答时逐句引用编号
    lines = []
    for i, h in enumerate(kept, 1):
        src = f"{h['kb']}/{h['source']}"
        lines.append(f"[{i}]（来源：{src}，距离 {h['distance']:.3f}）\n{h['text']}")
    return "\n\n".join(lines)