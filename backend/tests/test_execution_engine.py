"""Tests for the workflow execution engine components.

All LLM calls are mocked so tests run without an OpenAI API key.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# -----------------------------------------------------------------------
# WorkflowState TypedDict structure
# -----------------------------------------------------------------------
class TestWorkflowState:
    """Verify WorkflowState TypedDict has the expected fields."""

    def test_workflow_state_has_required_keys(self):
        from app.engine.state import WorkflowState

        annotations = WorkflowState.__annotations__
        expected_keys = {
            "messages",
            "current_input",
            "intermediate_results",
            "final_output",
            "metadata",
        }
        assert expected_keys == set(annotations.keys())

    def test_workflow_state_can_be_instantiated(self):
        """WorkflowState can be created as a plain dict matching the TypedDict shape."""
        from app.engine.state import WorkflowState

        state: WorkflowState = {
            "messages": [],
            "current_input": "hello",
            "intermediate_results": {},
            "final_output": None,
            "metadata": {},
        }
        assert state["current_input"] == "hello"
        assert state["final_output"] is None
        assert isinstance(state["messages"], list)


# -----------------------------------------------------------------------
# Tool registry
# -----------------------------------------------------------------------
class TestToolRegistry:
    """Test the tool registry in app.engine.tools."""

    def test_get_tool_by_name_returns_calculator(self):
        from app.engine.tools import get_tool_by_name

        tool = get_tool_by_name("calculator")
        assert tool is not None
        assert tool.name == "calculator"

    def test_get_tool_by_name_returns_web_search(self):
        from app.engine.tools import get_tool_by_name

        tool = get_tool_by_name("web_search")
        assert tool is not None
        assert tool.name == "web_search"

    def test_get_tool_by_name_returns_web_scrape(self):
        from app.engine.tools import get_tool_by_name

        tool = get_tool_by_name("web_scrape")
        assert tool is not None
        assert tool.name == "web_scrape"

    def test_get_tool_by_name_returns_file_writer(self):
        from app.engine.tools import get_tool_by_name

        tool = get_tool_by_name("file_writer")
        assert tool is not None
        assert tool.name == "file_writer"

    def test_get_tool_by_name_returns_none_for_unknown(self):
        from app.engine.tools import get_tool_by_name

        tool = get_tool_by_name("nonexistent_tool")
        assert tool is None

    def test_get_tools_by_names(self):
        from app.engine.tools import get_tools_by_names

        tools = get_tools_by_names(["calculator", "web_search"])
        assert len(tools) == 2
        names = {t.name for t in tools}
        assert names == {"calculator", "web_search"}

    def test_get_tools_by_names_skips_unknown(self):
        from app.engine.tools import get_tools_by_names

        tools = get_tools_by_names(["calculator", "unknown_tool"])
        assert len(tools) == 1
        assert tools[0].name == "calculator"

    def test_get_tools_by_names_empty_list(self):
        from app.engine.tools import get_tools_by_names

        tools = get_tools_by_names([])
        assert tools == []


# -----------------------------------------------------------------------
# Calculator tool
# -----------------------------------------------------------------------
class TestCalculatorTool:
    """Test the calculator tool with various expressions."""

    def _invoke_calculator(self, expression: str) -> str:
        from app.engine.tools import calculator

        return calculator.invoke({"expression": expression})

    def test_addition(self):
        assert self._invoke_calculator("2 + 3") == "5"

    def test_subtraction(self):
        assert self._invoke_calculator("10 - 4") == "6"

    def test_multiplication(self):
        assert self._invoke_calculator("6 * 7") == "42"

    def test_division(self):
        result = self._invoke_calculator("10 / 4")
        assert float(result) == 2.5

    def test_floor_division(self):
        assert self._invoke_calculator("10 // 3") == "3"

    def test_modulo(self):
        assert self._invoke_calculator("10 % 3") == "1"

    def test_exponentiation(self):
        assert self._invoke_calculator("2 ** 10") == "1024"

    def test_complex_expression(self):
        result = self._invoke_calculator("(2 + 3) * 4")
        assert result == "20"

    def test_nested_parentheses(self):
        result = self._invoke_calculator("((1 + 2) * (3 + 4))")
        assert result == "21"

    def test_negative_numbers(self):
        result = self._invoke_calculator("-5 + 3")
        assert result == "-2"

    def test_division_by_zero(self):
        result = self._invoke_calculator("1 / 0")
        assert "Division by zero" in result

    def test_invalid_expression(self):
        result = self._invoke_calculator("hello world")
        assert "error" in result.lower()

    def test_large_exponent_blocked(self):
        result = self._invoke_calculator("2 ** 10000")
        assert "error" in result.lower() or "Exponent too large" in result


# -----------------------------------------------------------------------
# Graph compilation (mock LLM)
# -----------------------------------------------------------------------
class TestGraphCompilation:
    """Test that the runtime can compile a simple graph definition."""

    async def test_compile_simple_graph(self):
        """Compile a start -> end graph and verify the result is a CompiledStateGraph."""
        from langgraph.graph.state import CompiledStateGraph

        from app.engine.runtime import WorkflowRuntime

        ws_manager = AsyncMock()
        ws_manager.broadcast_to_execution = AsyncMock()
        ws_manager.broadcast_to_dashboard = AsyncMock()

        db_session_factory = AsyncMock()

        runtime = WorkflowRuntime(
            ws_manager=ws_manager,
            db_session_factory=db_session_factory,
        )

        graph_def = {
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": "Start"},
                },
                {
                    "id": "end",
                    "type": "end",
                    "position": {"x": 0, "y": 200},
                    "data": {"label": "End"},
                },
            ],
            "edges": [
                {
                    "id": "e1",
                    "source": "start",
                    "target": "end",
                    "type": "default",
                },
            ],
        }

        compiled = await runtime.compile(
            workflow_dict=graph_def,
            agents_map={},
            execution_id="test-exec-001",
        )

        assert isinstance(compiled, CompiledStateGraph)

    async def test_compile_graph_with_agent_node(self):
        """Compile a graph containing an agent node (LLM is not called at compile time)."""
        from langgraph.graph.state import CompiledStateGraph

        from app.engine.runtime import WorkflowRuntime

        ws_manager = AsyncMock()
        ws_manager.broadcast_to_execution = AsyncMock()
        ws_manager.broadcast_to_dashboard = AsyncMock()

        db_session_factory = AsyncMock()

        runtime = WorkflowRuntime(
            ws_manager=ws_manager,
            db_session_factory=db_session_factory,
        )

        agent_id = "agent-123"
        graph_def = {
            "nodes": [
                {
                    "id": "start",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {"label": "Start"},
                },
                {
                    "id": "agent_node",
                    "type": "agent",
                    "position": {"x": 0, "y": 100},
                    "data": {
                        "label": "Test Agent",
                        "agentId": agent_id,
                    },
                },
                {
                    "id": "end",
                    "type": "end",
                    "position": {"x": 0, "y": 200},
                    "data": {"label": "End"},
                },
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "agent_node"},
                {"id": "e2", "source": "agent_node", "target": "end"},
            ],
        }

        agents_map = {
            agent_id: {
                "name": "Test Agent",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 4096,
                "system_prompt": "You are a test agent.",
                "guardrails": {},
                "tools": [],
            },
        }

        compiled = await runtime.compile(
            workflow_dict=graph_def,
            agents_map=agents_map,
            execution_id="test-exec-002",
        )

        assert isinstance(compiled, CompiledStateGraph)


# -----------------------------------------------------------------------
# Workflow validate_graph (service-level, no DB)
# -----------------------------------------------------------------------
class TestValidateGraph:
    """Test WorkflowService.validate_graph static method directly."""

    def test_valid_graph(self):
        from app.services.workflow_service import WorkflowService

        graph_def = {
            "nodes": [
                {"id": "start", "type": "start", "data": {"label": "Start"}},
                {"id": "end", "type": "end", "data": {"label": "End"}},
            ],
            "edges": [
                {"id": "e1", "source": "start", "target": "end"},
            ],
        }
        result = WorkflowService.validate_graph(graph_def)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["node_count"] == 2
        assert result["edge_count"] == 1

    def test_empty_graph(self):
        from app.services.workflow_service import WorkflowService

        result = WorkflowService.validate_graph({})
        assert result["valid"] is False

    def test_graph_with_no_nodes(self):
        from app.services.workflow_service import WorkflowService

        result = WorkflowService.validate_graph({"nodes": [], "edges": []})
        assert result["valid"] is False
        assert any("at least one node" in e for e in result["errors"])

    def test_edge_referencing_unknown_node(self):
        from app.services.workflow_service import WorkflowService

        graph_def = {
            "nodes": [{"id": "start", "type": "start", "data": {}}],
            "edges": [{"id": "e1", "source": "start", "target": "ghost"}],
        }
        result = WorkflowService.validate_graph(graph_def)
        assert result["valid"] is False
        assert any("ghost" in e for e in result["errors"])

    def test_node_without_id(self):
        from app.services.workflow_service import WorkflowService

        graph_def = {
            "nodes": [{"type": "start", "data": {}}],
            "edges": [],
        }
        result = WorkflowService.validate_graph(graph_def)
        assert result["valid"] is False
        assert any("id" in e.lower() for e in result["errors"])
