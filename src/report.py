from __future__ import annotations

from pathlib import Path

from src.engine import HistoryResult, MonteCarloResult


def generate_report(
    results: MonteCarloResult | HistoryResult,
    output_path: Path,
) -> None:
    ...
