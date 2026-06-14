import os

from src.cli.renderer import console, render_help, render_status
from src.cli.theme import THEMES


def handle_command(command: str, session) -> bool:
    parts = command.split()
    cmd = parts[0]

    if cmd == "/help":
        render_help(session)
        return True

    if cmd == "/clear":
        os.system("clear")
        return True

    if cmd == "/raw":
        session.raw_mode = not session.raw_mode
        console.print(f"[green]Raw mode:[/green] {session.raw_mode}")
        return True

    if cmd == "/sources":
        session.show_sources = not session.show_sources
        console.print(f"[green]Show sources:[/green] {session.show_sources}")
        return True

    if cmd == "/history":
        if not session.history:
            console.print("[yellow]No history yet.[/yellow]")
            return True

        for index, item in enumerate(session.history, start=1):
            console.print(f"[cyan]{index}.[/cyan] {item}")
        return True

    if cmd == "/topk":
        if len(parts) < 2:
            console.print("[red]Usage:[/red] /topk 10")
            return True

        try:
            session.top_k = int(parts[1])
            console.print(f"[green]top_k changed to[/green] {session.top_k}")
        except ValueError:
            console.print("[red]top_k must be a number[/red]")

        return True

    if cmd == "/theme":
        if len(parts) < 2:
            console.print("[red]Usage:[/red] /theme hacker|ocean|sunset|amber")
            return True

        theme_name = parts[1].lower()

        if theme_name not in THEMES:
            console.print("[red]Available themes:[/red] hacker, ocean, sunset, amber")
            return True

        session.theme_name = theme_name
        console.print(f"[green]Theme changed to[/green] {theme_name}")
        render_status(session)
        return True

    if cmd == "/exit":
        raise EOFError

    console.print("[red]Unknown command. Try /help[/red]")
    return True
