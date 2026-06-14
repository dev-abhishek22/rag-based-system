from rich.align import Align
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.cli.features import CLI_FEATURES
from src.cli.theme import get_theme

console = Console()


def render_banner(session):
    theme = get_theme(session.theme_name)

    banner = Text()

    banner.append(
        """
    ____                 _____                     __
   / __ \\___ _   __     / ___/___  ____ __________/ /_
  / /_/ / _ \\ | / /     \\__ \\/ _ \\/ __ `/ ___/ ___/ __ \\
 / _, _/  __/ |/ /     ___/ /  __/ /_/ / /  / /__/ / / /
/_/ |_|\\___/|___/     /____/\\___/\\__,_/_/   \\___/_/ /_/

""",
        style=theme["primary"],
    )

    subtitle = Text(
        "Semantic Automotive Search Engine",
        style=theme["muted"],
        justify="center",
    )

    console.print(
        Panel(
            Group(
                Align.center(banner),
                Text(""),
                Align.center(subtitle),
            ),
            border_style=theme["secondary"],
            padding=(1, 2),
        )
    )


def render_command_palette(session):
    theme = get_theme(session.theme_name)

    table = Table.grid(padding=(0, 3))
    table.add_column(style=theme["accent"], no_wrap=True)
    table.add_column(style="white")
    table.add_column(style=theme["muted"])

    for feature in CLI_FEATURES:
        table.add_row(
            f"[bold]{feature.shortcut}[/bold]",
            f"[bold {theme['primary']}]{feature.command}[/bold {theme['primary']}]",
            feature.description,
        )

    console.print(
        Panel(
            table,
            title="[bold]RevSearch Command Palette[/bold]",
            subtitle="Type a slash command, e.g. /theme ocean",
            border_style=theme["secondary"],
            padding=(1, 2),
        )
    )


def render_help(session):
    theme = get_theme(session.theme_name)

    table = Table(
        title="Available Commands",
        border_style=theme["secondary"],
        header_style=f"bold {theme['primary']}",
    )

    table.add_column("Command", style=theme["accent"], no_wrap=True)
    table.add_column("Description", style="white")

    for feature in CLI_FEATURES:
        table.add_row(feature.command, feature.description)

    console.print(table)


def render_status(session):
    theme = get_theme(session.theme_name)

    console.print(
        Panel.fit(
            f"[bold {theme['primary']}]TOP-K[/bold {theme['primary']}]: {session.top_k}   "
            f"[bold {theme['primary']}]THEME[/bold {theme['primary']}]: {session.theme_name}   "
            f"[bold {theme['primary']}]RAW[/bold {theme['primary']}]: {session.raw_mode}   "
            f"[bold {theme['primary']}]SOURCES[/bold {theme['primary']}]: {session.show_sources}",
            border_style=theme["secondary"],
        )
    )


def render_answer(session, point):
    theme = get_theme(session.theme_name)
    payload = point.payload or {}

    content = payload.get("content", "")[:1600]

    answer = f"""
## {payload.get("car_name", "Unknown Car")}

**Brand:** {payload.get("brand_name", "N/A")}  
**Model:** {payload.get("model_name", "N/A")}  
**Submodel:** {payload.get("submodel_name", "N/A")}  
**Chunk:** `{payload.get("chunk_type", "N/A")}`  
**Score:** `{point.score:.4f}`  

---

{content}
"""

    console.print(
        Panel(
            Markdown(answer),
            title="Answer",
            border_style=theme["secondary"],
        )
    )


def render_sources(session, results):
    if not session.show_sources:
        return

    theme = get_theme(session.theme_name)

    table = Table(
        title="Sources",
        border_style=theme["secondary"],
        header_style=f"bold {theme['primary']}",
    )

    table.add_column("#", justify="right", style=theme["accent"])
    table.add_column("Score", style="white")
    table.add_column("Car", style="white")
    table.add_column("Chunk", style=theme["accent"])
    table.add_column("URL", style=theme["muted"])

    for index, point in enumerate(results, start=1):
        payload = point.payload or {}

        table.add_row(
            str(index),
            f"{point.score:.4f}",
            str(payload.get("car_name", "N/A")),
            str(payload.get("chunk_type", "N/A")),
            str(payload.get("url", "N/A")),
        )

    console.print(table)


def render_raw(point):
    payload = point.payload or {}
    console.print(payload)
