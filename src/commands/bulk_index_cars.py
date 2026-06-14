import argparse
import time

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from src.chunkers.car_chunker import format_car_chunks
from src.database.sql_connection import SessionLocal
from src.embeddings.embedding_service import EmbeddingService
from src.logger.logger_service import logger_service
from src.services.car_etl_service import CarEtlService
from src.services.qdrant_vector_service import QdrantVectorService

console = Console()


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
        chunk_id = doc.get("chunk_id") or f"car_{car_id}_{chunk_type}_{index}"

        metadata.pop("chunk_type", None)

        normalized.append(
            {
                "chunk_id": chunk_id,
                "chunk_type": chunk_type,
                "content": content.strip(),
                "metadata": metadata,
            }
        )

    return normalized


def run(
    batch_size: int,
    qdrant_batch_size: int,
    embedding_batch_size: int,
    start_after_car_id: int,
    limit: int | None,
    dry_run: bool = False,
):
    etl_service = CarEtlService()
    embedding_service = EmbeddingService()
    vector_service = QdrantVectorService()

    if not dry_run:
        vector_service.create_collection_if_not_exists()

    db = SessionLocal()
    try:
        total_active = etl_service.repository.count_active_cars(db)
    finally:
        db.close()

    total_target = min(limit, total_active) if limit else total_active

    total_indexed = 0
    total_skipped = 0
    total_failed = 0
    total_chunks = 0
    total_embeddings = 0
    started_at = time.time()

    console.print(
        f"\n[bold cyan]Car RAG Bulk Indexing[/bold cyan] "
        f"[yellow]dry_run={dry_run}[/yellow]\n"
    )

    car_progress = Progress(
        SpinnerColumn(style="green"),
        TextColumn("[bold green]{task.description}"),
        BarColumn(
            bar_width=None,
            complete_style="green",
            finished_style="bold green",
            pulse_style="green",
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    overall_progress = Progress(
        SpinnerColumn(style="#e63946"),
        TextColumn("[bold #e63946]{task.description}"),
        BarColumn(
            bar_width=None,
            complete_style="#e63946",
            finished_style="bold #e63946",
            pulse_style="#e63946",
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    )

    group = Group(car_progress, overall_progress)

    with Live(group, console=console, refresh_per_second=10):
        car_progress.start()
        overall_progress.start()

        car_task = car_progress.add_task(
            "Current car waiting...",
            total=100,
        )

        overall_task = overall_progress.add_task(
            "Overall cars",
            total=total_target,
        )

        for item in etl_service.fetch_all_active_car_payloads(
            batch_size=batch_size,
            start_after_car_id=start_after_car_id,
            limit=limit,
        ):
            car_id = item["car_id"]
            payload = item["payload"]

            raw_chunks = None
            chunks = None
            texts = None
            embeddings = []

            try:
                car_progress.reset(
                    car_task,
                    total=100,
                    completed=0,
                    description=f"Car {car_id}: payload ready",
                )

                car_progress.update(car_task, completed=10)

                raw_chunks = format_car_chunks(payload)
                chunks = normalize_chunks(raw_chunks)

                if not chunks:
                    total_skipped += 1
                    car_progress.update(
                        car_task,
                        completed=100,
                        description=f"Car {car_id}: skipped",
                    )
                    overall_progress.advance(overall_task)
                    continue

                car_progress.update(
                    car_task,
                    completed=20,
                    description=f"Car {car_id}: chunks={len(chunks)}",
                )

                texts = [chunk["content"] for chunk in chunks]
                total_texts = len(texts)
                embedded_count = 0

                for batch_vectors in embedding_service.embed_documents_in_batches(
                    texts=texts,
                    batch_size=embedding_batch_size,
                ):
                    embeddings.extend(batch_vectors)
                    embedded_count += len(batch_vectors)

                    percent = 20 + int((embedded_count / total_texts) * 60)

                    car_progress.update(
                        car_task,
                        completed=percent,
                        description=(
                            f"Car {car_id}: embedding "
                            f"{embedded_count}/{total_texts}"
                        ),
                    )

                if len(chunks) != len(embeddings):
                    raise ValueError(
                        f"chunks and embeddings mismatch: "
                        f"chunks={len(chunks)}, embeddings={len(embeddings)}"
                    )

                if dry_run:
                    car_progress.update(
                        car_task,
                        completed=100,
                        description=(
                            f"Car {car_id}: dry-run done " f"vectors={len(embeddings)}"
                        ),
                    )
                else:
                    car_progress.update(
                        car_task,
                        completed=85,
                        description=f"Car {car_id}: uploading to Qdrant",
                    )

                    vector_service.upsert_embeddings(
                        chunks=chunks,
                        embeddings=embeddings,
                        batch_size=qdrant_batch_size,
                    )

                    car_progress.update(
                        car_task,
                        completed=100,
                        description=f"Car {car_id}: indexed",
                    )

                total_indexed += 1
                total_chunks += len(chunks)
                total_embeddings += len(embeddings)

            except Exception as error:
                total_failed += 1
                logger_service.error(
                    f"Failed to index car_id={car_id}",
                    str(error),
                    "BulkIndexer",
                )
                car_progress.update(
                    car_task,
                    completed=100,
                    description=f"Car {car_id}: failed",
                )

            finally:
                payload = None
                raw_chunks = None
                chunks = None
                texts = None
                embeddings = None

                overall_progress.advance(overall_task)
                overall_progress.update(
                    overall_task,
                    description=(
                        f"Overall cars "
                        f"[indexed={total_indexed} "
                        f"failed={total_failed} "
                        f"skipped={total_skipped}]"
                    ),
                )

        car_progress.stop()
        overall_progress.stop()

    elapsed = time.time() - started_at

    table = Table(title="Bulk Indexing Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Cars Indexed", str(total_indexed))
    table.add_row("Cars Skipped", str(total_skipped))
    table.add_row("Cars Failed", str(total_failed))
    table.add_row("Chunks Generated", str(total_chunks))
    table.add_row("Embeddings Generated", str(total_embeddings))
    table.add_row("Dry Run", str(dry_run))
    table.add_row("Elapsed", f"{elapsed:.1f}s")

    console.print()
    console.print(table)

    logger_service.log(
        (
            f"Bulk indexing complete — indexed={total_indexed}, "
            f"skipped={total_skipped}, failed={total_failed}, "
            f"chunks={total_chunks}, embeddings={total_embeddings}, "
            f"dry_run={dry_run}, elapsed={elapsed:.1f}s"
        ),
        "BulkIndexer",
    )


def main():
    parser = argparse.ArgumentParser(description="Index all active cars into Qdrant")

    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--qdrant-batch-size", type=int, default=100)
    parser.add_argument("--embedding-batch-size", type=int, default=8)
    parser.add_argument("--start-after-car-id", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    run(
        batch_size=args.batch_size,
        qdrant_batch_size=args.qdrant_batch_size,
        embedding_batch_size=args.embedding_batch_size,
        start_after_car_id=args.start_after_car_id,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
