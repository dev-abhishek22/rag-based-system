import re
from collections import Counter
from typing import Optional


MIN_CHARS = 120
MAX_CHARS = 2500

REQUIRED_TOP_LEVEL_FIELDS = [
    "chunk_id",
    "chunk_type",
    "content",
    "metadata",
]

REQUIRED_METADATA_FIELDS = [
    "car_id",
    "car_name",
    "brand_name",
    "model_name",
]


def has_html(text: str) -> bool:
    return bool(re.search(r"<[^>]+>", text or ""))


def validate_chunk(chunk: dict, index: int) -> Optional[dict]:
    issues = []

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in chunk:
            issues.append(f"Missing top-level field: {field}")

    content = chunk.get("content") or ""
    metadata = chunk.get("metadata") or {}

    if not content.strip():
        issues.append("Empty content")

    if len(content) < MIN_CHARS:
        issues.append(f"Too short: {len(content)} chars")

    if len(content) > MAX_CHARS:
        issues.append(f"Too large: {len(content)} chars")

    if has_html(content):
        issues.append("HTML detected")

    if "None" in content or "null" in content:
        issues.append("Possible null text found")

    for field in REQUIRED_METADATA_FIELDS:
        if not metadata.get(field):
            issues.append(f"Missing metadata: {field}")

    if not issues:
        return None

    return {
        "index": index,
        "chunk_id": chunk.get("chunk_id"),
        "chunk_type": chunk.get("chunk_type"),
        "issues": issues,
        "preview": content[:300],
    }


def validate_chunks(chunks: list[dict]) -> Optional[dict]:
    results = []

    for index, chunk in enumerate(chunks, start=1):
        issue = validate_chunk(chunk, index)

        if issue:
            results.append(issue)

    return results


def get_chunk_stats(chunks: list[dict]) -> dict:
    sizes = [len(chunk.get("content") or "") for chunk in chunks]
    chunk_types = Counter(chunk.get("chunk_type") for chunk in chunks)

    return {
        "total_chunks": len(chunks),
        "chunk_types": dict(chunk_types),
        "min_size": min(sizes) if sizes else 0,
        "max_size": max(sizes) if sizes else 0,
        "avg_size": round(sum(sizes) / len(sizes), 2) if sizes else 0,
    }