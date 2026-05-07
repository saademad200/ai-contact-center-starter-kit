"""
Agent Tool Registry
====================
Registers all tools available to the Alfalah GPT agent.
Each tool has:
  - A Python function in TOOL_FUNCTIONS
  - A JSON schema in OPENAI_TOOLS (fed to the OpenAI API)
"""

import inspect
import json
from collections.abc import Callable

from app.agent.tools.calculate_historical_value import calculate_historical_value
from app.agent.tools.get_fund_nav import get_fund_nav
from app.agent.tools.get_fund_performance import get_fund_performance
from app.agent.tools.list_funds import list_funds
from app.agent.tools.project_investment import project_investment
from app.agent.tools.recommend_funds import recommend_funds
from app.agent.tools.search_kb import search_kb

# ── Python function map ───────────────────────────────────────────────────────
TOOL_FUNCTIONS: dict[str, Callable] = {
    "get_fund_nav": get_fund_nav,
    "get_fund_performance": get_fund_performance,
    "list_funds": list_funds,
    "recommend_funds": recommend_funds,
    "project_investment": project_investment,
    "calculate_historical_value": calculate_historical_value,
    "search_kb": search_kb,
}

# ── OpenAI JSON schemas ───────────────────────────────────────────────────────
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_fund_nav",
            "description": (
                "Fetches the latest live Net Asset Value (NAV / unit price) and offer price "
                "for a specific Alfalah mutual fund. Use when the user asks about current price, "
                "NAV, unit price, or fund prices."
            ),
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
            "description": (
                "Fetches performance returns (monthly return, return since inception, 1Y/3Y/5Y annualised) "
                "for a specific Alfalah mutual fund. Use when the user asks about fund returns, "
                "historical performance, or how a fund has performed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fund_name": {
                        "type": "string",
                        "description": "The full name of the fund.",
                    }
                },
                "required": ["fund_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_funds",
            "description": (
                "Lists all Alfalah mutual funds, optionally filtered by risk level, investment horizon, "
                "investor goal, or Shariah compliance. Use when the user asks to 'show all funds', "
                "'list funds', or wants to browse available products."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "risk": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter by risk level.",
                    },
                    "horizon": {
                        "type": "string",
                        "enum": ["short", "short-medium", "medium", "long"],
                        "description": "Filter by investment horizon.",
                    },
                    "goal": {
                        "type": "string",
                        "enum": [
                            "income",
                            "parking",
                            "regular_income",
                            "capital_preservation",
                            "growth",
                            "wealth_building",
                            "retirement",
                        ],
                        "description": "Filter by investor goal.",
                    },
                    "shariah_only": {
                        "type": "boolean",
                        "description": "If true, return only Shariah-compliant funds.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_funds",
            "description": (
                "Recommends suitable Alfalah mutual funds based on the investor's goal, risk appetite, "
                "and investment horizon. Use when the user asks for fund recommendations, wants to invest "
                "by goal (e.g. monthly income, retirement), by risk appetite (low/medium/high), or by "
                "investment horizon (short/medium/long term)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "enum": [
                            "regular_income",
                            "income",
                            "parking",
                            "capital_preservation",
                            "growth",
                            "wealth_building",
                            "retirement",
                        ],
                        "description": (
                            "Investor goal. Use 'regular_income' for monthly income needs (bills, groceries, school fees). "
                            "Use 'retirement' for pension/long-term planning. Use 'growth' or 'wealth_building' for capital appreciation."
                        ),
                    },
                    "risk": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Risk appetite. 'low' = capital preservation, 'medium' = balanced, 'high' = equity growth.",
                    },
                    "horizon": {
                        "type": "string",
                        "enum": ["short", "short-medium", "medium", "long"],
                        "description": "Investment horizon. 'short' = < 1 year, 'long' = 5+ years.",
                    },
                    "shariah_only": {
                        "type": "boolean",
                        "description": "If true, only recommend Shariah-compliant (Islamic) funds.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "project_investment",
            "description": (
                "Calculates the projected future value of an investment in an Alfalah fund using compound growth. "
                "Use when the user asks 'if I invest PKR X in fund Y for N years, what will I get?' "
                "or 'calculate my returns' or 'how much will my investment grow?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fund_name": {
                        "type": "string",
                        "description": "The name of the Alfalah fund to project returns for.",
                    },
                    "principal_pkr": {
                        "type": "number",
                        "description": "The initial investment amount in PKR.",
                    },
                    "years": {
                        "type": "integer",
                        "description": "Number of years to project the investment forward.",
                    },
                    "annual_return_pct": {
                        "type": "number",
                        "description": "Optional override for the expected annual return %. If not provided, uses the fund's historical annualised return.",
                    },
                },
                "required": ["fund_name", "principal_pkr", "years"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_historical_value",
            "description": (
                "Calculates what a past investment would be worth today. "
                "Use when the user asks 'if I had invested PKR X in fund Y N years ago, what would it be worth now?' "
                "or 'what would my investment be worth if I invested in 2020?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fund_name": {
                        "type": "string",
                        "description": "The name of the Alfalah fund.",
                    },
                    "principal_pkr": {
                        "type": "number",
                        "description": "The original investment amount in PKR.",
                    },
                    "years_ago": {
                        "type": "integer",
                        "description": "How many years ago the hypothetical investment was made.",
                    },
                },
                "required": ["fund_name", "principal_pkr", "years_ago"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_kb",
            "description": (
                "Searches the internal knowledge base (fund prospectuses, FAQs, SECP regulations, policies) "
                "to answer factual questions. Use for policy, eligibility, account opening, fee structure, "
                "KYC, zakat, and customer service questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or search phrase.",
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
