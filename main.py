from langgraph.graph import MessagesState, StateGraph, START, END
from typing import Annotated, TypedDict
from langgraph.types import Send
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, AIMessage
import operator
from dataclasses import dataclass
from pydantic import BaseModel, Field
from web_search import search_the_web
from wiki_search import search_the_wikipedia

class OverallState(TypedDict):
    topic: str
    analysts: Annotated[list, operator.add]
    analysts_quantity: int 
    interview_questions: int 
    reports: Annotated[list, operator.add]
    introduction: str
    report_body: str
    conclusion: str

@dataclass
class Analyst:
    position: str
    background: str
    character: str

    @property
    def description(self) -> str:
        return (
            f"Your work position is {self.position}, "
            f"your background is {self.background}, "
            f"and your character is {self.character}"
        )

class CreateAnalyst(BaseModel):
    position: str
    background: str
    character: str

class CreateAnalysts(BaseModel):
    analysts: list[CreateAnalyst] = Field(description="List of analysts to create")

class InterviewState(MessagesState):
    topic: str
    analyst: Analyst
    context: Annotated[list, operator.add]
    interview_questions: int
    report: str

class SearchState(TypedDict):
    query: str

class Question(BaseModel):
    question: str

class SearchQuery(BaseModel):
    query: str

class Response(BaseModel):
    response: str

class Report(BaseModel):
    report: str

class Introduction(BaseModel):
    introduction: str

class ReportBody(BaseModel):
    report_body: str

class Conclusion(BaseModel):
    conclusion: str

analysts_creation_prompt = """Your task is to create {quantity} analysts that will be best suitable for this topic: {topic}. You need to think of best position,
 background and character for each of analysts that will make their analysis topic specific and will cover a lot of details."""

question_creation_prompt = """You are very expirienced analyst. {description}. 
Your task is to ask expert with knowledge very good questions about {topic} to cover this topic. Make a specific questions that can't be just answered with yes or no.
Obtain information about the topic. If you're satisfied with interview and think that you fully covered the topic answer with 'Thank you very much for the interview!'"""

search_query_creation_prompt = """Your task is to create best search query that will help to answer this question {question}. Make sure that it's not too specific and not too wide.
Results from this search will help the expert to answer this question."""

response_creation_prompt = """You're an expert in this topic/field {topic}. Your task is to answer the question from the analyst based on your context and to make very good quality response.
You have this context about your field {context}. """

report_creation_prompt = """You'll be given a chat between analyst and expert. 
Your task is to create detailed report of it, you need to focus on the expert responses mostly, not on the dialoge by itself. Your report will be used in research creation so don't mess it up.
"""

introduction_creation_prompt = """Your task is to create really good introduction for the research report based on this reports from the interviews with the experst: {reports}."""

report_body_creation_prompt = """Your task is to create really good main body for the research report based on this reports from the interviews with the experst: {reports}."""

conclusion_creation_prompt = """Your task is to create really good conclusion for the research report based on this reports from the interviews with the experst: {reports}."""

llm = init_chat_model(model="gpt-4.1-mini")

def create_analysts(state: OverallState):
    n_analysts = state.get("analysts_quantity", 3)
    prompt = analysts_creation_prompt.format(quantity=n_analysts, topic=state["topic"])
    response = llm.with_structured_output(CreateAnalysts).invoke(prompt)

    analysts = [Analyst(**analyst.model_dump()) for analyst in response.analysts]

    return {"analysts": analysts}

def move_to_inverviews(state: OverallState):
    interviews = []
    for analyst in state["analysts"]:
        interviews.append(Send("interview", {"topic": state["topic"], "analyst": analyst}))

    return interviews

def ask_question(state: InterviewState):
    prompt = question_creation_prompt.format(description=state["analyst"].description, topic=state["topic"])
    
    messages_for_llm = [
        SystemMessage(content=prompt),
        *state["messages"]
    ]
    
    response = llm.with_structured_output(Question).invoke(messages_for_llm)
    return {"messages": [AIMessage(content=response.question, name="analyst")]}

