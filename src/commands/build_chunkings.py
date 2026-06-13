import argparse
from tqdm import tqdm

from src.database.connection import SessionLocal
from src.services.car_etl_service import CarEtlService
from src.chunkers.car_chunker import format_car_chunks
from src.utils.save_files import save_payload, save_chunks


def normalize_chunks(docs: list[dict]) -> list[dict]:
    normalized_docs = []

    for index, doc in enumerate(docs, start=1):
        metadata = doc.get("metadata") or {}

        content = doc.get("content") or doc.get("text") or ""
        chunk_type = doc.get("chunk_type") or metadata.get("chunk_type")

        if not content or not content.strip():
            continue

        if not chunk_type:
            continue

        car_id = metadata.get("car_id")
        chunk_id = doc.get("chunk_id") or f"car_{car_id}_{chunk_type}_{index}"

        metadata.pop("chunk_type", None)

        normalized_docs.append({
            "chunk_id": chunk_id,
            "chunk_type": chunk_type,
            "content": content.strip(),
            "metadata": metadata,
        })

    return normalized_docs


def build_docs_for_car(car_id: int):
    db = SessionLocal()
    service = CarEtlService()

    try:
        with tqdm(
            total=5,
            desc=f"Building car_id={car_id}",
            unit="step",
            dynamic_ncols=True,
            leave=True,
        ) as pbar:
            pbar.set_postfix_str("Fetching payload")
            payload = service.fetch_single_car_payload(db, car_id)
            pbar.update(1)

            if not payload:
                tqdm.write(f"No car found for car_id={car_id}")
                return

            pbar.set_postfix_str("Saving payload")
            payload_file = save_payload(payload, car_id)
            pbar.update(1)

            pbar.set_postfix_str("Generating chunks")
            raw_docs = format_car_chunks(payload)
            docs = normalize_chunks(raw_docs)
            pbar.update(1)

            pbar.set_postfix_str("Saving chunks")
            chunks_file = save_chunks(docs, car_id)
            pbar.update(1)

            pbar.set_postfix_str("Done")
            pbar.update(1)

        tqdm.write("\n" + "=" * 100)
        tqdm.write(f"Generated {len(docs)} docs/chunks for car_id={car_id}")
        tqdm.write(f"Payload saved: {payload_file}")
        tqdm.write(f"Chunks saved: {chunks_file}")
        tqdm.write("=" * 100)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Build RAG docs/chunks for a single car")
    parser.add_argument("car_id", type=int, help="Car ID to build docs for")

    args = parser.parse_args()
    build_docs_for_car(args.car_id)


if __name__ == "__main__":
    main()