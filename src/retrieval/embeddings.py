from __future__ import annotations

from functools import lru_cache
import hashlib

from langchain_core.embeddings import Embeddings


def _text_to_hash_embedding(text: str, dim: int = 384) -> list[float]:
    """Create a simple deterministic embedding from text hash."""
    hash_obj = hashlib.sha256(text.lower().encode())
    hash_bytes = hash_obj.digest()

    embedding = []
    for i in range(dim):
        byte_idx = i % len(hash_bytes)
        val = hash_bytes[byte_idx] / 255.0 * 2 - 1
        embedding.append(float(val))

    norm = sum(x**2 for x in embedding) ** 0.5
    if norm > 0:
        embedding = [x / norm for x in embedding]

    return embedding


@lru_cache(maxsize=4)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(model_name)
    except Exception:
        return None


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = _load_model(model_name)
        self.model_name = model_name
        if self.model is None:
            print(f"[WARNING] Could not load {model_name}, using hash-based fallback embeddings")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self.model is not None:
            embeddings = self.model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        else:
            return [_text_to_hash_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.model is not None:
            embedding = self.model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        else:
            return _text_to_hash_embedding(text)
