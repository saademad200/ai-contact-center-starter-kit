"""Integration tests for ticket management endpoints."""

from unittest.mock import patch


class TestListTickets:
    def test_list_tickets_empty(self, client, make_table):
        with patch("app.routers.tickets.get_table", return_value=make_table()):
            resp = client.get("/api/v1/tickets")

        assert resp.status_code == 200
        assert resp.json() == {"tickets": []}

    def test_list_tickets_returns_items(self, client, make_table):
        tickets = [
            {"pk": "t1", "sk": "TICKET", "status": "open"},
            {"pk": "t2", "sk": "TICKET", "status": "resolved"},
        ]
        with patch("app.routers.tickets.get_table", return_value=make_table(scan={"Items": tickets})):
            resp = client.get("/api/v1/tickets")

        assert resp.status_code == 200
        assert len(resp.json()["tickets"]) == 2


class TestUpdateTicketStatus:
    def test_update_to_in_progress(self, client, make_table):
        ticket = {"pk": "t1", "sk": "TICKET", "status": "open"}
        with patch("app.routers.tickets.get_table", return_value=make_table(get_item={"Item": ticket})):
            resp = client.put("/api/v1/tickets/t1", json={"status": "in_progress"})

        assert resp.status_code == 200
        assert "t1" in resp.json()["message"]
        assert "in_progress" in resp.json()["message"]

    def test_update_to_resolved(self, client, make_table):
        ticket = {"pk": "t1", "sk": "TICKET", "status": "in_progress"}
        with patch("app.routers.tickets.get_table", return_value=make_table(get_item={"Item": ticket})):
            resp = client.put("/api/v1/tickets/t1", json={"status": "resolved"})

        assert resp.status_code == 200

    def test_update_invalid_status_rejected(self, client, make_table):
        """Status values outside the enum are rejected by pydantic validation."""
        with patch("app.routers.tickets.get_table", return_value=make_table()):
            resp = client.put("/api/v1/tickets/t1", json={"status": "invalid_status"})

        assert resp.status_code == 422

    def test_update_ticket_not_found(self, client, make_table):
        with patch("app.routers.tickets.get_table", return_value=make_table(get_item={})):
            resp = client.put("/api/v1/tickets/nonexistent", json={"status": "resolved"})

        assert resp.status_code == 404
