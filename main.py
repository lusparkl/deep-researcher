from langgraph.graph import MessagesState, StateGraph, START, END
from typing import Literal
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

@tool
def get_favorite_character_of_the_user(anime: str) -> str:
    """Get user favorite character by anime name.
    
    Args:
        anime: Name of the anime, case doesn't matter"""
    
    match anime.lower():
        case "naruto":
            return "Sakura"
        case "bleach":
            return "Urahara"
        case "cowboy bebop":
            return "Spike"
        case _:
            return "Can't find this anime in db."

@tool(description="Get list of users favorite food.")
def get_favorite_food() -> list[str]:
    return ["Pizza", "Spagetti", "Rice", "Ice Cream"]

@tool(description="Get user name")
def get_name() -> str:
    return "Sasha"

config = {"configurable": {"thread_id": 1}}
memory = InMemorySaver()

llm = init_chat_model("gpt-4.1-mini")

llm_with_tools = llm.bind_tools([get_favorite_character_of_the_user, get_favorite_food, get_name])

def tool_calling_llm(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


graph_builder = StateGraph(MessagesState)
graph_builder.add_node("tool_calling_llm", tool_calling_llm)
graph_builder.add_node("tools", ToolNode([get_favorite_character_of_the_user, get_favorite_food, get_name]))
graph_builder.add_edge(START, "tool_calling_llm")
graph_builder.add_conditional_edges("tool_calling_llm", tools_condition)
graph_builder.add_edge("tools", "tool_calling_llm")
graph = graph_builder.compile(checkpointer=memory)

response = graph.invoke({"messages": HumanMessage(content="Hello, tell me my favorite Bleach character and tell if he like's the same food as I or not.")}, config)

response_2 = graph.invoke({"messages": [HumanMessage(content="I think Urahara like Japanese food.")]}, config)

for m in response_2["messages"]:
    m.pretty_print()
