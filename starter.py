import asyncio
import uuid

from temporalio.client import Client

from models import GenerateReportInput, UserDecision, UserDecisionSignal
from workflow import GenerateReportWorkflow  # Your Workflow definition


async def send_user_decision_signal(client: Client, workflow_id: str):
    # Get handle to the Workflow Execution
    handle = client.get_workflow_handle(workflow_id)

    while True:
        print("\n" + "=" * 80)
        print("Calling LLM! Check the Web UI for the research output.")
        print("Would you like to keep or edit it?")
        print("1. Type 'keep' to approve the output and create PDF")
        print("2. Type 'edit' to modify the output")
        print("=" * 80)

        decision = input("Your decision (keep/edit): ").strip().lower()

        if decision in {"keep", "1"}:
            signal_data = UserDecisionSignal(decision=UserDecision.KEEP)
            await handle.signal("user_decision_signal", signal_data)
            print("Signal sent to keep output and create PDF")
            break

        elif decision in {"edit", "2"}:
            additional_prompt = input(
                "Enter additional instructions (optional): "
            ).strip()
            signal_data = UserDecisionSignal(
                decision=UserDecision.EDIT, additional_prompt=additional_prompt
            )
            await handle.signal("user_decision_signal", signal_data)
            print("Signal sent to regenerate output")

        else:
            print("Please enter either 'keep' or 'edit'")


async def main():
    # Connect to the Temporal service
    client = await Client.connect("localhost:7233", namespace="default")

    # Get user input for research topic
    print("Welcome to the Research Report Generator!")
    prompt = input("Enter your research topic or question: ").strip()

    if not prompt:
        prompt = "Give me 5 fun and fascinating facts about tardigrades."
        print(f"No prompt entered. Using default: {prompt}")

    # The input data for your Workflow, including the prompt and API key
    research_input = GenerateReportInput(prompt=prompt)

    # Start the Workflow execution
    handle = await client.start_workflow(
        GenerateReportWorkflow,  # The Workflow method to execute
        research_input,
        id=f"tutorial-{uuid.uuid4()}",
        task_queue="tutorial",  # task queue your Worker is polling
    )

    _signal_task = asyncio.create_task(send_user_decision_signal(client, handle.id))

    print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")
    result = await handle.result()
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