def create_search_query(state: InterviewState):
    question = state["messages"][-1].content
    prompt = search_query_creation_prompt.format(question=question)
    
    result = llm.with_structured_output(SearchQuery).invoke(prompt)
    return {"query": result.query}

def search_web(state: SearchState):
    results = search_the_web(state["query"])
    return {"context": [page.text for page in results]}

def search_wikipidea(state: SearchState):
    result = search_the_wikipedia(state["query"])
    if result:
        return {"context": [result]}
    else:
        return None

def answer_question(state: InterviewState):
    context = "\n\n".join(state["context"])
    prompt = response_creation_prompt.format(topic=state["topic"], context=context)
    result = llm.with_structured_output(Response).invoke(prompt)
    return {"messages": [AIMessage(content=result.response, name="expert")]}

def continue_or_end_interview(state: InterviewState):
    analyst_messages = [msg for msg in state["messages"]
                        if getattr(msg, "name", None) == "analyst"]
    
    n_questions = state.get("interview_questions", 2)

    if len(analyst_messages) == n_questions or "Thank you very much for the interview!" in analyst_messages[-1].content:
        return "end"
    return "continue"

def create_interview_report(state: InterviewState):
    llm_messages = [
        SystemMessage(content=report_creation_prompt),
        *state["messages"]
    ]

    result = llm.with_structured_output(Report).invoke(llm_messages)
    return {"report": result.report}

def run_interviews(state: InterviewState):
    result = interview_graph.invoke(state)

    return {"reports": [result["report"]]}

def create_report_introduction(state: OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = introduction_creation_prompt.format(reports = reports)
    result = llm.with_structured_output(Introduction).invoke(prompt)
    return {"introduction": result.introduction}

def create_report_body(state: OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = report_body_creation_prompt.format(reports = reports)
    result = llm.with_structured_output(ReportBody).invoke(prompt)
    return {"report_body": result.report_body}

def create_report_conclusion(state: OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = conclusion_creation_prompt.format(reports = reports)
    result = llm.with_structured_output(Conclusion).invoke(prompt)
    return {"conclusion": result.conclusion}

interview_builder = StateGraph(InterviewState)
interview_builder.add_node("ask_question", ask_question)
interview_builder.add_node("create_search_query", create_search_query)
interview_builder.add_node("search_web", search_web)
interview_builder.add_node("search_wikipedia", search_wikipidea)
interview_builder.add_node("answer_question", answer_question)
interview_builder.add_node("create_interview_report", create_interview_report)

interview_builder.add_edge(START, "ask_question")
interview_builder.add_edge("ask_question", "create_search_query")
interview_builder.add_edge("create_search_query", "search_wikipedia")
interview_builder.add_edge("create_search_query", "search_web")
interview_builder.add_edge("search_wikipedia", "answer_question")
interview_builder.add_edge("search_web", "answer_question")
interview_builder.add_conditional_edges("answer_question", continue_or_end_interview, {"continue": "ask_question", "end": "create_interview_report"})
interview_builder.add_edge("create_interview_report", END)

interview_graph = interview_builder.compile()

graph_builder = StateGraph(OverallState)
graph_builder.add_node("create_analysts", create_analysts)
graph_builder.add_node("interview", run_interviews)
graph_builder.add_node("create_introduction", create_report_introduction)
graph_builder.add_node("create_body", create_report_body)
graph_builder.add_node("create_conclusion", create_report_conclusion)

graph_builder.add_edge(START, "create_analysts")
graph_builder.add_conditional_edges("create_analysts", move_to_inverviews, ["interview"])
graph_builder.add_edge("interview", "create_introduction")
graph_builder.add_edge("interview", "create_body")
graph_builder.add_edge("interview", "create_conclusion")
graph_builder.add_edge("create_introduction", END)
graph_builder.add_edge("create_body", END)
graph_builder.add_edge("create_conclusion", END)

graph = graph_builder.compile()
