# Vector Store Backends

The application supports two vector store backends for RAG knowledge-base storage.
Both expose an identical async API so the rest of the application is agnostic to
the selected backend.

| Backend | When to use | Persistence |
|---------|-------------|-------------|
| **ChromaDB** (default) | Local development, single-node demos, quick start | On-disk (`./chroma_db`) |
| **pgvector** | Production, multi-node, teams that already run PostgreSQL | PostgreSQL table |

## Configuration

Set the backend via environment variables (or `.env`):

```bash
# --- ChromaDB (default) ---
VECTOR_STORE_TYPE=chromadb
# No other config required.

# --- pgvector ---
VECTOR_STORE_TYPE=pgvector
DATABASE_URL=postgresql://user:password@host:5432/dbname
PGVECTOR_DIMENSION=384   # must match embedding model output (all-MiniLM-L6-v2 = 384)
```

If `VECTOR_STORE_TYPE` is omitted it defaults to `chromadb` and the application
behaves exactly as before.

## PostgreSQL + pgvector setup

### 1. Run a pgvector-enabled PostgreSQL

Local example with Docker:

```bash
docker run -d --name pgvector \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 \
    pgvector/pgvector:pg16
```

On AWS, use **RDS for PostgreSQL** with the `vector` extension (available on
PostgreSQL 16+). Connect via `DATABASE_URL`.

### 2. Create the extension and table

The backend runs `CREATE EXTENSION IF NOT EXISTS vector` and creates the table
on startup automatically (`PgVectorStore.initialize()`). You can also apply the
schema manually:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE vector_store (
    id       TEXT PRIMARY KEY,
    content  TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384) NOT NULL,
    source   TEXT
);

CREATE INDEX vector_store_embedding_idx
    ON vector_store USING hnsw (embedding vector_cosine_ops);
CREATE INDEX vector_store_source_idx ON vector_store (source);
CREATE INDEX vector_store_metadata_idx
    ON vector_store USING GIN (metadata jsonb_path_ops);
```

### 3. Notes

- The table stores **pre-generated embeddings** from the embedding service — no
  embedding model runs inside PostgreSQL.
- `PGVECTOR_DIMENSION` must match the embedding model output dimension. The
  default `all-MiniLM-L6-v2` model produces 384-dimensional vectors.
- Cosine distance (`<=>`) is used for similarity search, matching ChromaDB's
  `hnsw:space: cosine` semantics.
- The `/api/v1/chroma` admin endpoints are ChromaDB-specific and return
  `NotImplementedError` when pgvector is selected.

## Running tests

### Unit tests (no database required)

```bash
cd backend
python -m pytest tests/unit/test_vector_store.py -v
```

### Integration tests (PostgreSQL + pgvector required)

```bash
docker run -d --name pgvector-test \
    -e POSTGRES_PASSWORD=postgres \
    -p 5432:5432 \
    pgvector/pgvector:pg16

export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
python -m pytest tests/integration/test_pgvector.py -v
```

The integration tests are marked `pgvector` and are skipped automatically when
no `DATABASE_URL` is set.
