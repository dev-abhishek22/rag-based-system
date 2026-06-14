from typing import Any
from uuid import NAMESPACE_DNS, uuid5

from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    FieldCondition,
    Filter,
    MatchValue,
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
        existing_collections = {collection.name for collection in collections}

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
                distance=DISTANCE_MAP[settings.QDRANT_DISTANCE.lower()],
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
        chunks: list,
        embeddings: list,
        batch_size: int = 100,
    ):
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must be the same.")

        self.create_collection_if_not_exists()

        total = len(chunks)
        batches_done = 0

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

            batches_done += 1

        logger_service.log(
            f"Upserted {total} vectors into {self.collection_name} "
            f"({batches_done} batch(es))",
            "Qdrant",
        )

    def delete_points_by_car_id(self, car_id: int) -> int:
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="car_id",
                        match=MatchValue(value=car_id),
                    )
                ]
            ),
            wait=True,
        )

        deleted = getattr(result, "deleted", None)

        logger_service.log(
            f"Deleted existing vectors for car_id={car_id} "
            f"(count={deleted if deleted is not None else 'unknown'})",
            "Qdrant",
        )

        return deleted or 0
