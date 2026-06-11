from langgraph.types import Send
import app.research.models as models
import app.research.promts as prompts
from langchain.messages import SystemMessage, AIMessage, HumanMessage
from app.research.search_tools.web_search import search_the_web
from app.research.search_tools.wiki_search import search_the_wikipedia
from app.research.llm import get_structured_output
import app.config as config


def create_analysts(state: models.OverallState):
    n_analysts = state.get("analysts_quantity", config.n_analysts)
    prompt = prompts.analysts_creation.format(quantity=n_analysts, topic=state["topic"])
    response, rate_lim = get_structured_output(prompt, models.CreateAnalysts, False)

    analysts = [models.Analyst(**analyst.model_dump()) for analyst in response.analysts]

    return {"analysts": analysts, "rate_limit_exceeded": rate_lim}

def move_to_inverviews(state: models.OverallState):
    interviews = []
    for analyst in state["analysts"]:
        interviews.append(Send("interview", {"topic": state["topic"], "analyst": analyst, "rate_limit_exceeded": state["rate_limit_exceeded"]}))

    return interviews

def ask_question(state: models.InterviewState):
    prompt = prompts.question_creation.format(description=state["analyst"].description, topic=state["topic"])
    
    messages_for_llm = [
        SystemMessage(content=prompt),
        *state["messages"]
    ]
    
    response, rate_lim = get_structured_output(messages_for_llm, models.Question, state["rate_limit_exceeded"])
    return {"messages": [AIMessage(content=response.question, name="analyst")], "rate_limit_exceeded": rate_lim}

def create_search_query(state: models.InterviewState):
    question = state["messages"][-1].content
    prompt = prompts.search_query_creation.format(question=question)
    
    response, rate_lim = get_structured_output(prompt, models.SearchQuery, state["rate_limit_exceeded"])
    return {"query": response.query, "rate_limit_exceeded": rate_lim}

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

    result, rate_lim = get_structured_output(prompt, models.Response, state["rate_limit_exceeded"])
    return {"messages": [AIMessage(content=result.response, name="expert")], "rate_limit_exceeded": rate_lim}

def continue_or_end_interview(state: models.InterviewState):
    analyst_messages = [msg for msg in state["messages"]
                        if getattr(msg, "name", None) == "analyst"]
    
    n_questions = state.get("interview_questions", config.n_questions_from_each_analyst)

    if len(analyst_messages) == n_questions or "Thank you very much for the interview!" in analyst_messages[-1].content:
        return "end"
    return "continue"

def create_interview_report(state: models.InterviewState):
    llm_messages = [
        SystemMessage(content=prompts.report_creation),
        *state["messages"]
    ]

    response, rate_lim = get_structured_output(llm_messages, models.Report, state["rate_limit_exceeded"])
    return {"report": response.report, "rate_limit_exceeded": rate_lim}

def create_report_introduction(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.introduction_creation.format(reports = reports)
    response, rate_lim = get_structured_output(prompt, models.Introduction, state["rate_limit_exceeded"])
    return {"introduction": response.introduction, "rate_limit_exceeded": rate_lim}

def create_report_body(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.report_body_creation.format(reports = reports)
    response, rate_lim = get_structured_output(prompt, models.ReportBody, state["rate_limit_exceeded"])
    return {"report_body": response.report_body, "rate_limit_exceeded": rate_lim}

def create_report_conclusion(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    prompt = prompts.conclusion_creation.format(reports = reports)
    response, rate_lim = get_structured_output(prompt, models.Conclusion, state["rate_limit_exceeded"])
    return {"conclusion": response.conclusion, "rate_limit_exceeded": rate_lim}

def should_clarify_topic(state: models.TopicAssignmentState):
    prompt = prompts.topic_assignment
    llm_messages = [
        SystemMessage(content=prompt),
        *state["messages"]
    ]
    response, rate_lim = get_structured_output(llm_messages, models.TopicAsignment, False)

    return {"next_node": response.research_or_assign, "topic": response.clear_topic, "rate_limit_exceeded": rate_lim}

def route_after_topic_assignment(state: models.TopicAssignmentState):
    return state["next_node"]

def clarify_research_topic(state: models.TopicAssignmentState):
    prompt = prompts.topic_clarification
    llm_messages = [
        SystemMessage(prompt),
        *state["messages"]
    ]
    response, rate_lim = get_structured_output(llm_messages, models.Clarification, state["rate_limit_exceeded"])
    return {"messages": [AIMessage(content=response.clarification)], "rate_limit_exceeded": rate_lim, "clarification": response.clarification}


