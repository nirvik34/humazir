import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich import box

from humanizr import __version__
from humanizr.config import CFG
from humanizr.parser import parse
from humanizr import detector as det
from humanizr import humanizer as hum
from humanizr import skills as sk
from humanizr import exporters as exp


CONFIG_FILE = Path.home() / ".humanizr.json"


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            return {}
    return {}


def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))



app = typer.Typer(help="Humanizr CLI", add_completion=False)
skill_app = typer.Typer(help="Skill packs")
app.add_typer(skill_app, name="skill")

console = Console()


def banner():
    console.print(
        Panel.fit(
            f"[bold green]HUMANIZR[/bold green]\n[dim]v{__version__}[/dim]",
            border_style="green",
        )
    )


def task(label, func, *args, **kwargs):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task(label, total=None)
        return func(*args, **kwargs)


@app.command("set-model")
def set_model(name: str):
    cfg = load_config()
    cfg["model"] = name
    save_config(cfg)
    console.print(f"[green]Saved model:[/green] {name}")


@app.command("current-model")
def current_model():
    cfg = load_config()
    model = cfg.get("model", "deepseek-coder:6.7b")
    console.print(f"[cyan]Current model:[/cyan] {model}")


@app.command("models")
def models():
    console.print("""
[bold green]Available Models[/bold green]

• deepseek-coder:6.7b
• llama3:8b
• mistral
• phi3
• codellama
""")


@app.command()
def detect(file: str):
    banner()

    text = task("Reading file...", parse, file)

    rules = sk.load_skills().get("detect", [])

    result = task(
        "Analyzing text...",
        det.detect,
        text,
        sensitivity=CFG["detection"]["default_sensitivity"],
        extra_detect_rules=rules,
    )

    console.print(
        Panel.fit(
            f"AI Score: {result.ai_score}%\n"
            f"Confidence: {result.confidence}\n"
            f"{result.verdict}",
            border_style="cyan",
        )
    )



@app.command()
def humanize(file: str):
    banner()

    text = task("Reading file...", parse, file)

    rules = sk.load_skills().get("humanize", [])

    result = task(
        "Humanizing...",
        hum.humanize,
        text,
        style=CFG["humanizer"]["default_style"],
        skill_rules=rules,
    )

    console.print(
        Panel(
            result.rewritten,
            title="Humanized Output",
            border_style="green",
        )
    )


@app.command()
def report():
    banner()

    folder = Path(CFG["output"]["reports_dir"])

    if not folder.exists():
        console.print("[yellow]No reports found[/yellow]")
        return

    files = sorted(folder.glob("*.json"), reverse=True)

    if not files:
        console.print("[yellow]No reports found[/yellow]")
        return

    latest = files[0]
    data = json.loads(latest.read_text())
    console.print_json(json.dumps(data, indent=2))



@skill_app.command("list")
def skill_list():
    banner()

    items = sk.list_skills()

    if not items:
        console.print("[yellow]No skills installed[/yellow]")
        return

    table = Table(box=box.SIMPLE)
    table.add_column("Name")
    table.add_column("Humanize")
    table.add_column("Detect")

    for s in items:
        table.add_row(
            s["name"],
            str(s["humanize_rules"]),
            str(s["detect_rules"]),
        )

    console.print(table)


# -----------------------------------

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        banner()
        console.print(ctx.get_help())


def run():
    app()


if __name__ == "__main__":
    run()