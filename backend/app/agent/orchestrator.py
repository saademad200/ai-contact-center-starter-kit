"""
Agent Orchestrator
Main loop: receive message → call OpenAI with tools → handle tool calls → return response.
Model and system prompt are fetched dynamically from DynamoDB registries.
OpenAI client is wrapped by Langfuse for automatic tracing.
"""

import os
from typing import Any, cast

import boto3
import langfuse
from langfuse.openai import AsyncOpenAI

from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tool_registry import OPENAI_TOOLS, execute_tool
from app.core.dynamo import get_table


def _init_langfuse() -> None:
    """Explicitly initialise Langfuse. Reads LANGFUSE_BASE_URL or LANGFUSE_HOST."""
    import logging

    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
    # Support both LANGFUSE_BASE_URL (.env convention) and LANGFUSE_HOST
    host = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST") or "https://cloud.langfuse.com"
    if pk and sk:
        langfuse.Langfuse(public_key=pk, secret_key=sk, host=host)
        logging.getLogger(__name__).info(f"[Langfuse] Initialised — host: {host}")
    else:
        logging.getLogger(__name__).warning(
            "[Langfuse] Skipped — LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not found in environment."
        )


_init_langfuse()


def _get_client() -> AsyncOpenAI:
    """Always build a fresh client so secrets loaded at startup are picked up."""
    return AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


_dynamodb: Any = None


def _get_dynamo() -> Any:
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
        table = get_table("model-registry")
        response = table.get_item(Key={"pk": "ACTIVE_MODEL", "sk": "ACTIVE_MODEL"})
        item = response.get("Item")
        if item and item.get("openai_model_id"):
            return cast(str, item["openai_model_id"])
    except Exception as e:
        print(f"[Orchestrator] DynamoDB model lookup failed, using default: {e}")
    return "gpt-4o-mini"


async def get_system_prompt() -> str:
    """Fetches the active system prompt version from DynamoDB Prompt Registry."""
    try:
        table = get_table("prompt-registry")
        response = table.get_item(Key={"pk": "ACTIVE_PROMPT", "sk": "ACTIVE_PROMPT"})
        item = response.get("Item")
        if item and item.get("content"):
            return cast(str, item["content"])
    except Exception as e:
        print(f"[Orchestrator] DynamoDB prompt lookup failed, using default: {e}")

    return SYSTEM_PROMPT  # noqa: F821


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
            return final_response.choices[0].message.content or ""

        return response_message.content or ""

    except Exception as e:
        print(f"[Orchestrator] Error: {e}")
        return "I'm sorry, I encountered an error processing your request. Please try again."
