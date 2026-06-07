from langgraph.graph import MessagesState, StateGraph, START, END
from typing import Annotated, TypedDict
from langgraph.types import Send
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import operator
from pydantic import BaseModel

load_dotenv()

subjects_prompt = """Your task is to generate some examples of this topic {topic}"""
jokes_prompt = """Create a really funny joke about this situation {subject}"""
get_best_prompt = """Analyze this jokes and pick the best one, return it's id: {jokes}"""

class OverallState(TypedDict):
    topic: str
    subjects: list
    jokes: Annotated[list, operator.add]
    best_joke: str

class Subjects(BaseModel):
    subjects: list[str]

class JokeState(TypedDict):
    subject: str

class Joke(BaseModel):
    joke: str

class BestJoke(BaseModel):
    joke_id: int

llm = init_chat_model(model="gpt-4.1-mini")

def generate_subjects(state: OverallState):
    response = llm.with_structured_output(Subjects).invoke(subjects_prompt.format(topic=state["topic"]))
    return {"subjects": response.subjects}

def move_from_subjects_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

def generate_joke(state: JokeState):
    response = llm.with_structured_output(Joke).invoke(jokes_prompt.format(subject=state["subject"]))
    return {"jokes": [response.joke]}

def get_best_joke(state: OverallState):
    jokes = "\n\n".join(state["jokes"])
    response = llm.with_structured_output(BestJoke).invoke(get_best_prompt.format(jokes=jokes))
    return {"best_joke": state["jokes"][response.joke_id]}

graph_builder = StateGraph(OverallState)
graph_builder.add_node("generate_subjects", generate_subjects)
graph_builder.add_node("generate_joke", generate_joke)
graph_builder.add_node("get_best_joke", get_best_joke)

graph_builder.add_edge(START, "generate_subjects")
graph_builder.add_conditional_edges("generate_subjects", move_from_subjects_to_jokes, ["generate_joke"])
graph_builder.add_edge("generate_joke", "get_best_joke")
graph_builder.add_edge("get_best_joke", END)

graph = graph_builder.compile()
result = graph.invoke(OverallState(topic="Football"))
print(result["best_joke"])