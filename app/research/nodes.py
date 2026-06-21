from langgraph.types import Send
import app.research.models as models
import app.research.promts as prompts
from langchain.messages import SystemMessage, AIMessage
from app.research.search_tools.web_search import search_the_web
from app.research.search_tools.wiki_search import search_the_wikipedia
from app.research.llm import get_structured_output
import app.config as config
from uuid import uuid4


def _new_source_id() -> str:
    return f"S{uuid4().hex[:8]}"

def _format_context_document(source_id: str, url: str, text: str) -> str:
    return f"Source ID: [{source_id}]\nURL: {url}\nContent:\n{text}"

def create_analysts(state: models.OverallState):
    n_analysts = state.get("analysts_quantity", config.n_analysts)
    prompt = prompts.analysts_creation.format(quantity=n_analysts, topic=state["topic"])
    response, rate_lim = get_structured_output(prompt, models.CreateAnalysts, False, True)

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
    context = []
    sources = []
    for page in results:
        url = (page.url or "").strip()
        text = (page.text or "").strip()
        if not url or not text:
            continue

        source_id = _new_source_id()
        context.append(_format_context_document(source_id, url, text))
        sources.append(models.Source(link=url, id=source_id))
    
    return {"context": context, "sources": sources}

def search_wikipidea(state: models.SearchState):
    result = search_the_wikipedia(state["query"])
    if not result:
        return {"context": [], "sources": []}

    text, url = result
    if text:
        source_id = _new_source_id()
        context = _format_context_document(source_id, url, text.strip())
        source = models.Source(link=url, id=source_id)
        return {"context": [context], "sources": [source]}
    else:
        return {"context": [], "sources": []}

def answer_question(state: models.InterviewState):
    context = "\n\n".join(state.get("context", []))
    question = next(
        (msg.content for msg in reversed(state["messages"]) if getattr(msg, "name", None) == "analyst"),
        "",
    )
    prompt = prompts.response_creation.format(topic=state["topic"], question=question, context=context)

    result, rate_lim = get_structured_output(prompt, models.Response, state["rate_limit_exceeded"], True)
    return {"messages": [AIMessage(content=result.response, name="expert")], "rate_limit_exceeded": rate_lim}

def continue_or_end_interview(state: models.InterviewState):
    analyst_messages = [msg for msg in state["messages"]
                        if getattr(msg, "name", None) == "analyst"]
    
    n_questions = state.get("interview_questions", config.n_questions_from_each_analyst)

    if len(analyst_messages) == n_questions or "Thank you very much for the interview!" in analyst_messages[-1].content:
        return "end"
    return "continue"

def create_interview_report(state: models.InterviewState):
    sources = models.format_source_registry(state.get("sources", []))
    llm_messages = [
        SystemMessage(content=prompts.report_creation.format(sources=sources)),
        *state["messages"]
    ]

    response, rate_lim = get_structured_output(llm_messages, models.Report, state["rate_limit_exceeded"], True)
    return {"report": response.report, "rate_limit_exceeded": rate_lim}

def create_report_introduction(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    sources = models.format_source_registry(state.get("sources", []))
    prompt = prompts.introduction_creation.format(reports=reports, sources=sources)
    response, rate_lim = get_structured_output(prompt, models.Introduction, state["rate_limit_exceeded"], True)
    return {"introduction": response.introduction, "rate_limit_exceeded": rate_lim}

def create_report_body(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    sources = models.format_source_registry(state.get("sources", []))
    prompt = prompts.report_body_creation.format(reports=reports, sources=sources)
    response, rate_lim = get_structured_output(prompt, models.ReportBody, state["rate_limit_exceeded"], True)
    return {"report_body": response.report_body, "rate_limit_exceeded": rate_lim}

def create_report_conclusion(state: models.OverallState):
    reports = "\n\n".join(state["reports"])
    sources = models.format_source_registry(state.get("sources", []))
    prompt = prompts.conclusion_creation.format(reports=reports, sources=sources)
    response, rate_lim = get_structured_output(prompt, models.Conclusion, state["rate_limit_exceeded"], True)
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
