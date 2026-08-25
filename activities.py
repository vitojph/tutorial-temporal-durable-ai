import os

from dotenv import load_dotenv
from litellm import completion
from litellm.types.utils import ModelResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from temporalio import activity

from models import LLMCallInput, PDFGenerationInput

load_dotenv(override=True)  # Reads your .env file and loads your environment variables

# Get LLM_API_KEY environment variable
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-5.6-luna")
LLM_API_KEY = os.getenv("LLM_API_KEY", None)


@activity.defn
def llm_call(input: LLMCallInput) -> ModelResponse:
    return completion(
        model=LLM_MODEL,
        api_key=LLM_API_KEY,
        messages=[{"content": input.prompt, "role": "user"}],
    )


@activity.defn
def create_pdf(input: PDFGenerationInput) -> str:
    doc = SimpleDocTemplate(input.filename, pagesize=letter)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        spaceAfter=30,
        alignment=1,
    )

    story: list[Flowable] = []
    title = Paragraph("Research Report", title_style)
    story.append(title)
    story.append(Spacer(1, 20))

    paragraphs = input.content.split("\n\n")
    for para in paragraphs:
        if para.strip():
            p = Paragraph(para.strip(), styles["Normal"])
            story.append(p)
            story.append(Spacer(1, 12))

    doc.build(story)
    return input.filename


@activity.defn
def send_email() -> str:
    """Simulates sending e-mail"""

    # This simulates a temporary failure - maybe a database is down,
    # or an API is temporarily unavailable
    # raise ApplicationError("Simulated failure: Email service temporarily unavailable")

    # This code would run if we remove the error above
    return "Email sent"
