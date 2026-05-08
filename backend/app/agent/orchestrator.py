"""
Agent Orchestrator
Main loop: receive message → call OpenAI with tools → handle tool calls → return response.
Model and system prompt are fetched dynamically from DynamoDB registries.
OpenAI client is wrapped by Langfuse for automatic tracing.
"""

import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import Any, cast

import boto3
import langfuse

from app.agent.system_prompt import SYSTEM_PROMPT
from app.agent.tool_registry import OPENAI_TOOLS, execute_tool
from app.core.dynamo import get_table

log = logging.getLogger(__name__)


def init_langfuse() -> None:
    """Explicitly initialise Langfuse SDK. Call this AFTER secrets are loaded."""
    pk = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    sk = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST") or "https://us.cloud.langfuse.com"
    if pk and sk:
        langfuse.Langfuse(public_key=pk, secret_key=sk, host=host)
        log.info("[Langfuse] Initialised — host: %s", host)
    else:
        log.warning(
            "[Langfuse] Skipped — LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not found. Traces will NOT be sent."
        )


def _get_client() -> Any:
    """Build a fresh Langfuse-wrapped AsyncOpenAI client.
    Re-importing AsyncOpenAI from langfuse.openai each call ensures it picks up
    the env vars that were set by Secrets Manager at startup.
    """
    from langfuse.openai import AsyncOpenAI as LFAsyncOpenAI  # noqa: PLC0415

    return LFAsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


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
        log.warning("[Orchestrator] DynamoDB model lookup failed, using default: %s", e)
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
        log.warning("[Orchestrator] DynamoDB prompt lookup failed, using default: %s", e)

    return SYSTEM_PROMPT  # noqa: F821


async def chat_with_agent(
    conversation_history: list[dict[str, str]],
    user_message: str,
    conversation_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Main agent loop — async generator that yields text chunks.
    - Tool-call detection (first LLM call) is non-streaming.
    - Tool hint tokens yielded immediately so the widget shows a thinking indicator.
    - Synthesis (second) call uses stream=True so tokens appear word-by-word.
    - Direct answers (no tool calls) are yielded as a single chunk.
    """
    system_prompt = await get_system_prompt()
    model = await get_active_model()
    cid = conversation_id or "no-conv-id"

    log.info("[Orchestrator] Request — model=%s conv=%s history_len=%d", model, cid, len(conversation_history))

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    try:
        t0 = time.perf_counter()
        # First LLM call — non-streaming so we can inspect for tool calls
        response = await _get_client().chat.completions.create(
            model=model,
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            temperature=0.3,
            metadata={"conversation_id": conversation_id} if conversation_id else {},
        )
        llm_ms = int((time.perf_counter() - t0) * 1000)

        response_message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason
        log.info(
            "[Orchestrator] LLM call 1 — finish_reason=%s tool_calls=%d latency=%dms",
            finish_reason,
            len(response_message.tool_calls or []),
            llm_ms,
        )

        # ── Tool handling ─────────────────────────────────────────────────────
        if response_message.tool_calls:
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments
                log.info("[Orchestrator] ⚙ Tool call — name=%s args=%s conv=%s", tool_name, tool_args[:120], cid)
                # Yield hint so widget shows tool indicator immediately
                yield f"[TOOL:{tool_name}]"

                t_tool = time.perf_counter()
                tool_result = await execute_tool(tool_name=tool_name, arguments=tool_args)
                tool_ms = int((time.perf_counter() - t_tool) * 1000)
                log.info(
                    "[Orchestrator] ✓ Tool result — name=%s result_len=%d latency=%dms",
                    tool_name,
                    len(tool_result),
                    tool_ms,
                )
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "name": tool_name, "content": tool_result}
                )

            # Second call — stream the synthesis answer token-by-token
            t1 = time.perf_counter()
            stream = await _get_client().chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
            log.info(
                "[Orchestrator] LLM call 2 (synthesis streamed) — latency=%dms", int((time.perf_counter() - t1) * 1000)
            )

        else:
            # No tool calls — direct answer, yield as single chunk
            yield response_message.content or ""

    except Exception as e:
        log.error("[Orchestrator] Error — %s conv=%s", e, cid)
        yield "I'm sorry, I encountered an error processing your request. Please try again."
