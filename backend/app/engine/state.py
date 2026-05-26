from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class WorkflowState(TypedDict):
    """State that flows through every node in a compiled workflow graph."""

    # Conversation thread - uses LangGraph's built-in message reducer
    # so each node can append messages without overwriting the history.
    messages: Annotated[list[BaseMessage], add_messages]

    # The original user input that triggered this execution.
    current_input: str

    # Results collected from each node, keyed by node_id.
    intermediate_results: dict

    # The final text output of the workflow (set by the last agent or end node).
    final_output: str | None

    # Accumulated metadata: token counts, costs, timing, etc.
    metadata: dict
