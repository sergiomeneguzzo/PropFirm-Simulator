from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import click
from rich import box
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from src.engine import run_history, run_montecarlo
from src.loader import load_config, load_equity_csv, load_trades_csv, trades_to_equity
from src.report import render_history, render_montecarlo

console = Console()

_STATUS_STYLE: dict[str, str] = {
    "PASS": "bold green",
    "FAIL_MAX_DD": "bold red",
    "FAIL_DAILY_DD": "yellow",
    "FAIL_TIME": "dim",
}


def _validate_out_path(ctx: click.Context, param: click.Parameter, value: str) -> Path:
    out = Path(value)
    if not out.suffix:
        raise click.BadParameter("output path must include a filename", ctx=ctx, param=param)
    if not out.parent.exists():
        raise click.BadParameter(
            f"directory '{out.parent}' does not exist", ctx=ctx, param=param
        )
    return out


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--equity",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to equity curve CSV or trades CSV (see --trades).",
)
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to YAML firm config file.",
)
@click.option(
    "--out",
    required=True,
    callback=_validate_out_path,
    is_eager=False,
    expose_value=True,
    help="Output HTML report path.",
)
@click.option(
    "--runs",
    default=10_000,
    show_default=True,
    type=click.IntRange(min=1),
    help="Number of Monte Carlo simulation runs.",
)
@click.option(
    "--trades",
    is_flag=True,
    default=False,
    help="Treat --equity as a trades CSV (ticket, open_time, close_time, profit).",
)
def run(equity: Path, config: Path, out: Path, runs: int, trades: bool) -> None:
    try:
        firm_config = load_config(str(config))
    except ValueError as exc:
        console.print(f"[bold red]Config error:[/] {exc}")
        sys.exit(1)

    try:
        if trades:
            trades_df = load_trades_csv(str(equity))
            equity_data = trades_to_equity(trades_df, firm_config.account_size)
        else:
            equity_data = load_equity_csv(str(equity))
    except ValueError as exc:
        console.print(f"[bold red]Data error:[/] {exc}")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(f"Simulating {runs:,} runs…", total=runs)

        def on_progress(completed: int) -> None:
            progress.update(task, completed=completed)

        mc_result = run_montecarlo(equity_data, firm_config, runs, on_progress=on_progress)

    table = Table(
        title=f"[bold]{firm_config.name}[/] — {runs:,} Monte Carlo runs",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Pass Rate", f"[bold green]{mc_result.pass_rate:.2f}%[/]")
    table.add_section()
    for status, pct in mc_result.failure_breakdown.items():
        style = _STATUS_STYLE.get(status, "")
        table.add_row(f"[{style}]{status}[/]", f"[{style}]{pct:.2f}%[/]")
    table.add_section()
    table.add_row("Avg Days (Pass)", f"{mc_result.avg_days_pass:.1f}")
    table.add_row("Avg Days (Fail)", f"{mc_result.avg_days_fail:.1f}")

    console.print(table)

    render_montecarlo(mc_result, firm_config, str(out))
    console.print(f"\n[bold]Report saved:[/] {out}")


@cli.command()
@click.option(
    "--equity",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to equity curve CSV file.",
)
@click.option(
    "--config",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to YAML firm config file.",
)
@click.option(
    "--out",
    required=True,
    callback=_validate_out_path,
    is_eager=False,
    expose_value=True,
    help="Output HTML report path.",
)
def history(equity: Path, config: Path, out: Path) -> None:
    try:
        firm_config = load_config(str(config))
    except ValueError as exc:
        console.print(f"[bold red]Config error:[/] {exc}")
        sys.exit(1)

    try:
        equity_data = load_equity_csv(str(equity))
    except ValueError as exc:
        console.print(f"[bold red]Data error:[/] {exc}")
        sys.exit(1)

    with console.status(f"Analysing {len(equity_data):,} rows…"):
        hist_result = run_history(equity_data, firm_config)

    total = len(hist_result.windows)
    status_counts: Counter[str] = Counter(w.result.status for w in hist_result.windows)

    table = Table(
        title=f"[bold]{firm_config.name}[/] — Historical Windows ({firm_config.max_trading_days}-day)",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Status", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Share", justify="right")

    table.add_row("Total", str(total), "100.0%")
    table.add_section()
    for status in ("PASS", "FAIL_MAX_DD", "FAIL_DAILY_DD", "FAIL_TIME"):
        count = status_counts.get(status, 0)
        pct = count / total * 100 if total else 0.0
        style = _STATUS_STYLE.get(status, "")
        table.add_row(
            f"[{style}]{status}[/]",
            f"[{style}]{count}[/]",
            f"[{style}]{pct:.1f}%[/]",
        )

    console.print(table)

    render_history(hist_result, firm_config, str(out))
    console.print(f"\n[bold]Report saved:[/] {out}")


if __name__ == "__main__":
    cli()
