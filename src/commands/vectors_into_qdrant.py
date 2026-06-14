import argparse
import json
from pathlib import Path

from tqdm import tqdm

from src.logger.logger_service import logger_service
from src.services.qdrant_vector_service import QdrantVectorService

EMBEDDINGS_DIR = Path("data/embeddings")


def index_car_embeddings(car_id: int, batch_size: int = 100):
    file_path = EMBEDDINGS_DIR / f"car_{car_id}_embeddings.json"

    if not file_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {file_path}")

    logger_service.log(f"Loading embeddings from {file_path}", "QdrantIndexer")

    with file_path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    if not records:
        logger_service.log(f"No embeddings found for car_id={car_id}", "QdrantIndexer")
        return

    chunks = []
    embeddings = []

    for record in records:
        if not record.get("embedding"):
            continue

        chunks.append(
            {
                "chunk_id": record["chunk_id"],
                "chunk_type": record["chunk_type"],
                "content": record["content"],
                "metadata": record.get("metadata", {}),
            }
        )
        embeddings.append(record["embedding"])

    vector_service = QdrantVectorService()

    with tqdm(total=len(chunks), desc=f"Indexing car {car_id}", unit="chunk") as pbar:
        for start in range(0, len(chunks), batch_size):
            end = min(start + batch_size, len(chunks))

            vector_service.upsert_embeddings(
                chunks=chunks[start:end],
                embeddings=embeddings[start:end],
                batch_size=end - start,
            )

            pbar.update(end - start)

    logger_service.log(
        f"Successfully indexed {len(chunks)} chunks for car_id={car_id}",
        "QdrantIndexer",
    )

    print(f"Successfully indexed {len(chunks)} chunks for car_id={car_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--car-id", type=int, required=True)
    parser.add_argument("--batch-size", type=int, default=100)

    args = parser.parse_args()

    index_car_embeddings(car_id=args.car_id, batch_size=args.batch_size)


if __name__ == "__main__":
    main()
