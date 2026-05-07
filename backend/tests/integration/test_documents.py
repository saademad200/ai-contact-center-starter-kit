"""Integration tests for document upload and management endpoints."""

from unittest.mock import AsyncMock, patch


class TestDocumentUpload:
    def test_upload_pdf_to_rag_returns_202(self, client, make_table):
        """PDF upload to RAG destination is accepted and queued for background ingestion."""
        table = make_table()
        with (
            patch("app.routers.documents.get_table", return_value=table),
            patch("app.routers.documents.ingest_pdf", new_callable=AsyncMock, return_value=12),
        ):
            resp = client.post(
                "/api/v1/documents/upload",
                data={"destination": "rag", "fund_name": "Alfalah GHP Income Fund"},
                files={"file": ("prospectus.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["destination"] == "rag"
        assert body["status"] == "processing"
        assert "doc_id" in body

    def test_upload_non_pdf_to_rag_is_rejected(self, client, make_table):
        """Non-PDF files sent to the RAG destination are rejected with 400."""
        with patch("app.routers.documents.get_table", return_value=make_table()):
            resp = client.post(
                "/api/v1/documents/upload",
                data={"destination": "rag"},
                files={"file": ("notes.txt", b"some text content", "text/plain")},
            )

        assert resp.status_code == 400

    def test_upload_txt_to_finetune_uploads_to_s3(self, client, make_table):
        """Text file upload to finetune destination is sent to S3 and returns 202."""
        table = make_table()
        with (
            patch("app.routers.documents.get_table", return_value=table),
            patch(
                "app.routers.documents.upload_file",
                new_callable=AsyncMock,
                return_value="s3://alfalah-ai-training-data/raw/abc123/faqs.txt",
            ),
        ):
            resp = client.post(
                "/api/v1/documents/upload",
                data={"destination": "finetune"},
                files={"file": ("faqs.txt", b"Q: What is NAV?\nA: Net Asset Value.", "text/plain")},
            )

        assert resp.status_code == 202
        body = resp.json()
        assert body["destination"] == "finetune"
        assert body["status"] == "uploaded_to_s3"

    def test_upload_no_filename_rejected(self, client, make_table):
        """Requests with an empty filename are rejected (422 from multipart validation)."""
        with patch("app.routers.documents.get_table", return_value=make_table()):
            resp = client.post(
                "/api/v1/documents/upload",
                data={"destination": "rag"},
                files={"file": ("", b"", "application/octet-stream")},
            )

        assert resp.status_code == 422


class TestDocumentCRUD:
    def test_list_documents_empty(self, client, make_table):
        with patch("app.routers.documents.get_table", return_value=make_table()):
            resp = client.get("/api/v1/documents")

        assert resp.status_code == 200
        assert resp.json() == {"documents": []}

    def test_list_documents_returns_items(self, client, make_table):
        docs = [
            {"pk": "doc1", "sk": "DOC", "filename": "prospectus.pdf", "status": "ingested"},
            {"pk": "doc2", "sk": "DOC", "filename": "faqs.txt", "status": "uploaded_to_s3"},
        ]
        with patch("app.routers.documents.get_table", return_value=make_table(scan={"Items": docs})):
            resp = client.get("/api/v1/documents")

        assert resp.status_code == 200
        assert len(resp.json()["documents"]) == 2

    def test_get_document_found(self, client, make_table):
        doc = {"pk": "doc1", "sk": "DOC", "filename": "prospectus.pdf", "status": "ingested"}
        with patch("app.routers.documents.get_table", return_value=make_table(get_item={"Item": doc})):
            resp = client.get("/api/v1/documents/doc1")

        assert resp.status_code == 200
        assert resp.json()["filename"] == "prospectus.pdf"

    def test_get_document_not_found(self, client, make_table):
        with patch("app.routers.documents.get_table", return_value=make_table(get_item={})):
            resp = client.get("/api/v1/documents/nonexistent")

        assert resp.status_code == 404

    def test_delete_document(self, client, make_table):
        doc = {"pk": "doc1", "sk": "DOC", "status": "ingested"}
        with patch("app.routers.documents.get_table", return_value=make_table(get_item={"Item": doc})):
            resp = client.delete("/api/v1/documents/doc1")

        assert resp.status_code == 200
        assert "deleted" in resp.json()["message"]

    def test_delete_document_not_found(self, client, make_table):
        with patch("app.routers.documents.get_table", return_value=make_table(get_item={})):
            resp = client.delete("/api/v1/documents/nonexistent")

        assert resp.status_code == 404
