# Services — implement class interfaces from PROJECT_PLAN.md §8
# embedding_service.py  → EmbeddingService (sentence-transformers/all-MiniLM-L6-v2)
# vector_service.py     → VectorService (ChromaDB)
# llm_service.py        → BaseLLMProvider, GroqProvider, HuggingFaceProvider
# document_processor.py → DocumentProcessor (PDF/DOCX/MD/TXT → List[Chunk])
# storage_service.py    → StorageService (S3 upload/download/presign)
