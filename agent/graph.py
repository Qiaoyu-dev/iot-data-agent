from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from tools.sensor import get_sensor_temperature, get_sensor_stats
from tools.knowledge import search_knowledge
from config.settings import DEEPSEEK_API_KEY

llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

tools = [get_sensor_temperature, get_sensor_stats, search_knowledge]
llm_with_tools = llm.bind_tools(tools)

SYSTEM = SystemMessage(content=(
    "你是 IoT 设备运维分析助手。回答时："
    "①需要实时/统计数据就调传感器工具；②需要故障处理方法就检索知识库；"
    "③结论必须标注来源（[1] 引用编号或数据时间）"
))

def llm_node(state: AgentState):
    messages = [SYSTEM] + state["messages"]
    return {"messages": [llm_with_tools.invoke(messages)]}

def router(state: AgentState):
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

builder = StateGraph(AgentState)
builder.add_node("llm", llm_node)
builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
builder.set_entry_point("llm")
builder.add_conditional_edges("llm", router, {"tools": "tools", END: END})
builder.add_edge("tools", "llm")

graph = builder.compile(checkpointer=MemorySaver())
