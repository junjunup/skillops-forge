"""``skillops`` CLI — typer + rich."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from skillops_forge import __version__
from skillops_forge.ci import init_ci as ci_init
from skillops_forge.config import (
    DEFAULT_OUT_DIR,
    DEFAULT_THRESHOLD,
    EXIT_AUDIT_FAILED,
    EXIT_INTERNAL_ERROR,
    EXIT_OK,
    EXIT_USER_ERROR,
)
from skillops_forge.exceptions import SkillOpsError, UserError
from skillops_forge.logging_setup import setup_logging
from skillops_forge.models import SkillReport
from skillops_forge.pipeline import run_pipeline
from skillops_forge.reporter import render
from skillops_forge.rule_catalog import RuleInfo, get_rule, list_rules

app = typer.Typer(
    name="skillops",
    help="SkillOps Forge — static analysis & risk auditor for AI skill packs.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


@app.command()
def scan(
    path: Annotated[Path, typer.Argument(help="Skill file or directory to scan.")],
    report: Annotated[
        str,
        typer.Option(
            "--report",
            "-r",
            help="Report format: md | html | json | all.",
            case_sensitive=False,
        ),
    ] = "md",
    out_dir: Annotated[
        Path,
        typer.Option("--out-dir", "-o", help="Directory to write report files to."),
    ] = DEFAULT_OUT_DIR,
    threshold: Annotated[
        int,
        typer.Option("--threshold", "-t", help="Pass-fail score threshold (0-100)."),
    ] = DEFAULT_THRESHOLD,
    no_cursor_rules: Annotated[
        bool,
        typer.Option("--no-cursor-rules", help="Skip .cursor/rules directories."),
    ] = False,
    no_runner: Annotated[
        bool,
        typer.Option("--no-runner", help="Skip examples dry-run."),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable DEBUG logging.")] = False,
) -> None:
    """Scan a skill file or directory and produce a risk report."""
    setup_logging(verbose=verbose)
    fmt = report.lower()
    if fmt not in {"md", "html", "json", "all"}:
        console.print(f"[red]Invalid --report value:[/red] {report!r}")
        raise typer.Exit(code=EXIT_USER_ERROR)
    if not path.exists():
        console.print(f"[red]Path does not exist:[/red] {path}")
        raise typer.Exit(code=EXIT_USER_ERROR)
    try:
        result = run_pipeline(
            path,
            threshold=threshold,
            include_cursor_rules=not no_cursor_rules,
            enable_runner=not no_runner,
        )
        written = render(result, fmt=fmt, out_dir=out_dir)  # type: ignore[arg-type]
    except UserError as exc:
        console.print(f"[red]User error:[/red] {exc}")
        raise typer.Exit(code=EXIT_USER_ERROR) from exc
    except SkillOpsError as exc:
        console.print(f"[red]SkillOps error:[/red] {exc}")
        raise typer.Exit(code=EXIT_INTERNAL_ERROR) from exc
    except Exception as exc:  # pragma: no cover - last-resort safety net
        console.print(f"[red]Internal error:[/red] {exc}")
        raise typer.Exit(code=EXIT_INTERNAL_ERROR) from exc

    _print_summary(result, written)
    raise typer.Exit(code=EXIT_OK if result.is_passed else EXIT_AUDIT_FAILED)


@app.command(name="init-ci")
def init_ci(
    provider: Annotated[
        str,
        typer.Option(
            "--provider",
            "-p",
            help="CI provider (currently only github-actions).",
        ),
    ] = "github-actions",
    github_actions: Annotated[
        bool,
        typer.Option(
            "--github-actions/--no-github-actions",
            help="Generate a GitHub Actions workflow (default; alias for --provider github-actions).",
        ),
    ] = True,
    out: Annotated[
        Path,
        typer.Option("--out", "-o", help="Output workflow path."),
    ] = Path(".github/workflows/skillops.yml"),
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing file.")] = False,
) -> None:
    """Generate a CI workflow that runs SkillOps Forge."""
    setup_logging(verbose=False)
    if not github_actions:
        console.print("[red]No CI provider selected (pass --github-actions).[/red]")
        raise typer.Exit(code=EXIT_USER_ERROR)
    if provider != "github-actions":
        console.print(f"[red]Unsupported provider:[/red] {provider}")
        raise typer.Exit(code=EXIT_USER_ERROR)
    try:
        target = ci_init(provider="github-actions", out=out, force=force)
    except FileExistsError as exc:
        console.print(f"[red]{exc}[/red] Use --force to overwrite.")
        raise typer.Exit(code=EXIT_USER_ERROR) from exc
    except SkillOpsError as exc:
        console.print(f"[red]SkillOps error:[/red] {exc}")
        raise typer.Exit(code=EXIT_INTERNAL_ERROR) from exc
    console.print(f"[green]Wrote[/green] {target}")
    raise typer.Exit(code=EXIT_OK)


@app.command()
def version() -> None:
    """Print the SkillOps Forge version."""
    console.print(f"skillops-forge {__version__}")
    raise typer.Exit(code=EXIT_OK)


@app.command()
def rules(
    severity: Annotated[
        str | None,
        typer.Option(
            "--severity",
            "-s",
            help="Filter by severity (critical/high/medium/low/info).",
            case_sensitive=False,
        ),
    ] = None,
    kind: Annotated[
        str | None,
        typer.Option(
            "--kind",
            "-k",
            help="Filter by kind: 'audit' or 'security'.",
            case_sensitive=False,
        ),
    ] = None,
) -> None:
    """List every built-in rule (security + audit)."""
    setup_logging(verbose=False)
    catalog = list_rules()
    if severity:
        sev = severity.lower()
        catalog = [r for r in catalog if r.severity.value == sev]
    if kind:
        kd = kind.lower()
        if kd not in {"audit", "security"}:
            console.print(f"[red]Invalid --kind:[/red] {kind!r}")
            raise typer.Exit(code=EXIT_USER_ERROR)
        catalog = [r for r in catalog if r.kind == kd]
    table = Table(title=f"SkillOps Forge rules ({len(catalog)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Kind", style="magenta")
    table.add_column("Severity")
    table.add_column("Name")
    for r in catalog:
        table.add_row(r.id, r.kind, r.severity.value.upper(), r.name)
    console.print(table)
    raise typer.Exit(code=EXIT_OK)


@app.command()
def rule(
    rule_id: Annotated[str, typer.Argument(help="Rule ID, e.g. SEC-012 or AUD-110.")],
) -> None:
    """Show full details for a single rule."""
    setup_logging(verbose=False)
    info = get_rule(rule_id)
    if info is None:
        console.print(f"[red]Unknown rule:[/red] {rule_id}")
        raise typer.Exit(code=EXIT_USER_ERROR)
    _print_rule_detail(info)
    raise typer.Exit(code=EXIT_OK)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _print_rule_detail(info: RuleInfo) -> None:
    table = Table(show_header=False, header_style="bold", title=f"Rule {info.id}")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("ID", info.id)
    table.add_row("Kind", info.kind)
    table.add_row("Severity", info.severity.value.upper())
    table.add_row("Name", info.name)
    table.add_row("Category", info.category)
    table.add_row("Message", escape(info.message))
    table.add_row("Remediation", escape(info.remediation))
    table.add_row("Docs", info.docs_url)
    console.print(table)


def _print_summary(report: SkillReport, written: list[Path]) -> None:
    summary = report.summary()
    table = Table(title="SkillOps Forge Result", show_header=False, header_style="bold")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value")
    table.add_row("Score", f"{summary['score']} / 100")
    table.add_row("Risk", summary["overall_risk"].upper())
    table.add_row("Threshold", str(summary["threshold"]))
    table.add_row("Passed", "yes" if summary["is_passed"] else "no")
    table.add_row("Files", str(summary["files"]))
    table.add_row("Audit findings", str(summary["audit_findings"]))
    table.add_row("Security findings", str(summary["security_findings"]))
    table.add_row("Examples run", str(summary["examples_run"]))
    console.print(table)
    for p in written:
        console.print(f"  → {p}")


def main() -> None:  # pragma: no cover - CLI entry
    """Module-level entry point."""
    try:
        app()
    except SystemExit:
        raise
    except Exception as exc:
        console.print(f"[red]Fatal:[/red] {exc}")
        sys.exit(EXIT_INTERNAL_ERROR)


__all__ = ["app", "main"]
