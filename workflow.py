from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from models import UserDecision

with workflow.unsafe.imports_passed_through():
    from activities import create_pdf, llm_call, send_email
    from models import (
        GenerateReportInput,
        LLMCallInput,
        PDFGenerationInput,
        UserDecisionSignal,
    )


@workflow.defn
class GenerateReportWorkflow:
    def __init__(self) -> None:
        self._current_prompt: str = ""
        self._user_decision: UserDecisionSignal = UserDecisionSignal(
            decision=UserDecision.WAIT
        )

    @workflow.signal
    async def user_decision_signal(self, decision_data: UserDecisionSignal) -> None:
        self._user_decision = decision_data

    @workflow.run
    async def run(self, input: GenerateReportInput) -> str:
        llm_call_input = LLMCallInput(prompt=input.prompt)

        # Continue looping until the user approves the research
        continue_user_input_loop = True

        # Execute the LLM call to generate research based on the current prompt
        while continue_user_input_loop:
            research_facts = await workflow.execute_activity(
                llm_call,
                llm_call_input,
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Waiting for Signal with user decision
            await workflow.wait_condition(
                lambda: self._user_decision.decision != UserDecision.WAIT
            )

            # User approved the research - exit the loop and proceed to PDF generation
            if self._user_decision.decision == UserDecision.KEEP:
                workflow.logger.info("User approved the research. Creating PDF...")
                continue_user_input_loop = False
            # User wants to edit the research - update the prompt and loop again
            elif self._user_decision.decision == UserDecision.EDIT:
                workflow.logger.info("User requested research modification.")
                if self._user_decision.additional_prompt != "":
                    # Append the user's additional instructions to the existing prompt
                    self._current_prompt = f"{self._current_prompt}\n\nAdditional instructions: {self._user_decision.additional_prompt}"
                else:
                    workflow.logger.info(
                        "No additional instructions provided. Regenerating with original prompt."
                    )
                # Update the Activity input with the modified prompt for the next iteration
                llm_call_input.prompt = self._current_prompt
                self._user_decision = UserDecisionSignal(decision=UserDecision.WAIT)

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
