from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.engine import run_history, run_montecarlo
from src.rules import ChallengeConfig


@pytest.fixture
def config() -> ChallengeConfig:
    return ChallengeConfig(
        name="Test",
        account_size=10_000,
        profit_target_pct=10.0,
        max_drawdown_pct=10.0,
        daily_drawdown_pct=5.0,
        max_trading_days=20,
        min_trading_days=3,
    )


@pytest.fixture
def equity_df() -> pd.DataFrame:
    rng = np.random.default_rng(seed=0)
    returns = rng.normal(0.003, 0.012, 100)
    equity = np.empty(101)
    equity[0] = 10_000.0
    equity[1:] = 10_000.0 * np.cumprod(1 + returns)
    dates = pd.bdate_range("2024-01-02", periods=101)
    return pd.DataFrame({"date": dates, "equity": equity})


def test_montecarlo_passrate_bounds(config: ChallengeConfig, equity_df: pd.DataFrame) -> None:
    result = run_montecarlo(equity_df, config, runs=200)
    assert 0.0 <= result.pass_rate <= 100.0


def test_history_window_count(config: ChallengeConfig, equity_df: pd.DataFrame) -> None:
    n = len(equity_df)
    result = run_history(equity_df, config)
    assert len(result.windows) == n - config.max_trading_days
