"""
src/pipeline/car_index_pipeline.py

Orchestrates the full pipeline for a single car:
    fetch → clean → chunk → validate → embed → upsert into Qdrant

No files are saved at any stage.
All progress updates are returned as strings so the caller (command)
can forward them to tqdm or print them however it likes.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Generator

from src.chunkers.car_chunker import format_car_chunks
from src.config.settings import settings
from src.embeddings.embedding_service import EmbeddingService
from src.logger.logger_service import logger_service
from src.repositories.car_etl_repository import CarEtlRepository
from src.services.car_etl_service import CarEtlService
from src.services.qdrant_vector_service import QdrantVectorService


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _safe_value(v: Any) -> Any:
    """
    Convert values that Qdrant payload cannot handle into JSON-safe types.
    - datetime / date  → ISO string
    - Decimal          → float
    - None             → kept (Qdrant accepts null)
    - everything else  → as-is (str, int, float, bool, list, dict)
    """
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def _clean_payload(metadata: dict) -> dict:
    """Return a new dict with all values made Qdrant-safe."""
    return {k: _safe_value(v) for k, v in metadata.items() if v is not None}


def _normalize_chunks(docs: list[dict]) -> list[dict]:
    """
    Filter and normalise raw chunks produced by format_car_chunks().

    Fixes issue #7: copies metadata before mutating it.
    Fixes issue #8: chunk_id stable (relies on caller to pass good chunk_ids,
                    but at minimum we do not use bare index as fallback here —
                    we build a deterministic fallback from car_id + chunk_type
                    + a counter per chunk_type).
    """
    type_counters: dict[str, int] = {}
    normalized: list[dict] = []

    for doc in docs:
        # Safely copy metadata (fix #7 — no mutation of original)
        metadata = dict(doc.get("metadata") or {})

        content: str = (doc.get("content") or doc.get("text") or "").strip()
        chunk_type: str = doc.get("chunk_type") or metadata.get("chunk_type") or ""

        # Drop empty content or missing chunk_type
        if not content or not chunk_type:
            continue

        car_id = metadata.get("car_id", "unknown")

        # Build a stable chunk_id (fix #8)
        existing_id = doc.get("chunk_id")
        if existing_id:
            chunk_id = existing_id
        else:
            type_counters[chunk_type] = type_counters.get(chunk_type, 0) + 1
            chunk_id = f"car_{car_id}__{chunk_type}__{type_counters[chunk_type]}"

        # Remove chunk_type from metadata (it lives at top level)
        metadata.pop("chunk_type", None)

        normalized.append(
            {
                "chunk_id": chunk_id,
                "chunk_type": chunk_type,
                "content": content,
                "metadata": metadata,
            }
        )

    return normalized


def _validate_payload(payload: dict, car_id: int) -> str | None:
    """
    Returns an error string if the payload fails validation, else None.
    Fixes issue #5.
    """
    car = payload.get("car") or {}

    if not car:
        return f"car_id={car_id}: payload has no 'car' key"
    if not car.get("car_id"):
        return f"car_id={car_id}: missing car_id in car dict"
    if not car.get("car_name"):
        return f"car_id={car_id}: missing car_name"
    if not car.get("brand_name"):
        return f"car_id={car_id}: missing brand_name"
    if not car.get("model_name"):
        return f"car_id={car_id}: missing model_name"

    return None


def _validate_chunks(chunks: list[dict], car_id: int) -> str | None:
    """
    Stricter chunk validation before embedding.
    Fixes issue #6.
    """
    if not chunks:
        return f"car_id={car_id}: produced 0 valid chunks after normalisation"

    for i, chunk in enumerate(chunks):
        if not chunk.get("chunk_id"):
            return f"car_id={car_id}: chunk[{i}] missing chunk_id"
        if not chunk.get("chunk_type"):
            return f"car_id={car_id}: chunk[{i}] missing chunk_type"
        if not chunk.get("content", "").strip():
            return f"car_id={car_id}: chunk[{i}] has empty content"

    return None


# ──────────────────────────────────────────────
# Pipeline steps (each returns the next artefact)
# ──────────────────────────────────────────────

class CarIndexPipeline:
    """
    Stateless pipeline. Instantiate once, call process_car() for each car.
    Embedding model and Qdrant service are initialised lazily on first call
    so the CLI can show the progress bar before the slow model load.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self._etl_service = CarEtlService()
        self._embedding_service: EmbeddingService | None = None
        self._vector_service: QdrantVectorService | None = None

    # ── lazy initialisers ──────────────────────

    def _get_embedding_service(self) -> EmbeddingService:
        if self._embedding_service is None:
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    def _get_vector_service(self) -> QdrantVectorService:
        if self._vector_service is None:
            self._vector_service = QdrantVectorService()
        return self._vector_service

    # ── public entry point ────────────────────

    def process_car(
        self,
        db,
        car_id: int,
    ) -> Generator[str, None, dict]:
        """
        Generator that yields step labels as it progresses so the caller can
        update a progress bar.  Finally returns a result dict via StopIteration.

        Usage:
            gen = pipeline.process_car(db, car_id)
            try:
                while True:
                    label = next(gen)
                    pbar.set_postfix_str(label)
                    pbar.update(1)
            except StopIteration as e:
                result = e.value   # {"ok": True} or {"ok": False, "reason": "..."}

        Steps (7 total — caller should set tqdm total=7):
            1. fetch
            2. validate payload
            3. chunk
            4. validate chunks
            5. embed
            6. upsert   (skipped in dry_run)
            7. done
        """
        result: dict = {"ok": False, "reason": "unknown"}

        # ── Step 1: Fetch & clean ──────────────
        yield "fetching"
        try:
            payload = self._etl_service.fetch_single_car_payload(db, car_id)
        except Exception as exc:
            result["reason"] = f"fetch error: {exc}"
            logger_service.error(f"car_id={car_id} fetch failed", str(exc), "Pipeline")
            return result

        if not payload:
            result["reason"] = "no data returned from DB"
            return result

        # ── Step 2: Validate payload ───────────
        yield "validating payload"
        err = _validate_payload(payload, car_id)
        if err:
            result["reason"] = err
            return result

        # ── Step 3: Chunk ──────────────────────
        yield "chunking"
        try:
            raw_chunks = format_car_chunks(payload)
            chunks = _normalize_chunks(raw_chunks)
        except Exception as exc:
            result["reason"] = f"chunking error: {exc}"
            logger_service.error(f"car_id={car_id} chunking failed", str(exc), "Pipeline")
            return result

        # ── Step 4: Validate chunks ────────────
        yield "validating chunks"
        err = _validate_chunks(chunks, car_id)
        if err:
            result["reason"] = err
            return result

        # ── Step 5: Embed ──────────────────────
        yield "embedding"
        texts = [c["content"] for c in chunks]

        try:
            vectors = self._EmbeddingService().embed_documents(texts)
        except Exception as exc:
            result["reason"] = f"embedding error: {exc}"
            logger_service.error(f"car_id={car_id} embedding failed", str(exc), "Pipeline")
            return result

        # Fix #23: validate embedding count matches chunk count
        if len(vectors) != len(chunks):
            result["reason"] = (
                f"embedding count mismatch: got {len(vectors)} vectors "
                f"for {len(chunks)} chunks"
            )
            return result

        # Fix #14: validate embedding dimension
        if vectors and len(vectors[0]) != settings.QDRANT_VECTOR_SIZE:
            result["reason"] = (
                f"embedding dimension {len(vectors[0])} != "
                f"expected {settings.QDRANT_VECTOR_SIZE}"
            )
            return result

        # ── Step 6: Upsert ────────────────────
        yield "upserting"
        if self.dry_run:
            logger_service.log(
                f"[dry-run] car_id={car_id}: would upsert {len(chunks)} chunks",
                "Pipeline",
            )
        else:
            vector_service = self._get_vector_service()

            # Fix #18: delete stale vectors for this car before re-indexing
            try:
                vector_service.delete_points_by_car_id(car_id)
            except Exception as exc:
                # Non-fatal — log and continue; collection may be empty
                logger_service.warn(
                    f"car_id={car_id}: delete_points_by_car_id failed ({exc}), continuing",
                    "Pipeline",
                )

            # Clean metadata before upsert (fix #13)
            clean_chunks = []
            for chunk in chunks:
                clean_chunks.append(
                    {
                        **chunk,
                        "metadata": _clean_payload(chunk.get("metadata") or {}),
                    }
                )

            try:
                vector_service.upsert_embeddings(
                    chunks=clean_chunks,
                    embeddings=vectors,
                    # batch_size comes from settings so it is configurable (fix #15)
                    batch_size=getattr(settings, "QDRANT_UPSERT_BATCH_SIZE", 100),
                )
            except Exception as exc:
                result["reason"] = f"qdrant upsert error: {exc}"
                logger_service.error(f"car_id={car_id} upsert failed", str(exc), "Pipeline")
                return result

        # ── Step 7: Done ──────────────────────
        yield "done"
        result = {"ok": True, "chunks": len(chunks), "vectors": len(vectors)}
        return result
