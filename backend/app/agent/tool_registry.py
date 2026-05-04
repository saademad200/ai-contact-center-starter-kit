import inspect
import json
from collections.abc import Callable

from app.agent.tools.get_fund_nav import get_fund_nav
from app.agent.tools.get_fund_performance import get_fund_performance
from app.agent.tools.search_kb import search_kb

# ── Python function map ───────────────────────────────────────────────────────
TOOL_FUNCTIONS: dict[str, Callable] = {
    "get_fund_nav": get_fund_nav,
    "get_fund_performance": get_fund_performance,
    "search_kb": search_kb,
}

# ── OpenAI JSON schemas ───────────────────────────────────────────────────────
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_fund_nav",
            "description": "Fetches the latest live Net Asset Value (NAV / unit price) for a specific Alfalah mutual fund. Use this when the user asks about current price or NAV.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fund_name": {
                        "type": "string",
                        "description": "The full name of the fund, e.g. 'Alfalah GHP Islamic Income Fund'.",
                    }
                },
                "required": ["fund_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fund_performance",
            "description": "Fetches the latest performance returns (1M, 3M, YTD, 1Y) for a specific Alfalah mutual fund. Use this when the user asks about fund returns or historical performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fund_name": {
                        "type": "string",
                        "description": "The full name of the fund, e.g. 'Alfalah GHP Islamic Income Fund'.",
                    }
                },
                "required": ["fund_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": "Searches the internal knowledge base (fund prospectuses, FAQs, SECP regulations, policies) to answer factual questions. Use this for policy, eligibility, account opening, and fee questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or a search phrase to look up in the knowledge base.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


async def execute_tool(tool_name: str, arguments: str) -> str:
    """Dispatches a tool call from OpenAI and returns the result as a string."""
    if tool_name not in TOOL_FUNCTIONS:
        return f"Error: Tool '{tool_name}' is not registered."
    try:
        args = json.loads(arguments)
        func = TOOL_FUNCTIONS[tool_name]
        if inspect.iscoroutinefunction(func):
            result = await func(**args)
        else:
            result = func(**args)
        return str(result)
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"
