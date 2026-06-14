from transformers.utils import logging
from langchain_huggingface import HuggingFaceEmbeddings

from src.config.settings import settings

logging.set_verbosity_error()

class EmbeddingService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={
                "device": "mps",
                "local_files_only": True,
            },
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8,
            },
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_documents_in_batches(
        self,
        texts: list[str],
        batch_size: int = 8,
    ):
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            yield self.embeddings.embed_documents(batch)


_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService()

    return _embedding_service
