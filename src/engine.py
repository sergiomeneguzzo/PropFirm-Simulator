from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.rules import ChallengeConfig, SimResult


@dataclass
class MonteCarloResults:
    config: ChallengeConfig
    runs: int
    pass_rate: float
    sim_results: list[SimResult] = field(default_factory=list)
    equity_paths: list[list[float]] = field(default_factory=list)


@dataclass
class HistoricalResults:
    config: ChallengeConfig
    windows: list[dict] = field(default_factory=list)
    pass_rate: float = 0.0


def run_monte_carlo(
    equity_data: pd.DataFrame,
    config: ChallengeConfig,
    runs: int,
) -> MonteCarloResults:
    ...


def run_historical(
    equity_data: pd.DataFrame,
    config: ChallengeConfig,
) -> HistoricalResults:
    ...
