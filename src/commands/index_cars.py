"""
src/commands/index_cars.py
──────────────────────────
CLI command that indexes all active cars into Qdrant.

Pipeline per car (no file I/O at any stage):
    fetch → clean → chunk → validate → embed → upsert

Progress display:
    - Outer bar  : total cars (based on count_active_cars())
    - Inner bar  : 7 steps for the current car

Usage examples
──────────────
# Full run
python -m src.commands.index_cars

# Test with 5 cars only
python -m src.commands.index_cars --limit 5

# Resume after a crash
python -m src.commands.index_cars --start-after-car-id 1360

# Dry run (no Qdrant writes)
python -m src.commands.index_cars --dry-run --limit 10

# Combine
python -m src.commands.index_cars --limit 50 --start-after-car-id 200 --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from tqdm import tqdm

from src.database.sql_connection import SessionLocal
from src.logger.logger_service import logger_service
from src.pipelines.car_index_pipeline import CarIndexPipeline
from src.repositories.car_etl_repository import CarEtlRepository
from src.services.qdrant_vector_service import QdrantVectorService


# ── Constants ──────────────────────────────────────────────────────────────

PIPELINE_STEPS = 7          # number of yields in CarIndexPipeline.process_car()
BATCH_SIZE     = 50         # how many car IDs to fetch from DB per SQL query


# ── Helpers ────────────────────────────────────────────────────────────────

def _count_total(start_after_car_id: int, limit: Optional[int]) -> int:
    """
    Returns the number of cars that will be processed so the outer
    progress bar can show a realistic total.
    """
    db = SessionLocal()
    try:
        repo = CarEtlRepository()
        total_active = repo.count_active_cars(db)

        # We only know approximately how many are after start_after_car_id,
        # but count_active_cars() counts all.  For the progress bar we use
        # the full count and let tqdm handle the slight inaccuracy.
        total = total_active
        if limit is not None:
            total = min(total, limit)
        return total
    finally:
        db.close()


def _ensure_collection() -> None:
    """Create the Qdrant collection once before the main loop."""
    svc = QdrantVectorService()
    svc.create_collection_if_not_exists()


def _print_summary(
    total_ok: int,
    total_skipped: int,
    failed_cars: list[dict],
    elapsed: float,
    dry_run: bool,
) -> None:
    mode = "[DRY RUN] " if dry_run else ""
    tqdm.write("\n" + "=" * 80)
    tqdm.write(f"{mode}Indexing complete in {elapsed:.1f}s")
    tqdm.write(f"  ✓  Indexed  : {total_ok}")
    tqdm.write(f"  -  Skipped  : {total_skipped}")
    tqdm.write(f"  ✗  Failed   : {len(failed_cars)}")

    if failed_cars:
        tqdm.write("\nFailed cars:")
        for entry in failed_cars:
            tqdm.write(f"  car_id={entry['car_id']:>6}  reason: {entry['reason']}")

    tqdm.write("=" * 80)


# ── Main logic ─────────────────────────────────────────────────────────────

def run_indexing(
    start_after_car_id: int = 0,
    limit: Optional[int] = None,
    batch_size: int = BATCH_SIZE,
    dry_run: bool = False,
) -> None:

    logger_service.log(
        f"Starting car indexing | start_after={start_after_car_id} | "
        f"limit={limit} | dry_run={dry_run}",
        "IndexCars",
    )

    # ── Pre-flight ──────────────────────────────
    total_estimate = _count_total(start_after_car_id, limit)

    if not dry_run:
        _ensure_collection()

    # ── Pipeline (shared across all cars so the embedding model loads once) ─
    pipeline = CarIndexPipeline(dry_run=dry_run)
    repo     = CarEtlRepository()

    # ── Counters ────────────────────────────────
    total_ok      = 0
    total_skipped = 0
    failed_cars: list[dict] = []   # fix #19 — collect {car_id, reason}
    last_car_id   = start_after_car_id
    total_processed = 0

    start_time = time.monotonic()

    # ── Outer progress bar (one tick per car) ───
    with tqdm(
        total=total_estimate,
        desc="Cars indexed",
        unit="car",
        dynamic_ncols=True,
        position=0,
        leave=True,
        colour="green",
    ) as outer_bar:

        while True:

            # ── Respect --limit ─────────────────
            if limit is not None and total_processed >= limit:
                break

            # ── Fetch next batch of car IDs ─────
            db = SessionLocal()
            try:
                remaining = None
                if limit is not None:
                    remaining = limit - total_processed

                current_batch = batch_size
                if remaining is not None:
                    current_batch = min(batch_size, remaining)

                car_ids = repo.get_active_car_ids_after_id(
                    db=db,
                    last_car_id=last_car_id,
                    limit=current_batch,
                )
            finally:
                db.close()

            if not car_ids:
                break   # no more cars

            # ── Process each car in the batch ───
            for car_id in car_ids:
                last_car_id = car_id

                outer_bar.set_description(f"Processing car_id={car_id}")

                # Inner bar — one tick per pipeline step
                with tqdm(
                    total=PIPELINE_STEPS,
                    desc=f"  car {car_id}",
                    unit="step",
                    dynamic_ncols=True,
                    position=1,
                    leave=False,
                    colour="cyan",
                ) as inner_bar:

                    db = SessionLocal()
                    try:
                        gen = pipeline.process_car(db, car_id)
                        result: dict = {"ok": False, "reason": "generator did not complete"}

                        try:
                            while True:
                                step_label = next(gen)
                                inner_bar.set_postfix_str(step_label)
                                inner_bar.update(1)

                        except StopIteration as stop:
                            result = stop.value or result

                    except Exception as exc:
                        # Unexpected error outside the generator
                        result = {"ok": False, "reason": f"unexpected: {exc}"}
                        logger_service.error(
                            f"car_id={car_id} unexpected pipeline error",
                            str(exc),
                            "IndexCars",
                        )
                    finally:
                        db.close()

                # ── Record outcome ───────────────
                if result.get("ok"):
                    total_ok += 1
                    chunks   = result.get("chunks", "?")
                    tqdm.write(
                        f"  ✓ car_id={car_id:<6}  chunks={chunks}"
                    )
                    logger_service.log(
                        f"car_id={car_id} indexed | chunks={chunks}",
                        "IndexCars",
                    )
                else:
                    reason = result.get("reason", "unknown")

                    # Distinguish "no data" (skip) from real errors
                    if "no data" in reason or "no car found" in reason.lower():
                        total_skipped += 1
                        tqdm.write(f"  - car_id={car_id:<6}  skipped ({reason})")
                    else:
                        failed_cars.append({"car_id": car_id, "reason": reason})
                        tqdm.write(f"  ✗ car_id={car_id:<6}  FAILED: {reason}")
                        logger_service.error(
                            f"car_id={car_id} failed",
                            reason,
                            "IndexCars",
                        )

                total_processed += 1
                outer_bar.update(1)

    # ── Final summary ───────────────────────────
    elapsed = time.monotonic() - start_time
    _print_summary(total_ok, total_skipped, failed_cars, elapsed, dry_run)


# ── CLI entry point ────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index all active cars into Qdrant (no file I/O).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--start-after-car-id",
        type=int,
        default=0,
        metavar="ID",
        help="Resume indexing after this car_id (cursor-based, fix #22)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after indexing N cars — useful for testing (fix #21)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        metavar="N",
        help="Number of car IDs to fetch from DB per SQL query",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Fetch, chunk, and embed but do NOT write to Qdrant (fix #20)",
    )

    args = parser.parse_args()

    try:
        run_indexing(
            start_after_car_id=args.start_after_car_id,
            limit=args.limit,
            batch_size=args.batch_size,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        tqdm.write("\n[interrupted] last processed car_id will be shown above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
