from dataclasses import dataclass
from enum import StrEnum


@dataclass
class LLMCallInput:
    prompt: str


@dataclass
class PDFGenerationInput:
    content: str
    filename: str = "final_report.pdf"


@dataclass
class GenerateReportInput:
    prompt: str


class UserDecision(StrEnum):
    KEEP = "KEEP"
    EDIT = "EDIT"
    WAIT = "WAIT"


@dataclass
class UserDecisionSignal:
    decision: UserDecision
    additional_prompt: str = ""
