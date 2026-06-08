from langgraph.graph import StateGraph, START, END
import app.research.nodes as nodes
import app.research.models as models

def run_interviews(state: models.InterviewState):
    result = interview_graph.invoke(state)

    return {"reports": [result["report"]]}

interview_builder = StateGraph(models.InterviewState)
interview_builder.add_node("ask_question", nodes.ask_question)
interview_builder.add_node("create_search_query", nodes.create_search_query)
interview_builder.add_node("search_web", nodes.search_web)
interview_builder.add_node("search_wikipedia", nodes.search_wikipidea)
interview_builder.add_node("answer_question", nodes.answer_question)
interview_builder.add_node("create_interview_report", nodes.create_interview_report)

interview_builder.add_edge(START, "ask_question")
interview_builder.add_edge("ask_question", "create_search_query")
interview_builder.add_edge("create_search_query", "search_wikipedia")
interview_builder.add_edge("create_search_query", "search_web")
interview_builder.add_edge("search_wikipedia", "answer_question")
interview_builder.add_edge("search_web", "answer_question")
interview_builder.add_conditional_edges("answer_question", nodes.continue_or_end_interview, {"continue": "ask_question", "end": "create_interview_report"})
interview_builder.add_edge("create_interview_report", END)

interview_graph = interview_builder.compile()

graph_builder = StateGraph(models.OverallState)
graph_builder.add_node("create_analysts", nodes.create_analysts)
graph_builder.add_node("interview", run_interviews)
graph_builder.add_node("create_introduction", nodes.create_report_introduction)
graph_builder.add_node("create_body", nodes.create_report_body)
graph_builder.add_node("create_conclusion", nodes.create_report_conclusion)

graph_builder.add_edge(START, "create_analysts")
graph_builder.add_conditional_edges("create_analysts", nodes.move_to_inverviews, ["interview"])
graph_builder.add_edge("interview", "create_introduction")
graph_builder.add_edge("interview", "create_body")
graph_builder.add_edge("interview", "create_conclusion")
graph_builder.add_edge("create_introduction", END)
graph_builder.add_edge("create_body", END)
graph_builder.add_edge("create_conclusion", END)

graph = graph_builder.compile()

print(graph.invoke({"topic": "People's attachment to material things."}))
