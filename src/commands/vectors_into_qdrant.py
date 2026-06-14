import argparse
import json
from pathlib import Path

from tqdm import tqdm
from qdrant_client.models import PointStruct

from src.config.settings import settings
from src.database.qdrant_connection import qdrant_client
from src.logger.logger_service import logger_service
from src.services.qdrant_vector_service import QdrantVectorService

EMBEDDINGS_DIR = Path("data/embeddings")

def index_car_embeddings(car_id: int, batch_size: int = 100):
    """
    Reads embeddings from:
        data/embeddings/car_<car_id>_embeddings.json

    and inserts/upserts them into Qdrant.
    """

    file_path = (
        EMBEDDINGS_DIR / f"car_{car_id}_embeddings.json"
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {file_path}"
        )

    logger_service.log(
        f"Loading embeddings from {file_path}",
        "QdrantIndexer",
    )

    with file_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not records:
        logger_service.log(
            f"No embeddings found for car_id={car_id}",
            "QdrantIndexer",
        )
        return

    vector_service = QdrantVectorService()

    vector_service.create_collection_if_not_exists()

    points = []

    with tqdm(
        total=len(records),
        desc=f"Indexing car {car_id}",
        unit="chunk",
    ) as progress_bar:

        for record in records:
            embedding = record.get("embedding")

            if not embedding:
                progress_bar.update(1)
                continue

            payload = {
                "chunk_id": record["chunk_id"],
                "chunk_type": record["chunk_type"],
                "content": record["content"],
                **record.get("metadata", {}),
            }

            point = PointStruct(
                id=vector_service._generate_point_id(
                    record["chunk_id"]
                ),
                vector=embedding,
                payload=payload,
            )

            points.append(point)

            if len(points) >= batch_size:
                qdrant_client.upsert(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    points=points,
                    wait=True,
                )

                points.clear()

            progress_bar.update(1)

    if points:
        qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points,
            wait=True,
        )

    logger_service.log(
        f"Successfully indexed "
        f"{len(records)} chunks for car_id={car_id}",
        "QdrantIndexer",
    )

    print(
        f"Successfully indexed "
        f"{len(records)} chunks for car_id={car_id}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--car-id",
        type=int,
        required=True,
        help="Car ID to index",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Qdrant upsert batch size",
    )

    args = parser.parse_args()

    index_car_embeddings(
        car_id=args.car_id,
        batch_size=args.batch_size,
    )