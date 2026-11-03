from langchain_core.tools import tool
from rag.retrieve import retrieve

@tool
def search_knowledge(query: str) -> str:
    """检索运维知识库，查询设备故障处理方法、报警规则、手册条款"""
    hits = retrieve(query)
    if not hits:
        return "知识库暂无相关内容"
    return "\n".join(f"[{i+1}]({h['source']}) {h['text']}" for i, h in enumerate(hits))
