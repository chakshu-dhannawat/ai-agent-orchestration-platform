"""Tool registry with real, working tools for agent workflows."""

from __future__ import annotations

import ast
import operator
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from langchain_core.tools import tool


# ---------------------------------------------------------------------------
# Web search via DuckDuckGo
# ---------------------------------------------------------------------------
@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return top 5 results with titles, snippets, and URLs."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        if not results:
            return "No results found."

        formatted: list[str] = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            body = r.get("body", "No snippet")
            href = r.get("href", r.get("link", ""))
            formatted.append(f"{i}. **{title}**\n   {body}\n   URL: {href}")

        return "\n\n".join(formatted)
    except Exception as exc:
        return f"Search error: {exc}"


# ---------------------------------------------------------------------------
# Web scrape: fetch a URL and extract readable text
# ---------------------------------------------------------------------------
@tool
def web_scrape(url: str) -> str:
    """Fetch a web page and extract its main text content (max 3000 characters)."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)

        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        if len(text) > 3000:
            text = text[:3000] + "\n\n... [truncated]"

        return text if text.strip() else "No readable text found on the page."
    except httpx.HTTPStatusError as exc:
        return f"HTTP error {exc.response.status_code} fetching {url}"
    except Exception as exc:
        return f"Scrape error: {exc}"


# ---------------------------------------------------------------------------
# Calculator: safely evaluate math expressions
# ---------------------------------------------------------------------------

# Allowed operators for safe evaluation
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval_node(node: ast.AST) -> float | int:
    """Recursively evaluate an AST node using only safe arithmetic operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        # Prevent excessively large exponents
        if op_type is ast.Pow and isinstance(right, (int, float)) and abs(right) > 1000:
            raise ValueError("Exponent too large (max 1000)")
        return _SAFE_OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return _SAFE_OPERATORS[op_type](operand)
    else:
        raise ValueError(f"Unsupported expression node: {type(node).__name__}")


@tool
def calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression and return the result.

    Supports: +, -, *, /, //, %, ** and parentheses.
    Examples: '2 + 3 * 4', '(10 - 3) ** 2', '100 / 7'
    """
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval_node(tree)
        return str(result)
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as exc:
        return f"Calculation error: {exc}"


# ---------------------------------------------------------------------------
# File writer: writes content to a virtual file stored in execution results
# ---------------------------------------------------------------------------
@tool
def file_writer(filename: str, content: str) -> str:
    """Write content to a virtual file. The file will be stored in the execution results.

    Args:
        filename: Name for the virtual file (e.g. 'report.md', 'data.csv')
        content: The text content to write to the file
    """
    # The actual storage is handled by the agent node which reads the tool
    # output and stores it in state.intermediate_results. We return a
    # structured marker that the node can parse.
    return f"__FILE_WRITE__:{filename}:{content}"


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

_TOOL_REGISTRY: dict[str, Any] = {
    "web_search": web_search,
    "web_scrape": web_scrape,
    "calculator": calculator,
    "file_writer": file_writer,
}


def get_tool_by_name(name: str):
    """Look up a tool by its string name. Returns None if not found."""
    return _TOOL_REGISTRY.get(name)


def get_tools_by_names(names: list[str]) -> list:
    """Return a list of tool objects for the given tool name strings."""
    tools = []
    for name in names:
        t = get_tool_by_name(name)
        if t is not None:
            tools.append(t)
    return tools
