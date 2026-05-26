"""
Pre-built workflow templates for the AI Agent Orchestration Platform.

Each template module exposes:
  - TEMPLATE_ID, TEMPLATE_NAME, TEMPLATE_DESCRIPTION
  - AGENTS: list of agent configuration dicts
  - GRAPH_DEFINITION: React Flow graph (nodes + edges)
"""

from app.templates import customer_support, research_summarize

TEMPLATES = [
    {
        "id": research_summarize.TEMPLATE_ID,
        "name": research_summarize.TEMPLATE_NAME,
        "description": research_summarize.TEMPLATE_DESCRIPTION,
        "agents": research_summarize.AGENTS,
        "graph_definition": research_summarize.GRAPH_DEFINITION,
    },
    {
        "id": customer_support.TEMPLATE_ID,
        "name": customer_support.TEMPLATE_NAME,
        "description": customer_support.TEMPLATE_DESCRIPTION,
        "agents": customer_support.AGENTS,
        "graph_definition": customer_support.GRAPH_DEFINITION,
    },
]


def get_template_by_id(template_id: str) -> dict | None:
    """Return a template dict by its string id, or None if not found."""
    for template in TEMPLATES:
        if template["id"] == template_id:
            return template
    return None
