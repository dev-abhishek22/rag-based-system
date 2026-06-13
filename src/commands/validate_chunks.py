import argparse
import json
from pathlib import Path

from src.validators.chunk_validator import validate_chunks, get_chunk_stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to chunks JSON file")

    args = parser.parse_args()

    chunk_file = Path(args.file)

    if not chunk_file.exists():
        print(f"File not found: {chunk_file}")
        return

    chunks = json.loads(chunk_file.read_text(encoding="utf-8"))

    stats = get_chunk_stats(chunks)
    issues = validate_chunks(chunks)

    print("=" * 100)
    print("CHUNK STATS")
    print("=" * 100)

    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Min size: {stats['min_size']}")
    print(f"Max size: {stats['max_size']}")
    print(f"Avg size: {stats['avg_size']}")

    print("\nChunk types:")
    for chunk_type, count in stats["chunk_types"].items():
        print(f"  {chunk_type}: {count}")

    print("\n" + "=" * 100)
    print("CHUNK ISSUES")
    print("=" * 100)

    if not issues:
        print("No issues found.")
        return

    print(f"Issue chunks: {len(issues)}")

    for issue in issues:
        print("\n" + "-" * 100)
        print(f"Chunk #{issue['index']}")
        print(f"ID: {issue['chunk_id']}")
        print(f"Type: {issue['chunk_type']}")

        print("Issues:")
        for item in issue["issues"]:
            print(f"  - {item}")

        print("Preview:")
        print(issue["preview"])


if __name__ == "__main__":
    main()