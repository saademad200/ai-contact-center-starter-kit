"""
AI Agent Orchestrator
======================
See PROJECT_PLAN.md §3 for full tool calling design.

Main loop:
1. Receive customer message + conversation history
2. Call Groq LLM with system prompt + tools schema
3. If LLM returns tool_call → execute tool → feed result back to LLM
4. If LLM returns text → stream response chunks via WebSocket
5. Log message + tool calls to DynamoDB

Supports multi-turn tool calling (LLM can call multiple tools in sequence).
"""
