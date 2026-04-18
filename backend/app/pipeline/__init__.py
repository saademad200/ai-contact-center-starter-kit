# Pipelines — implement orchestrators from PROJECT_PLAN.md §8 + §9 (sequence diagrams)
# ingestion_pipeline.py → IngestionPipeline: S3 → parse → chunk → embed → ChromaDB → DynamoDB status
# rag_pipeline.py       → RAGPipeline: query → embed → search → LLM stream → RAGEvent generator
