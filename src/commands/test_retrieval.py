import argparse

from rich.console import Console
from rich.panel import Panel

from src.retrievers.qdrant_retriever import QdrantRetriever

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Test Qdrant retrieval")

    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()

    retriever = QdrantRetriever()

    results = retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        format_results=False,
    )

    console.print(
        Panel.fit(
            f"[bold]Query:[/bold] {args.query}\n"
            f"[bold]Top K:[/bold] {args.top_k}\n"
            f"[bold]Results:[/bold] {len(results)}",
            title="Retrieval Test",
            border_style="pink1",
        )
    )

    for index, point in enumerate(results, start=1):
        payload = point.payload or {}

        console.print("\n" + "=" * 100)
        console.print(f"[bold pink1]RESULT #{index}[/bold pink1]")
        console.print(f"[bold]Score:[/bold] {point.score}")
        console.print(f"[bold]Point ID:[/bold] {point.id}")

        console.print(f"[bold]Chunk ID:[/bold] {payload.get('chunk_id')}")
        console.print(f"[bold]Chunk Type:[/bold] {payload.get('chunk_type')}")

        console.print(f"[bold]Car:[/bold] {payload.get('car_name')}")
        console.print(f"[bold]Brand:[/bold] {payload.get('brand_name')}")
        console.print(f"[bold]Model:[/bold] {payload.get('model_name')}")
        console.print(f"[bold]Submodel:[/bold] {payload.get('submodel_name')}")
        console.print(f"[bold]URL:[/bold] {payload.get('url')}")

        console.print(f"[bold]Min Price:[/bold] {payload.get('min_price')}")
        console.print(f"[bold]Max Price:[/bold] {payload.get('max_price')}")
        console.print(f"[bold]Min Mileage:[/bold] {payload.get('min_mileage')}")
        console.print(f"[bold]Max Mileage:[/bold] {payload.get('max_mileage')}")
        console.print(
            f"[bold]Airbags:[/bold] "
            f"{payload.get('min_no_of_airbags')} - {payload.get('max_no_of_airbags')}"
        )
        console.print(f"[bold]Rating:[/bold] {payload.get('overall_rating')}")
        console.print(f"[bold]Fuel Type:[/bold] {payload.get('fuel_type')}")
        console.print(f"[bold]Trim:[/bold] {payload.get('trim_name')}")

        console.print("-" * 100)
        console.print(payload.get("content", "")[:1500])


if __name__ == "__main__":
    main()
