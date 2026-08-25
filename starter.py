import asyncio
import uuid

from temporalio.client import Client

from models import GenerateReportInput, UserDecision, UserDecisionSignal
from workflow import GenerateReportWorkflow  # Your Workflow definition


async def send_user_decision(client: Client, workflow_id: str):
    handle = client.get_workflow_handle(workflow_id)

    while True:
        print("\n" + "=" * 50)
        print("Research is complete!")
        print("1. Type 'query' to view the current research result")
        print("2. Type 'keep' to approve the research and create PDF")
        print("3. Type 'edit' to modify the research")
        print("=" * 50)

        decision = input("Your decision (query/keep/edit): ").strip().lower()

        if decision in {"query", "1"}:
            await query_research_result(client, workflow_id)
        elif decision in {"keep", "2"}:
            signal_data = UserDecisionSignal(decision=UserDecision.KEEP)
            await handle.signal("user_decision_signal", signal_data)
            print("Signal sent to keep research and create PDF")
            break
        elif decision in {"edit", "3"}:
            additional_prompt = input("Enter new instructions (optional): ").strip()
            signal_data = UserDecisionSignal(
                decision=UserDecision.EDIT, additional_prompt=additional_prompt
            )
            await handle.signal("user_decision_signal", signal_data)
            print("Signal sent to regenerate research")
        else:
            print("Please enter either 'keep', 'edit', or 'query'")


async def query_research_result(client: Client, workflow_id: str):
    handle = client.get_workflow_handle(workflow_id)

    try:
        research_result = await handle.query(GenerateReportWorkflow.get_research_result)
        if research_result:
            print(f"\nResearch Result:\n{research_result}\n")
        else:
            print("Research Result: Not yet available")
    except Exception as e:
        print(f"Query failed: {e}")


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

    _signal_task = asyncio.create_task(send_user_decision(client, handle.id))

    print(f"Started workflow. Workflow ID: {handle.id}, RunID {handle.result_run_id}")
    result = await handle.result()
    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
