# Adding Temporal to Your Gen-AI Application Tutorial

This repository contains the code that goes along with our [`Adding Durability to AI Applications with Temporal`](https://learn.temporal.io/tutorials/ai/building-durable-ai-applications/durable-ai-with-temporal/) tutorial. Please reference that tutorial to see how to use this repository.

To see the completed code after following the tutorial, reference the `temporal_code` directory
=======

## Overview

This application generates research reports using LLM calls (OpenAI), creates PDF outputs, and implements human-in-the-loop interaction through Temporal's signals and queries. Users can approve, edit, or query research results in real-time without interrupting the workflow execution.

**Key Features:**

- Durable workflow execution with automatic retry policies
- LLM-based research generation with edit capability
- PDF report generation
- Real-time query support for progress monitoring
- Human-in-the-loop decision making via signals
- Resilience to failures through Temporal's durability guarantees

## Temporal Concepts

### **Workflow**

A workflow is the high-level orchestrator of your application logic. It defines the sequence of steps, decision logic, and failure handling for your business process.

In this project, `GenerateReportWorkflow` orchestrates the entire report generation process:

- Calls the LLM activity to generate research
- Waits for user approval via signals
- Handles user edits by re-running the LLM with modified prompts
- Executes PDF generation and email sending activities
- Implements retry policies for resilience

Key characteristics:

- **Deterministic**: Same inputs produce same execution paths
- **Durable**: Execution state survives failures and infrastructure changes
- **Observable**: Full execution history is preserved

### **Activities**

Activities are individual, potentially long-running tasks executed outside the workflow. They perform the actual business logic: making API calls, database operations, external service interactions.

This project includes three activities:

- `llm_call`: Calls OpenAI API to generate research based on a prompt
- `create_pdf`: Generates a PDF file from research content
- `send_email`: Simulates email delivery (with error handling capabilities)

Activities are:

- **Fault-tolerant**: Can fail and be retried with exponential backoff
- **Independently scalable**: Can be distributed across multiple worker processes
- **Isolated**: Cannot directly access workflow state; must pass inputs/outputs

### **Worker**

The worker is the process that executes workflows and activities. It connects to Temporal Server, polls a task queue for work, and executes the corresponding workflows/activities.

`worker.py` registers:

- The `GenerateReportWorkflow` class
- Activity functions (llm_call, create_pdf, send_email)
- A thread pool executor for concurrent activity execution
- Connects to the Temporal Server and listens on the "tutorial" task queue

Workers can be:

- **Scalable**: Run multiple instances to handle load
- **Independent**: Each worker is autonomous and stateless
- **Flexible**: Can be deployed on any infrastructure with access to Temporal Server

### **Signals**

Signals are asynchronous messages sent to a running workflow to influence its execution. They allow external systems to communicate with workflows without blocking the sender.

`user_decision_signal` receives:

- User decision (KEEP, EDIT, or WAIT)
- Optional additional prompt for research modifications

In the workflow, signals are received via:

```python
@workflow.signal
async def user_decision_signal(self, decision_data: UserDecisionSignal) -> None:
    self._user_decision = decision_data
```

The workflow waits for the signal:

```python
await workflow.wait_condition(
    lambda: self._user_decision.decision != UserDecision.WAIT
)
```

Signals are:

- **Non-blocking**: Sender doesn't wait for workflow response
- **Reliable**: Guaranteed delivery and durability
- **Stateful**: Can trigger workflow state changes

### **Queries**

Queries allow you to inspect workflow state without modifying it. They're read-only operations that return current data from a running workflow.

`get_research_result` returns the current research content:

```python
@workflow.query
def get_research_result(self) -> str:
    return self._research_result
```

In the starter, users can query the result:

```python
research_result = await handle.query(GenerateReportWorkflow.get_research_result)
```

Queries are:

- **Non-blocking**: Don't pause workflow execution
- **Immediate**: Return current state without waiting
- **Read-only**: Cannot modify workflow state

## Project Structure

- `workflow.py` - Defines the GenerateReportWorkflow orchestration logic
- `activities.py` - Implements individual tasks (LLM call, PDF creation, email sending)
- `worker.py` - Runs the worker process polling for workflow/activity work
- `starter.py` - Initiates workflows and handles user interaction via signals/queries
- `models.py` - Data classes for workflow inputs, signals, and queries
- `temporal_code/` - Reference implementation for the completed tutorial

## Prerequisites

- [OpenAI API key](https://platform.openai.com/api-keys)
- [Temporal CLI](https://docs.temporal.io/cli#install) (for running a local dev server)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python package/dependency manager)

## Getting Started

This project uses [uv](https://docs.astral.sh/uv/) to manage the Python environment and dependencies (see `pyproject.toml`).

1. Install dependencies (creates a `.venv` and installs everything from `pyproject.toml`/`uv.lock`):

   ```bash
   uv sync
   ```

2. Set up your OpenAI API key in `.env`:

   ```bash
   echo "LLM_API_KEY=sk-..." > .env
   ```

3. Start the Temporal dev server in a separate terminal:

   ```bash
   temporal server start-dev
   ```

4. Run the worker (leave it running in its own terminal):

   ```bash
   uv run worker.py
   ```

5. In another terminal, start a workflow:

   ```bash
   uv run starter.py
   ```

`uv run` automatically uses the project's virtual environment, so there's no need to manually activate it.

## Learn More

- [Building Durable AI Applications with Temporal](https://learn.temporal.io/tutorials/ai/building-durable-ai-applications/durable-ai-with-temporal/)
- [Human-in-the-Loop Patterns](https://learn.temporal.io/tutorials/ai/building-durable-ai-applications/human-in-the-loop/)
- [Temporal Python SDK Documentation](https://python.temporal.io/)
