from langgraph.types import Send
import app.research.models as models
import app.research.promts as prompts
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, AIMessage
from app.research.search_tools.web_search import search_the_web
from app.research.search_tools.wiki_search import search_the_wikipedia
from dotenv import load_dotenv
from os import getenv

HACK_AI_API_KEY = getenv("HACK_AI_API_KEY")

llm = ChatOpenAI(
    model="google/gemini-3.1-flash-lite",
    api_key=HACK_AI_API_KEY,
    base_url="https://ai.hackclub.com/proxy/v1"
)

def create_analysts(state: models.OverallState):
    n_analysts = state.get("analysts_quantity", 3)
    prompt = prompts.analysts_creation.format(quantity=n_analysts, topic=state["topic"])
    response = llm.with_structured_output(models.CreateAnalysts).invoke(prompt)

    analysts = [models.Analyst(**analyst.model_dump()) for analyst in response.analysts]

    return {"analysts": analysts}

def move_to_inverviews(state: models.OverallState):
    interviews = []
    for analyst in state["analysts"]:
        interviews.append(Send("interview", {"topic": state["topic"], "analyst": analyst}))

    return interviews

def ask_question(state: models.InterviewState):
    prompt = prompts.question_creation.format(description=state["analyst"].description, topic=state["topic"])
    
    messages_for_llm = [
        SystemMessage(content=prompt),
        *state["messages"]
    ]
    
    response = llm.with_structured_output(models.Question).invoke(messages_for_llm)
    return {"messages": [AIMessage(content=response.question, name="analyst")]}

def create_search_query(state: models.InterviewState):
    question = state["messages"][-1].content
    prompt = prompts.search_query_creation.format(question=question)
    
    result = llm.with_structured_output(models.SearchQuery).invoke(prompt)
    return {"query": result.query}

def search_web(state: models.SearchState):
    results = search_the_web(state["query"])
    return {"context": [page.text for page in results]}

def search_wikipidea(state: models.SearchState):
    result = search_the_wikipedia(state["query"])
    if result:
        return {"context": [result]}
    else:
        return None

def answer_question(state: models.InterviewState):
    context = "\n\n".join(state["context"])
    prompt = prompts.response_creation.format(topic=state["topic"], context=context)
    result = llm.with_structured_output(models.Response).invoke(prompt)
    return {"messages": [AIMessage(content=result.response, name="expert")]}

def continue_or_end_interview(state: models.InterviewState):
    analyst_messages = [msg for msg in state["messages"]
                        if getattr(msg, "name", None) == "analyst"]
    
    n_questions = state.get("interview_questions", 2)

    if len(analyst_messages) == n_questions or "Thank you very much for the interview!" in analyst_messages[-1].content:
        return "end"
    return "continue"

def create_interview_report(state: models.InterviewState):
    llm_messages = [
        SystemMessage(content=prompts.report_creation),
        *state["messages"]
    ]

    result = llm.with_structured_output(models.Report).invoke(llm_messages)
    return {"report": result.report}

def create_report_introduction(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.introduction_creation.format(reports = reports)
    result = llm.with_structured_output(models.Introduction).invoke(prompt)
    return {"introduction": result.introduction}

def create_report_body(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.report_body_creation.format(reports = reports)
    result = llm.with_structured_output(models.ReportBody).invoke(prompt)
    return {"report_body": result.report_body}

def create_report_conclusion(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.conclusion_creation.format(reports = reports)
    result = llm.with_structured_output(models.Conclusion).invoke(prompt)
    return {"conclusion": result.conclusion}