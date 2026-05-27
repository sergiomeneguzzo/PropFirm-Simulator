from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from src.rules import FirmConfig, RuleResult


@dataclass
class MonteCarloResults:
    config: FirmConfig
    runs: int
    pass_rate: float
    rule_results: list[RuleResult] = field(default_factory=list)
    equity_paths: list[list[float]] = field(default_factory=list)


@dataclass
class HistoricalResults:
    config: FirmConfig
    windows: list[dict] = field(default_factory=list)
    pass_rate: float = 0.0


def run_monte_carlo(
    equity_data: pd.DataFrame,
    config: FirmConfig,
    runs: int,
) -> MonteCarloResults:
    ...


def run_historical(
    equity_data: pd.DataFrame,
    config: FirmConfig,
) -> HistoricalResults:
    ...
