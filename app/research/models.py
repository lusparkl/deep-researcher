from langgraph.graph import MessagesState
from typing import Annotated, TypedDict
import operator
from dataclasses import dataclass
from pydantic import BaseModel, Field

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
