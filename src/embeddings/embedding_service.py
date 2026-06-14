from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={
                "device": "mps",
            },
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8,
            },
        )

    def embed_query(self, text: str) -> list[float]:
        return self.embeddings.embed_query(text)

    def embed_documents(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return self.embeddings.embed_documents(texts)

    def embed_documents_in_batches(
        self,
        texts: list[str],
        batch_size: int = 8,
    ):
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            yield self.embeddings.embed_documents(batch)
