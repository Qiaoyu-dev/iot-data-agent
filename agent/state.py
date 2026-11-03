from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
class AgentState(TypedDict): 
  messages: Annotated[list, add_messages]  # reducer 自动合并消息