import argparse
import time

from tqdm import tqdm

from src.chunkers.car_chunker import format_car_chunks
from src.database.sql_connection import SessionLocal
from src.embeddings.embedding_service import EmbeddingService
from src.logger.logger_service import logger_service
from src.services.car_etl_service import CarEtlService
from src.services.qdrant_vector_service import QdrantVectorService


def normalize_chunks(docs: list[dict]) -> list[dict]:
    normalized = []
    for index, doc in enumerate(docs, start=1):
        metadata = dict(doc.get("metadata") or {})
        content = doc.get("content") or doc.get("text") or ""
        chunk_type = doc.get("chunk_type") or metadata.get("chunk_type")

        if not content or not content.strip():
            continue

        if not chunk_type:
            continue

        car_id = metadata.get("car_id")
        chunk_id = f"car_{car_id}_{chunk_type}_{index}"
        metadata.pop("chunk_type", None)

        normalized.append({
            "chunk_id": chunk_id,
            "chunk_type": chunk_type,
            "content": content.strip(),
            "metadata": metadata,
        })

    return normalized


def run(
    batch_size: int,
    qdrant_batch_size: int,
    start_after_car_id: int,
    limit: int | None,
):
    etl_service = CarEtlService()
    embedding_service = EmbeddingService()
    vector_service = QdrantVectorService()

    vector_service.create_collection_if_not_exists()

    db = SessionLocal()
    try:
        total_active = etl_service.repository.count_active_cars(db)
    finally:
        db.close()

    logger_service.log(
        f"Bulk indexing started — total_active={total_active}, "
        f"start_after_car_id={start_after_car_id}, limit={limit}",
        "BulkIndexer",
    )

    total_indexed = 0
    total_skipped = 0
    total_failed = 0
    started_at = time.time()

    pbar = tqdm(
        total=min(limit, total_active) if limit else total_active,
        desc="Indexing cars",
        unit="car",
        dynamic_ncols=True,
        leave=True,
    )

    try:
        for item in etl_service.fetch_all_active_car_payloads(
            batch_size=batch_size,
            start_after_car_id=start_after_car_id,
            limit=limit,
        ):
            car_id = item["car_id"]
            payload = item["payload"]

            try:
                raw_chunks = format_car_chunks(payload)
                chunks = normalize_chunks(raw_chunks)

                if not chunks:
                    total_skipped += 1
                    tqdm.write(f"[SKIP] car_id={car_id}: no valid chunks produced")
                    pbar.update(1)
                    continue

                texts = [c["content"] for c in chunks]
                embeddings = embedding_service.embed_documents(texts)

                vector_service.upsert_embeddings(
                    chunks=chunks,
                    embeddings=embeddings,
                    batch_size=qdrant_batch_size,
                )

                total_indexed += 1
                logger_service.log(
                    f"Indexed car_id={car_id} with {len(chunks)} chunks",
                    "BulkIndexer",
                )

            except Exception as error:
                total_failed += 1
                logger_service.error(
                    f"Failed to index car_id={car_id}",
                    str(error),
                    "BulkIndexer",
                )
                tqdm.write(f"[FAIL] car_id={car_id}: {error}")

            pbar.update(1)
            pbar.set_postfix(
                indexed=total_indexed,
                failed=total_failed,
                skipped=total_skipped,
            )

    finally:
        pbar.close()

    elapsed = time.time() - started_at
    summary = (
        f"Bulk indexing complete — "
        f"indexed={total_indexed}, "
        f"skipped={total_skipped}, "
        f"failed={total_failed}, "
        f"elapsed={elapsed:.1f}s"
    )

    logger_service.log(summary, "BulkIndexer")

    print("\n" + "=" * 80)
    print(summary)
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Index all active cars into Qdrant")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--qdrant-batch-size", type=int, default=100)
    parser.add_argument("--start-after-car-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)

    args = parser.parse_args()

    run(
        batch_size=args.batch_size,
        qdrant_batch_size=args.qdrant_batch_size,
        start_after_car_id=args.start_after_car_id,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()