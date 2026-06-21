from langgraph.graph import MessagesState
from typing import Annotated, TypedDict, Literal
import operator
import re
from dataclasses import dataclass
from pydantic import BaseModel, Field
from aiogram.types import Message

class OverallState(TypedDict):
    topic: str
    analysts: Annotated[list, operator.add]
    analysts_quantity: int 
    interview_questions: int 
    reports: Annotated[list, operator.add]
    sources: Annotated[list, operator.add]
    rate_limit_exceeded: Annotated[bool, operator.or_]
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
    position: str = Field(description="Analyst position in the company, with some specifity.")
    background: str = Field(description="Detailed background of the analyst, suitable for the topic of the research of course.")
    character: str = Field(description="Character of the Analytic, can be from very kind and easy going up to boring and nerdy. Pick based on the research topic what's best.")

class CreateAnalysts(BaseModel):
    analysts: list[CreateAnalyst] = Field(description="List of analysts to create")

class InterviewState(MessagesState):
    topic: str
    analyst: Analyst
    context: Annotated[list, operator.add]
    sources: Annotated[list, operator.add]
    interview_questions: int
    rate_limit_exceeded: Annotated[bool, operator.or_]
    report: str

class SearchState(TypedDict):
    query: str

class Question(BaseModel):
    question: str = Field("Question to ask expert about topic. Shoould be really good one that will open the topic by itself.")

class SearchQuery(BaseModel):
    query: str = Field("Search query that will help to provide information to answer the question of the analytic.")

class Source(BaseModel):
    link: str = Field(description="URL of a source used in the research.")
    id: str = Field(description="Stable source identifier, without brackets. Cite it in text as [id].")

def unique_sources(sources: list | None) -> list[Source]:
    if not sources:
        return []

    unique = []
    seen_ids = set()

    for source in sources:
        if isinstance(source, dict):
            raw_id = source.get("id")
            raw_link = source.get("link")
        else:
            raw_id = getattr(source, "id", None)
            raw_link = getattr(source, "link", None)

        if raw_id is None or raw_link is None:
            continue

        source_id = str(raw_id).strip()
        link = str(raw_link).strip()

        if not source_id or not link or source_id in seen_ids:
            continue

        unique.append(Source(id=source_id, link=link))
        seen_ids.add(source_id)

    return unique

def format_source_registry(sources: list | None) -> str:
    source_list = unique_sources(sources)
    if not source_list:
        return "No source metadata was collected."

    return "\n".join(f"[{source.id}] {source.link}" for source in source_list)

MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u20ac\u2122": "'",
    "\u00e2\u20ac\u02dc": "'",
    "\u00e2\u20ac\u0153": '"',
    "\u00e2\u20ac\u009d": '"',
    "\u00e2\u20ac\ufffd": '"',
    "\u00e2\u20ac\u201d": "\u2014",
    "\u00e2\u20ac\u201c": "\u2013",
    "\u00e2\u20ac\u00a6": "\u2026",
    "\u00e2\u20ac\u00a2": "\u2022",
    "\u00e2\u201e\u00a2": "\u2122",
    "\u00e2\u201a\u00ac": "\u20ac",
    "\u00c2\u00a0": " ",
    "\u00c2\u00ad": "",
}

def clean_report_text(text: str) -> str:
    cleaned = text or ""

    for bad_text, fixed_text in MOJIBAKE_REPLACEMENTS.items():
        cleaned = cleaned.replace(bad_text, fixed_text)

    cleaned = cleaned.replace("\ufeff", "")
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = cleaned.replace("\u00c2", "")
    cleaned = re.sub(r"[\u200b\u200c\u200d\u2060]", "", cleaned)
    cleaned = re.sub(r"[^\S\n]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()

def build_source_citation_map(sources: list | None, texts: list[str] | None = None) -> dict[str, str]:
    source_list = unique_sources(sources)
    if not source_list:
        return {}

    sources_by_id = {source.id: source for source in source_list}
    ordered_ids = []
    seen_ids = set()

    for text in texts or []:
        for match in re.finditer(r"\[([^\]]+)\]", text or ""):
            source_id = match.group(1)
            if source_id in sources_by_id and source_id not in seen_ids:
                ordered_ids.append(source_id)
                seen_ids.add(source_id)

    for source in source_list:
        if source.id not in seen_ids:
            ordered_ids.append(source.id)
            seen_ids.add(source.id)

    return {source_id: str(index) for index, source_id in enumerate(ordered_ids, start=1)}

def replace_source_citations(text: str, citation_map: dict[str, str]) -> str:
    if not citation_map:
        return text

    def replace_match(match):
        source_id = match.group(1)
        if source_id not in citation_map:
            return match.group(0)
        return f"[{citation_map[source_id]}]"

    return re.sub(r"\[([^\]]+)\]", replace_match, text)

def format_markdown_sources(sources: list | None, citation_map: dict[str, str] | None = None) -> str:
    source_list = unique_sources(sources)
    if not source_list:
        return "No sources were collected."

    if not citation_map:
        return "\n".join(f"- [{source.id}] {source.link}" for source in source_list)

    ordered_sources = sorted(
        source_list,
        key=lambda source: int(citation_map.get(source.id, "999999")),
    )
    return "\n".join(f"- [{citation_map.get(source.id, source.id)}] {source.link}" for source in ordered_sources)

def renumber_report_citations(introduction: str, report_body: str, conclusion: str, sources: list | None) -> tuple[str, str, str, str]:
    introduction = clean_report_text(introduction)
    report_body = clean_report_text(report_body)
    conclusion = clean_report_text(conclusion)
    citation_map = build_source_citation_map(sources, [introduction, report_body, conclusion])
    return (
        replace_source_citations(introduction, citation_map),
        replace_source_citations(report_body, citation_map),
        replace_source_citations(conclusion, citation_map),
        format_markdown_sources(sources, citation_map),
    )

class Response(BaseModel):
    response: str = Field(description="Response to the question of the Data Analyst. Must be based on the provided resources and include inline citations like [S123abcd].")

class Report(BaseModel):
    report: str = Field(description="Report of the interview between the Analyst and Expert. Must be detailed, specific, and preserve inline source citations.")

class Introduction(BaseModel):
    introduction: str = Field(description="Introduction of the research. Should be concise and include source citations for factual claims.")

class ReportBody(BaseModel):
    report_body: str = Field(description="Report body, biggest part of the research, where all details and data should be described and explained with inline source citations.")

class Conclusion(BaseModel):
    conclusion: str = Field(description="Conclusion for the report. Must synthesize the data and cite source-backed judgments inline.")

class TopicAsignment(BaseModel):
    research_or_assign: Literal["research", "assign"] = Field("Decide should we proceed to the research or continue to clarify the topic. Pick 'research' to move on, and 'assign' to continue discussion with the user.")
    clear_topic: str = Field("Clear topic. If user provided it by first message you can just paste it there, if you discussed it make a clear topic so our research will be great.")

class Clarification(BaseModel):
    clarification: str = Field("Your message to user with request to clarify what user wants to research exactly.")

class TopicAssignmentState(MessagesState):
    message: Message
    rate_limit_exceeded: Annotated[bool, operator.or_]
    clarification: str
    topic: str
    next_node: str
