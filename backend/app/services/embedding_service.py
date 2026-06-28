from typing import Any, cast

from sentence_transformers import SentenceTransformer

EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 output dimension
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_model: Any = None


def get_model() -> Any:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


async def generate_embedding(text: str) -> list[float]:
    """Generates a 384-dimensional embedding for the given text."""
    model = get_model()
    embedding = model.encode(text)
    return cast(list[float], embedding.tolist())


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generates embeddings for a batch of texts."""
    model = get_model()
    embeddings = model.encode(texts)
    return cast(list[list[float]], embeddings.tolist())
