from dataclasses import dataclass


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
