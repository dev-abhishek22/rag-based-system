from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

from src.config.settings import settings
from src.database.qdrant_connection import qdrant_client
from src.logger.logger_service import logger_service

DISTANCE_MAP = {
    "cosine": Distance.COSINE,
    "euclid": Distance.EUCLID,
    "dot": Distance.DOT,
    "manhattan": Distance.MANHATTAN,
}


class QdrantVectorService:
    def __init__(self):
        self.client = qdrant_client
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    def create_collection_if_not_exists(self):
        """
        Creates the Qdrant collection if it does not already exist.
        """
        collections = self.client.get_collections().collections
        existing_collections = {
            collection.name
            for collection in collections
        }

        if self.collection_name in existing_collections:
            logger_service.log(
                f"Qdrant collection already exists: {self.collection_name}",
                "Qdrant",
            )
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=settings.QDRANT_VECTOR_SIZE,
                distance=DISTANCE_MAP[
                    settings.QDRANT_DISTANCE.lower()
                ],
            ),
        )

        logger_service.log(
            f"Qdrant collection created: {self.collection_name}",
            "Qdrant",
        )

    @staticmethod
    def _generate_point_id(chunk_id: str) -> str:
        """
        Generates a deterministic UUID from chunk_id.
        This allows upserts without duplicates.
        """
        return str(uuid5(NAMESPACE_DNS, chunk_id))

    def build_point(
        self,
        chunk: dict[str, Any],
        embedding: list[float],
    ) -> PointStruct:
        """
        Converts a chunk and embedding into a Qdrant point.
        """
        chunk_id = chunk["chunk_id"]

        payload = {
            "chunk_id": chunk_id,
            "chunk_type": chunk.get("chunk_type"),
            "content": chunk.get("content"),
            **chunk.get("metadata", {}),
        }

        return PointStruct(
            id=self._generate_point_id(chunk_id),
            vector=embedding,
            payload=payload,
        )

    def upsert_embeddings(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
        batch_size: int = 100,
    ):
        """
        Inserts or updates embeddings in Qdrant.
        """

        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks and embeddings must be the same."
            )

        self.create_collection_if_not_exists()

        total = len(chunks)

        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)

            batch_points = [
                self.build_point(chunk, embedding)
                for chunk, embedding in zip(
                    chunks[start:end],
                    embeddings[start:end],
                )
            ]

            self.client.upsert(
                collection_name=self.collection_name,
                points=batch_points,
                wait=True,
            )

            logger_service.log(
                f"Inserted {end}/{total} vectors into Qdrant",
                "Qdrant",
            )

        logger_service.log(
            f"Successfully inserted {total} vectors into "
            f"{self.collection_name}",
            "Qdrant",
        )