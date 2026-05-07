"""Integration tests for WebSocket chat endpoint."""

from unittest.mock import AsyncMock, patch


class TestWebSocketChat:
    def test_connect_send_receive(self, client, make_table):
        """A message sent over WS returns the agent reply."""
        table = make_table(query={"Items": []})
        with (
            patch("app.routers.chat_ws.get_table", return_value=table),
            patch(
                "app.routers.chat_ws.chat_with_agent",
                new_callable=AsyncMock,
                return_value="Hello! How can I help?",
            ),
            client.websocket_connect("/ws/chat/conv-001") as ws,
        ):
            ws.send_text("What is the NAV?")
            reply = ws.receive_text()

        assert reply == "Hello! How can I help?"

    def test_empty_message_is_ignored(self, client, make_table):
        """Whitespace-only messages do not trigger the agent."""
        table = make_table(query={"Items": []})
        with (
            patch("app.routers.chat_ws.get_table", return_value=table),
            patch("app.routers.chat_ws.chat_with_agent", new_callable=AsyncMock) as mock_agent,
            client.websocket_connect("/ws/chat/conv-002") as ws,
        ):
            ws.send_text("   ")
            # close without sending a real message

        mock_agent.assert_not_called()

    def test_conversation_history_passed_to_agent(self, client, make_table):
        """Existing message history is loaded from DynamoDB and forwarded to the agent."""
        history_items = [
            {"pk": "conv-003", "sk": "2026-01-01T00:00:00#aaa", "role": "user", "content": "Hi"},
            {"pk": "conv-003", "sk": "2026-01-01T00:00:01#bbb", "role": "assistant", "content": "Hello"},
        ]
        table = make_table(query={"Items": history_items})
        with (
            patch("app.routers.chat_ws.get_table", return_value=table),
            patch(
                "app.routers.chat_ws.chat_with_agent",
                new_callable=AsyncMock,
                return_value="follow-up reply",
            ) as mock_agent,
            client.websocket_connect("/ws/chat/conv-003") as ws,
        ):
            ws.send_text("Follow-up question")
            ws.receive_text()

        passed_history = mock_agent.call_args.kwargs["conversation_history"]
        assert len(passed_history) == 2
        assert passed_history[0] == {"role": "user", "content": "Hi"}
        assert passed_history[1] == {"role": "assistant", "content": "Hello"}

    def test_agent_error_returns_fallback_message(self, client, make_table):
        """If the agent raises, the WS sends a graceful error message instead of crashing."""
        table = make_table(query={"Items": []})
        with (
            patch("app.routers.chat_ws.get_table", return_value=table),
            patch(
                "app.routers.chat_ws.chat_with_agent",
                new_callable=AsyncMock,
                side_effect=Exception("LLM unavailable"),
            ),
            client.websocket_connect("/ws/chat/conv-004") as ws,
        ):
            ws.send_text("Hello")
            reply = ws.receive_text()

        assert "error" in reply.lower()

    def test_messages_saved_to_dynamodb(self, client, make_table):
        """Both the user message and assistant reply are persisted via put_item."""
        table = make_table(query={"Items": []})
        with (
            patch("app.routers.chat_ws.get_table", return_value=table),
            patch(
                "app.routers.chat_ws.chat_with_agent",
                new_callable=AsyncMock,
                return_value="agent reply",
            ),
            client.websocket_connect("/ws/chat/conv-005") as ws,
        ):
            ws.send_text("Save this")
            ws.receive_text()

        # put_item called at least twice: once for user msg, once for assistant reply
        assert table.put_item.call_count >= 2
