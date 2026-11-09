import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from tools.knowledge import search_knowledge
from tools.data_analysis import sensor_stats

load_dotenv()  # 读 .env 里的 DEEPSEEK_API_KEY

# ============ 系统提示词：路由规则的"最后一公里" ============
# 工具描述写在 docstring，全局行为约束写在这里，两者配合
SYSTEM_PROMPT = """你是水泵房 IoT 运维智能助手。严格遵守：

1. 涉及设备参数、告警阈值、巡检流程、故障码、处置步骤的问题，
   必须先调用 search_knowledge 检索资料，且回答只能基于检索到的内容，
   逐句用 [编号] 标注来源；检索返回"未找到"时如实说不知道，禁止编造。
2. 涉及传感器数据统计（均值/最值/异常情况）的问题，调用 sensor_stats。
3. 闲聊、常识、与运维无关的问题，直接简洁回答，不要调用任何工具。
4. 拿不准该用哪个工具时，优先保证"不编造"这一底线。"""

# ============ LLM：挂两件工具 ============
llm = ChatOpenAI(
    model="deepseek-chat",
    temperature=0.2,                      # 低温度，回答稳定可复现
    base_url="https://api.deepseek.com",
    api_key=os.environ["DEEPSEEK_API_KEY"],
)
tools = [search_knowledge, sensor_stats]
llm_with_tools = llm.bind_tools(tools)     # 把工具清单"登记"给 LLM


# ============ 节点 1：agent（调 LLM，自主决定调不调工具） ============
def agent_node(state: MessagesState):
    # 每轮把系统提示词插在最前面，再带上完整历史消息
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    response = llm_with_tools.invoke(msgs)
    # response 要么含 tool_calls（想调工具），要么是最终回答
    return {"messages": [response]}


# ============ 节点 2：tools（执行工具调用，结果写回消息列表） ============
tool_node = ToolNode(tools)

# ============ 组装图 ============
builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
# 条件边：LLM 输出有 tool_calls → 去 tools；没有 → END
builder.add_conditional_edges("agent", tools_condition)
# 工具执行完必须回到 agent：LLM 要基于结果组织语言，可能还会再调一次
builder.add_edge("tools", "agent")

# MemorySaver：thread_id 会话隔离的记忆（W1 验收已用过，保持不变）
graph = builder.compile(checkpointer=MemorySaver())
