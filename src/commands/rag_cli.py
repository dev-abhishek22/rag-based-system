import typer

from src.cli.app import run

app = typer.Typer(add_completion=False)


@app.callback(invoke_without_command=True)
def main():
    run()


if __name__ == "__main__":
    app()
