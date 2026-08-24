import asyncio
import concurrent.futures

from temporalio.client import Client
from temporalio.worker import Worker

from activities import create_pdf, llm_call, send_email
from workflow import GenerateReportWorkflow


async def run_worker():
    client = await Client.connect("localhost:7233", namespace="default")

    # Create a thread pool for running Activities
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        # Configure the Worker
        worker = Worker(
            client,
            task_queue="tutorial",  # Task queue that your Worker is listening to.
            workflows=[GenerateReportWorkflow],  # Register the Workflow on your Worker
            activities=[
                llm_call,
                create_pdf,
                send_email,
            ],  # Register the Activities on your Worker
            activity_executor=activity_executor,  # Thread pool that allows Activities to run concurrently
        )

        print("Starting the worker... ")
        await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
