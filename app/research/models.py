from langgraph.graph import MessagesState
from typing import Annotated, TypedDict, Literal
import operator
from dataclasses import dataclass
from pydantic import BaseModel, Field

class OverallState(TypedDict):
    topic: str
    analysts: Annotated[list, operator.add]
    analysts_quantity: int 
    interview_questions: int 
    reports: Annotated[list, operator.add]
    rate_limit_exceeded: bool
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
    interview_questions: int
    rate_limit_exceeded: bool
    report: str

class SearchState(TypedDict):
    query: str

class Question(BaseModel):
    question: str = Field("Question to ask expert about topic. Shoould be really good one that will open the topic by itself.")

class SearchQuery(BaseModel):
    query: str = Field("Search query that will help to provide information to answer the question of the analytic.")

class Response(BaseModel):
    response: str = Field("Response to the question of the Data Analyst, must be based on the resources and be clear.")

class Report(BaseModel):
    report: str = Field("Report of the interview between the Analyst and Expert, must be detailed and specific.")

class Introduction(BaseModel):
    introduction: str = Field("Introduction of the research. Shouldn't be very long, just introduces with the topic and data.")

class ReportBody(BaseModel):
    report_body: str = Field("Report body, biggest part of the research, where all details and data should be described and explained, without making any introduction and conclusiton parts, only main body with information.")

class Conclusion(BaseModel):
    conclusion: str = Field("Conlclusion for the report. Must be really good written and summ's up all data to few sentences.")

class TopicAsignment(BaseModel):
    response: str = Field("Your response to the user. Write only when the topic is unclear and we need to specify something. If everything is clear leave it emty.")
    research_or_assign: Literal["research", "assign"] = Field("Decide should we proceed to the research or continue to clarify the topic. Pick 'research' to move on, and 'assign' to continue discussion with the user.")
    clear_topic: str = Field("Clear topic. If user provided it by first message you can just paste it there, if you discussed it make a clear topic so our research will be great.")