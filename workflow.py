from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import create_pdf, llm_call, send_email
    from models import (
        GenerateReportInput,
        LLMCallInput,
        PDFGenerationInput,
    )


@workflow.defn
class GenerateReportWorkflow:
    @workflow.run
    async def run(self, input: GenerateReportInput) -> str:
        llm_call_input = LLMCallInput(prompt=input.prompt)

        # Step 1: Call LLM Activity
        research_facts = await workflow.execute_activity(
            llm_call,
            llm_call_input,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
                backoff_coefficient=3.0,
            ),
        )

        pdf_generation_input = PDFGenerationInput(
            content=research_facts["choices"][0]["message"]["content"]
        )

        # Step 2: Create PDF Activity
        pdf_filename = await workflow.execute_activity(
            create_pdf,
            pdf_generation_input,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
                backoff_coefficient=3.0,
            ),
        )

        # step 3 send an temporalio
        _email_sent = await workflow.execute_activity(
            send_email,
            start_to_close_timeout=timedelta(seconds=20),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_attempts=3,
                backoff_coefficient=3.0,
            ),
        )

        return f"Successfully created research report PDF: {pdf_filename}"
