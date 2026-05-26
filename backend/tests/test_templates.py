"""Tests for the pre-built workflow templates."""

import pytest

from app.templates import TEMPLATES, get_template_by_id
from app.templates.customer_support import (
    AGENTS as CS_AGENTS,
    GRAPH_DEFINITION as CS_GRAPH,
    TEMPLATE_ID as CS_ID,
    TEMPLATE_NAME as CS_NAME,
)
from app.templates.research_summarize import (
    AGENTS as RS_AGENTS,
    GRAPH_DEFINITION as RS_GRAPH,
    TEMPLATE_ID as RS_ID,
    TEMPLATE_NAME as RS_NAME,
)


class TestTemplateRegistry:
    """Verify that all templates are registered correctly."""

    def test_list_templates_count(self):
        """TEMPLATES list should contain exactly 2 templates."""
        assert len(TEMPLATES) == 2

    def test_list_templates_ids(self):
        """Both known template IDs should be present."""
        ids = {t["id"] for t in TEMPLATES}
        assert "research_summarize" in ids
        assert "customer_support" in ids

    def test_get_template_by_id_research(self):
        """get_template_by_id returns the research_summarize template."""
        t = get_template_by_id("research_summarize")
        assert t is not None
        assert t["name"] == RS_NAME

    def test_get_template_by_id_customer_support(self):
        """get_template_by_id returns the customer_support template."""
        t = get_template_by_id("customer_support")
        assert t is not None
        assert t["name"] == CS_NAME

    def test_get_template_by_id_unknown(self):
        """get_template_by_id returns None for an unknown id."""
        assert get_template_by_id("nonexistent_template") is None


class TestResearchTemplateStructure:
    """Verify the research_summarize template has the correct structure."""

    def test_template_id(self):
        assert RS_ID == "research_summarize"

    def test_template_name(self):
        assert RS_NAME == "Research & Summarize"

    def test_agents_count(self):
        """Research template should define exactly 3 agents."""
        assert len(RS_AGENTS) == 3

    def test_agent_names(self):
        names = {a["name"] for a in RS_AGENTS}
        assert names == {"Researcher", "Writer", "Reviewer"}

    def test_agent_roles(self):
        roles = {a["role"] for a in RS_AGENTS}
        assert roles == {"researcher", "writer", "reviewer"}

    def test_graph_nodes_count(self):
        """Research template graph should have 6 nodes."""
        nodes = RS_GRAPH["nodes"]
        assert len(nodes) == 6

    def test_graph_edges_count(self):
        """Research template graph should have 6 edges."""
        edges = RS_GRAPH["edges"]
        assert len(edges) == 6

    def test_graph_node_types(self):
        node_types = {n["type"] for n in RS_GRAPH["nodes"]}
        assert "start" in node_types
        assert "end" in node_types
        assert "agent" in node_types
        assert "condition" in node_types

    def test_researcher_has_search_tools(self):
        """The Researcher agent should have web_search and web_scrape tools."""
        researcher = next(a for a in RS_AGENTS if a["name"] == "Researcher")
        assert "web_search" in researcher["tools"]
        assert "web_scrape" in researcher["tools"]


class TestCustomerSupportTemplateStructure:
    """Verify the customer_support template has the correct structure."""

    def test_template_id(self):
        assert CS_ID == "customer_support"

    def test_template_name(self):
        assert CS_NAME == "Customer Support Triage"

    def test_agents_count(self):
        """Customer support template should define 4 agents."""
        assert len(CS_AGENTS) == 4

    def test_agent_names(self):
        names = {a["name"] for a in CS_AGENTS}
        expected = {
            "Triage Agent",
            "Billing Support Agent",
            "Technical Support Agent",
            "General Support Agent",
        }
        assert names == expected

    def test_graph_nodes_count(self):
        """Customer support template graph should have 7 nodes."""
        nodes = CS_GRAPH["nodes"]
        assert len(nodes) == 7

    def test_graph_edges_count(self):
        """Customer support template graph should have 8 edges."""
        edges = CS_GRAPH["edges"]
        assert len(edges) == 8

    def test_graph_has_condition_node(self):
        condition_nodes = [n for n in CS_GRAPH["nodes"] if n["type"] == "condition"]
        assert len(condition_nodes) >= 1

    def test_billing_agent_has_calculator(self):
        """Billing Support Agent should have the calculator tool."""
        billing = next(a for a in CS_AGENTS if a["name"] == "Billing Support Agent")
        assert "calculator" in billing["tools"]

    def test_technical_agent_has_web_search(self):
        """Technical Support Agent should have the web_search tool."""
        tech = next(a for a in CS_AGENTS if a["name"] == "Technical Support Agent")
        assert "web_search" in tech["tools"]


class TestTemplateGraphStartAndEnd:
    """Both templates must have start and end nodes in their graphs."""

    @pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t["id"])
    def test_template_has_start_node(self, template):
        nodes = template["graph_definition"]["nodes"]
        start_nodes = [n for n in nodes if n["type"] == "start"]
        assert len(start_nodes) >= 1, f"Template '{template['id']}' has no start node"

    @pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t["id"])
    def test_template_has_end_node(self, template):
        nodes = template["graph_definition"]["nodes"]
        end_nodes = [n for n in nodes if n["type"] == "end"]
        assert len(end_nodes) >= 1, f"Template '{template['id']}' has no end node"


class TestTemplateAgentsHaveRequiredFields:
    """All template agents must have name, role, and system_prompt."""

    @pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t["id"])
    def test_agents_have_required_fields(self, template):
        for agent in template["agents"]:
            assert "name" in agent and agent["name"], (
                f"Agent in '{template['id']}' missing 'name'"
            )
            assert "role" in agent and agent["role"], (
                f"Agent '{agent.get('name', '?')}' in '{template['id']}' missing 'role'"
            )
            assert "system_prompt" in agent and agent["system_prompt"], (
                f"Agent '{agent.get('name', '?')}' in '{template['id']}' missing 'system_prompt'"
            )

    @pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t["id"])
    def test_agents_have_model_field(self, template):
        for agent in template["agents"]:
            assert "model" in agent and agent["model"], (
                f"Agent '{agent['name']}' in '{template['id']}' missing 'model'"
            )

    @pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t["id"])
    def test_agents_have_tools_field(self, template):
        for agent in template["agents"]:
            assert "tools" in agent, (
                f"Agent '{agent['name']}' in '{template['id']}' missing 'tools'"
            )
            assert isinstance(agent["tools"], list), (
                f"Agent '{agent['name']}' tools should be a list"
            )
