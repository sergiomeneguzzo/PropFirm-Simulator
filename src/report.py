from __future__ import annotations

from pathlib import Path

from src.engine import HistoricalResults, MonteCarloResults


def generate_report(
    results: MonteCarloResults | HistoricalResults,
    output_path: Path,
) -> None:
    ...
