from concurrent.futures import ThreadPoolExecutor
from time import sleep

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from src.cli.commands import handle_command
from src.cli.renderer import (
    console,
    render_answer,
    render_banner,
    render_command_palette,
    render_raw,
    render_sources,
    render_status,
)
from src.cli.session import CliSession
from src.cli.theme import get_theme, get_prompt_style
from src.retrievers.qdrant_retriever import QdrantRetriever
from prompt_toolkit.formatted_text import FormattedText


class SlashCommandCompleter(Completer):
    commands = [
        ("/help", "Show commands and examples"),
        ("/topk", "Set result count"),
        ("/theme", "Change CLI theme"),
        ("/raw", "Toggle raw output"),
        ("/sources", "Toggle sources"),
        ("/history", "View search history"),
        ("/clear", "Clear terminal"),
        ("/exit", "Quit RevSearch"),
    ]

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.strip()

        if not text.startswith("/"):
            return

        for command, description in self.commands:
            if command.startswith(text):
                yield Completion(
                    command,
                    start_position=-len(text),
                    display=command,
                    display_meta=description,
                )


def get_prompt(session):
    theme = get_theme(session.theme_name)

    return ANSI(
        f"{theme['prompt_primary']}rev" f"{theme['prompt_accent']}search" f"\033[0m ❯ "
    )


def bottom_toolbar(session):
    return (
        f" top_k={session.top_k} | "
        f"theme={session.theme_name} | "
        f"raw={session.raw_mode} | "
        f"sources={session.show_sources} | "
        f"/help "
    )


def run():
    session_state = CliSession()

    render_banner(session_state)
    render_status(session_state)

    command_completer = SlashCommandCompleter()

    prompt_style = get_prompt_style(session_state.theme_name)

    theme = get_theme(session_state.theme_name)

    with Progress(
        SpinnerColumn(style=theme["primary"]),
        TextColumn(
            f"[bold {theme['primary']}]{{task.description}}",
            justify="left",
        ),
        BarColumn(
            bar_width=40,
            complete_style=theme["primary"],
            finished_style=theme["success"],
        ),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            "Initializing RevSearch...",
            total=100,
        )

        progress.update(task, description="Preparing environment...")
        progress.advance(task, 15)
        sleep(0.15)

        progress.update(task, description="Loading configuration...")
        progress.advance(task, 15)
        sleep(0.15)

        progress.update(task, description="Starting retrieval engine...")

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(QdrantRetriever)

            while not future.done():
                progress.advance(task, 1)
                sleep(0.03)

            retriever = future.result()

        progress.advance(task, 50)

        progress.update(task, description="Finalizing startup...")
        progress.advance(task, 20)

    console.print(
        f"[bold {theme['success']}]✓ RevSearch is ready[/bold {theme['success']}]"
    )

    console.print(f"[{theme['muted']}]Type /help to view commands.[/{theme['muted']}]")

    prompt = PromptSession(
        history=FileHistory(".revsearch_history"),
        completer=command_completer,
        complete_while_typing=True,
        style=prompt_style,
        bottom_toolbar=lambda: bottom_toolbar(session_state),
    )

    while True:
        try:
            query = prompt.prompt(get_prompt(session_state)).strip()

            if not query:
                continue

            if query.lower() in {"exit", "quit", "q"}:
                break

            if query == "/":
                render_command_palette(session_state)
                continue

            if query.startswith("/"):
                handle_command(query, session_state)
                continue

            session_state.history.append(query)

            theme = get_theme(session_state.theme_name)

            with console.status(
                f"[bold {theme['primary']}]Searching knowledge base...[/bold {theme['primary']}]",
                spinner="dots12",
            ):
                results = retriever.retrieve(
                    query=query,
                    top_k=session_state.top_k,
                    format_results=False,
                )

            if not results:
                console.print("[red]No result found.[/red]")
                continue

            best_result = results[0]

            if session_state.raw_mode:
                render_raw(best_result)
            else:
                render_answer(session_state, best_result)

            render_sources(session_state, results)

        except KeyboardInterrupt:
            console.print("\n[yellow]Use /exit to quit.[/yellow]")

        except EOFError:
            break

    console.print("[green]Goodbye![/green]")
