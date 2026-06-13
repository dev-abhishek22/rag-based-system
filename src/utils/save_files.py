import json
from pathlib import Path
from typing import Any


def save_json(
    data: Any,
    filename: str,
    folder: str,
    indent: int = 2,
) -> Path:
    """
    Save any JSON serializable object.

    Example:
        save_json(payload, "car_123.json", "payloads")
        save_json(chunks, "car_123_chunks.json", "chunks")
    """

    directory = Path("data") / folder
    directory.mkdir(parents=True, exist_ok=True)

    filepath = directory / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=indent,
            ensure_ascii=False,
            default=str,
        )

    return filepath


def load_json(filename: str, folder: str) -> Any:
    """
    Load JSON from disk.

    Example:
        payload = load_json("car_123.json", "payloads")
    """

    filepath = Path("data") / folder / filename

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_payload(payload: dict, car_id: int) -> Path:
    return save_json(
        data=payload,
        filename=f"car_{car_id}.json",
        folder="payloads",
    )


def save_chunks(chunks: list[dict], car_id: int) -> Path:
    return save_json(
        data=chunks,
        filename=f"car_{car_id}_chunks.json",
        folder="chunks",
    )


def save_embeddings(
    embeddings: list[dict],
    car_id: int,
) -> Path:
    return save_json(
        data=embeddings,
        filename=f"car_{car_id}_embeddings.json",
        folder="embeddings",
    )