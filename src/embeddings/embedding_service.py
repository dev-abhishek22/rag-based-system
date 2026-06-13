from langchain_huggingface import HuggingFaceEmbeddings


class EmbeddingService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={
                "device": "cpu",
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