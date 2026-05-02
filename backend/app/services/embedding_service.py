from sentence_transformers import SentenceTransformer
from typing import List

# Load the local model lazily to avoid heavy startup times if not needed immediately
_model = None

def get_model():
    global _model
    if _model is None:
        # 384-dimensional dense vectors
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

async def generate_embedding(text: str) -> List[float]:
    """
    Generates a 384-dimensional embedding for the given text.
    """
    model = get_model()
    # model.encode returns a numpy array, convert to list of floats for ChromaDB
    embedding = model.encode(text)
    return embedding.tolist()

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generates embeddings for a batch of texts.
    """
    model = get_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()
