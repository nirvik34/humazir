"""
HUMANIZR CLI — AI Detector + Humanizer
Usage:
    humanizr detect <file> [--sensitivity low|medium|high] [--save] [--export txt|docx]
    humanizr humanize <file> [--style student|casual|expert|journalist] [--save]
    humanizr report
    humanizr skill list
    humanizr skill add <file.md>
    humanizr skill remove <name>
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box

from humanizr import __version__
from humanizr.config import CFG
from humanizr.parser import parse, SUPPORTED
from humanizr import detector as det
from humanizr import humanizer as hum
from humanizr import skills as sk
from humanizr import exporters as exp
from humanizr.utils import score_color, score_label

app  = typer.Typer(help="HUMANIZR — AI detection & humanization engine", add_completion=False)
skill_app = typer.Typer(help="Manage skill packs")
app.add_typer(skill_app, name="skill")

console = Console()


def _banner():
    console.print(Panel(
        Text("HUMANIZR", style="bold green", justify="center"),
        subtitle=f"[dim]v{__version__} · AI detect & rewrite[/dim]",
        border_style="green",
        padding=(0, 4),
    ))


@app.command()
def detect(
    file: str = typer.Argument(..., help="Path to .txt / .pdf / .docx file"),
    sensitivity: str = typer.Option(
        CFG["detection"]["default_sensitivity"],
        "--sensitivity", "-s",
        help="Detection sensitivity: low | medium | high",
    ),
    save: bool = typer.Option(False, "--save", help="Save JSON report to reports/"),
    export: Optional[str] = typer.Option(
        None, "--export", "-e",
        help="Export highlighted file: txt | docx",
    ),
    no_banner: bool = typer.Option(False, "--no-banner", hidden=True),
):
    """Detect AI-generated content in a file and score it 0–100."""
    if not no_banner:
        _banner()

    p = Path(file)
    console.print(f"[dim]Scanning:[/dim] [bold]{p.name}[/bold]")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as prog:
        prog.add_task("Parsing file...", total=None)
        try:
            text = parse(file)
        except (FileNotFoundError, ValueError, ImportError) as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    loaded = sk.load_skills()
    extra_detect = loaded.get("detect", [])
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as prog:
        prog.add_task("Analysing patterns...", total=None)
        result = det.detect(text, sensitivity=sensitivity, extra_detect_rules=extra_detect)
    color = score_color(result.ai_score)
    label = score_label(result.ai_score)
    bar_filled = int(result.ai_score / 5)
    bar = "█" * bar_filled + "░" * (20 - bar_filled)

    score_text = Text()
    score_text.append(f"\n  AI Score  ", style="dim")
    score_text.append(f"{result.ai_score}%", style=f"bold {color}")
    score_text.append(f"  [{label}]\n", style=color)
    score_text.append(f"  [{bar}]  ", style=color)
    score_text.append(f"confidence: {result.confidence}\n", style="dim")
    score_text.append(f"\n  {result.verdict}\n", style="italic")

    console.print(Panel(score_text, title="Detection Result", border_style=color))
    sig_table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
    sig_table.add_column("Signal", style="dim", width=20)
    sig_table.add_column("Score", justify="right", width=8)
    sig_table.add_column("Interpretation", width=30)

    interp = {
        "burstiness":      ("low=varied=human, high=uniform=AI", 0.5),
        "transitions":     ("frequency of 'furthermore', 'moreover'…", 0.4),
        "vocabulary":      ("AI vocabulary hits", 0.4),
        "inflation":       ("significance-inflation phrases", 0.3),
        "em_dash":         ("em dash (—) overuse", 0.3),
        "para_uniformity": ("paragraph structure sameness", 0.4),
    }
    for k, v in result.signals.items():
        hint, threshold = interp.get(k, ("", 0.5))
        style = "red" if v >= threshold else "green"
        sig_table.add_row(k.replace("_", " "), f"[{style}]{v:.2f}[/{style}]", f"[dim]{hint}[/dim]")

    console.print(sig_table)
    if result.flagged_passages:
        console.print(f"\n[bold]Flagged passages[/bold] [dim]({len(result.flagged_passages)} found)[/dim]")
        for fp in result.flagged_passages[:10]:
            flags_str = ", ".join(fp["flags"])
            console.print(f"  [dim]Line {fp['line']:>3}[/dim]  [red]{fp['excerpt']}[/red]")
            console.print(f"         [dim]↳ {flags_str}[/dim]")
    else:
        console.print("\n[green]No strong AI patterns flagged.[/green]")
    if result.human_signals:
        console.print(f"\n[green]Human signals:[/green] {' · '.join(result.human_signals)}")
    if save:
        report_data = exp.build_detect_report(file, result)
        path = exp.save_report(report_data, stem=p.stem)
        console.print(f"\n[dim]Report saved:[/dim] [bold]{path}[/bold]")

    if export:
        stem = p.stem
        if export.lower() == "txt":
            out = exp.export_highlighted_txt(text, result.flagged_passages, stem=stem)
            console.print(f"[dim]Highlighted TXT:[/dim] [bold]{out}[/bold]")
        elif export.lower() == "docx":
            try:
                out = exp.export_highlighted_docx(text, result.flagged_passages, stem=stem)
                console.print(f"[dim]Highlighted DOCX:[/dim] [bold]{out}[/bold]")
            except ImportError as e:
                console.print(f"[yellow]Warning:[/yellow] {e}")
        else:
            console.print(f"[yellow]Unknown export format:[/yellow] {export} (use txt or docx)")



@app.command()
def humanize(
    file: str = typer.Argument(..., help="Path to .txt / .pdf / .docx file"),
    style: str = typer.Option(
        CFG["humanizer"]["default_style"],
        "--style",
        help="Writing style: student | casual | expert | journalist",
    ),
    save: bool = typer.Option(False, "--save", help="Save humanized text to exports/"),
    no_banner: bool = typer.Option(False, "--no-banner", hidden=True),
):
    if not no_banner:
        _banner()

    p = Path(file)
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as prog:
        prog.add_task("Parsing file...", total=None)
        try:
            text = parse(file)
        except (FileNotFoundError, ValueError, ImportError) as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
    loaded = sk.load_skills()
    skill_rules = loaded.get("humanize", [])

    console.print(f"[dim]File:[/dim] [bold]{p.name}[/bold]  [dim]Style:[/dim] [bold]{style}[/bold]  "
                  f"[dim]Words:[/dim] {len(text.split())}")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console, transient=True) as prog:
        prog.add_task("Rewriting with human patterns...", total=None)
        try:
            result = hum.humanize(text, style=style, skill_rules=skill_rules)
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    console.print(Panel(
        result.rewritten,
        title=f"[green]Humanized Output[/green] [dim](style: {style})[/dim]",
        border_style="green",
        padding=(1, 2),
    ))

    if result.changes:
        console.print("\n[bold]Changes made:[/bold]")
        for c in result.changes:
            console.print(f"  [dim]·[/dim] {c}")

    console.print(
        f"\n  [dim]Words:[/dim] {result.word_count_before} → {result.word_count_after}"
    )

    if save:
        out = exp.export_humanized_txt(result.rewritten, stem=p.stem)
        report_data = exp.build_humanize_report(file, result)
        rep = exp.save_report(report_data, stem=p.stem + "_humanize")
        console.print(f"[dim]Saved:[/dim] [bold]{out}[/bold]")
        console.print(f"[dim]Report:[/dim] [bold]{rep}[/bold]")



@app.command()
def report(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all saved reports"),
):
    _banner()
    reports_dir = Path(CFG["output"]["reports_dir"])

    if not reports_dir.exists() or not list(reports_dir.glob("*.json")):
        console.print("[dim]No reports found. Run detect --save or humanize --save first.[/dim]")
        return

    files = sorted(reports_dir.glob("*.json"), reverse=True)

    if list_all:
        table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
        table.add_column("File", style="bold")
        table.add_column("Command")
        table.add_column("Score / Style")
        table.add_column("Timestamp")
        for f in files:
            try:
                data = json.loads(f.read_text())
                cmd = data.get("command", "?")
                score_or_style = (
                    f"{data['ai_score']}%" if cmd == "detect"
                    else data.get("style", "?")
                )
                table.add_row(f.name, cmd, score_or_style, data.get("timestamp", "?")[:19])
            except Exception:
                table.add_row(f.name, "?", "?", "?")
        console.print(table)
    else:
        latest = files[0]
        data = json.loads(latest.read_text())
        console.print(f"\n[bold]Latest report:[/bold] {latest.name}\n")
        console.print_json(json.dumps(data, indent=2))



@skill_app.command("list")
def skill_list():
    _banner()
    skills = sk.list_skills()
    if not skills:
        console.print("[dim]No skill packs installed. Add one with: humanizr skill add <file.md>[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="dim")
    table.add_column("Skill file", style="bold green")
    table.add_column("Humanize rules", justify="right")
    table.add_column("Detect rules", justify="right")
    for s in skills:
        table.add_row(s["name"], str(s["humanize_rules"]), str(s["detect_rules"]))
    console.print(table)


@skill_app.command("add")
def skill_add(path: str = typer.Argument(..., help="Path to .md skill file")):
    _banner()
    try:
        dest = sk.add_skill(path)
        console.print(f"[green]Skill installed:[/green] {dest}")
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@skill_app.command("remove")
def skill_remove(name: str = typer.Argument(..., help="Skill file name (with or without .md)")):
    _banner()
    if sk.remove_skill(name):
        console.print(f"[green]Skill removed:[/green] {name}")
    else:
        console.print(f"[yellow]Skill not found:[/yellow] {name}")
        raise typer.Exit(1)



@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
):
    if version:
        console.print(f"humanizr v{__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        _banner()
        console.print(ctx.get_help())
def run():
    app()

if __name__ == "__main__":
    run()