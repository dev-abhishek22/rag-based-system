import argparse
import json
from tqdm import tqdm

from src.database.connection import SessionLocal
from src.services.car_etl_service import CarEtlService
from src.chunkers.car_chunker import format_car_chunks
from src.utils.save_files import save_payload, save_chunks


def build_docs_for_car(car_id: int):
    db = SessionLocal()
    service = CarEtlService()

    try:
        with tqdm(total=5, desc=f"Building docs for car_id={car_id}", unit="step") as pbar:
            payload = service.fetch_single_car_payload(db, car_id)
            pbar.update(1)

            if not payload:
                print(f"No car found for car_id={car_id}")
                return

            payload_file = save_payload(payload, car_id)
            pbar.update(1)

            docs = format_car_chunks(payload)
            pbar.update(1)

            chunks_file = save_chunks(docs, car_id)
            pbar.update(1)

            print("\n" + "=" * 100)
            print(f"Generated {len(docs)} docs/chunks for car_id={car_id}")
            print(f"Payload saved: {payload_file}")
            print(f"Chunks saved: {chunks_file}")
            print("=" * 100)

            # for index, doc in enumerate(docs, start=1):
            #     print(f"\n\nDOC #{index}")
            #     print("-" * 100)
            #     print("CHUNK TYPE:", doc["metadata"].get("chunk_type"))
            #     print("METADATA:")
            #     print(json.dumps(doc["metadata"], indent=2, default=str))
            #     print("\nTEXT:")
            #     print(doc["text"])

            pbar.update(1)

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Build RAG docs/chunks for a single car")
    parser.add_argument("car_id", type=int, help="Car ID to build docs for")

    args = parser.parse_args()
    build_docs_for_car(args.car_id)


if __name__ == "__main__":
    main()