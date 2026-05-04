"""
Agent Orchestrator
Main loop: receive message → call OpenAI with tools → handle tool calls → return response.
Model and system prompt are fetched dynamically from DynamoDB registries.
OpenAI client is wrapped by Langfuse for automatic tracing.
"""

import os
from typing import Any

import boto3
from langfuse.openai import AsyncOpenAI

from app.agent.tool_registry import OPENAI_TOOLS, execute_tool

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


_dynamodb = None


def _get_dynamo():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            endpoint_url=os.environ.get("DYNAMODB_ENDPOINT_URL"),  # None in prod
        )
    return _dynamodb


async def get_active_model() -> str:
    """Fetches the currently active fine-tuned model ID from DynamoDB Model Registry."""
    try:
        table = _get_dynamo().Table("alfalah-model-registry")
        response = table.get_item(Key={"pk": "ACTIVE_MODEL", "sk": "ACTIVE_MODEL"})
        item = response.get("Item")
        if item and item.get("openai_model_id"):
            return item["openai_model_id"]
    except Exception as e:
        print(f"[Orchestrator] DynamoDB model lookup failed, using default: {e}")
    return "gpt-4o-mini"


async def get_system_prompt() -> str:
    """Fetches the active system prompt version from DynamoDB Prompt Registry."""
    try:
        table = _get_dynamo().Table("alfalah-prompt-registry")
        response = table.get_item(Key={"pk": "ACTIVE_PROMPT", "sk": "ACTIVE_PROMPT"})
        item = response.get("Item")
        if item and item.get("content"):
            return item["content"]
    except Exception as e:
        print(f"[Orchestrator] DynamoDB prompt lookup failed, using default: {e}")

    return (
        "You are Alfalah GPT, a helpful and professional customer support AI for Alfalah Investments. "
        "You assist customers with questions about mutual funds, investments, and account management. "
        "Use the available tools to fetch live fund data when needed. "
        "Always add the disclaimer 'Past performance is not indicative of future results.' when discussing fund performance. "
        "Be concise, accurate, and professional at all times."
    )


async def chat_with_agent(
    conversation_history: list[dict[str, str]],
    user_message: str,
    conversation_id: str | None = None,
) -> str:
    """
    Main agent loop.
    - Prepends system prompt from DynamoDB.
    - Sends history + user message to OpenAI (Langfuse traces this automatically).
    - Handles tool calls if triggered, then gets a final response.
    Returns the assistant reply as a string.
    """
    system_prompt = await get_system_prompt()
    model = await get_active_model()

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    try:
        # First LLM call — may include tool call requests
        response = await _get_client().chat.completions.create(
            model=model,
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            temperature=0.3,
            metadata={"conversation_id": conversation_id} if conversation_id else {},
        )

        response_message = response.choices[0].message

        # ── Tool handling loop ────────────────────────────────────────────────
        if response_message.tool_calls:
            messages.append(response_message)  # include assistant's tool call

            for tool_call in response_message.tool_calls:
                tool_result = await execute_tool(
                    tool_name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result,
                    }
                )

            # Second call — produce final answer using tool results
            final_response = await _get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
            )
            return final_response.choices[0].message.content

        return response_message.content

    except Exception as e:
        print(f"[Orchestrator] Error: {e}")
        return "I'm sorry, I encountered an error processing your request. Please try again."
