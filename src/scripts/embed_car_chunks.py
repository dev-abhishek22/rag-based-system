import argparse
from tqdm import tqdm

from src.embeddings.embedding_service import EmbeddingService
from src.utils.save_files import load_json, save_embeddings


def build_embeddings_for_car(car_id: int):
    print(f"\nLoading chunks for car_id={car_id}...")

    chunks = load_json(
        filename=f"car_{car_id}_chunks.json",
        folder="chunks",
    )

    print("Loading embedding model...")
    embedding_service = EmbeddingService()

    texts = [chunk["content"] for chunk in chunks if chunk.get("content")]

    print(f"Generating embeddings for {len(texts)} chunks...")

    vectors = embedding_service.embed_documents(texts)

    embedded_chunks = []
    vector_index = 0

    with tqdm(
        total=len(texts),
        desc=f"Processing car_id={car_id}",
        unit="chunk",
    ) as pbar:

        for chunk in chunks:
            content = chunk.get("content")

            if not content:
                continue

            embedding = vectors[vector_index]
            vector_index += 1

            embedded_chunks.append({
                **chunk,
                "embedding_dimension": len(embedding),
                "embedding": embedding,
            })

            pbar.update(1)

    filepath = save_embeddings(
        embeddings=embedded_chunks,
        car_id=car_id,
    )

    print("\n" + "=" * 80)
    print(f"Embeddings saved for car_id={car_id}")
    print(f"Total chunks embedded: {len(embedded_chunks)}")

    if embedded_chunks:
        print(
            f"Embedding dimension: "
            f"{embedded_chunks[0]['embedding_dimension']}"
        )

    print(f"Saved at: {filepath}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--car-id", type=int, required=True)

    args = parser.parse_args()

    build_embeddings_for_car(args.car_id)


if __name__ == "__main__":
    main()