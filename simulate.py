import sys
from pathlib import Path

import click

from src.engine import run_montecarlo, run_history
from src.loader import load_config, load_equity_csv
from src.report import generate_report


def _validate_out_path(ctx: click.Context, param: click.Parameter, value: str) -> Path:
    out = Path(value)
    if not out.suffix:
        raise click.BadParameter("output path must include a filename", ctx=ctx, param=param)
    if not out.parent.exists():
        raise click.BadParameter(f"directory '{out.parent}' does not exist", ctx=ctx, param=param)
    return out


@click.group()
def cli() -> None:
    pass


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
@click.option(
    "--runs",
    default=10_000,
    show_default=True,
    type=click.IntRange(min=1),
    help="Number of Monte Carlo simulation runs.",
)
def run(equity: Path, config: Path, out: Path, runs: int) -> None:
    equity_data = load_equity_csv(str(equity))
    firm_config = load_config(str(config))
    results = run_montecarlo(equity_data, firm_config, runs)
    generate_report(results, out)
    click.echo(f"Report written to {out}")


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
    equity_data = load_equity_csv(str(equity))
    firm_config = load_config(str(config))
    results = run_history(equity_data, firm_config)
    generate_report(results, out)
    click.echo(f"Report written to {out}")


if __name__ == "__main__":
    cli()
