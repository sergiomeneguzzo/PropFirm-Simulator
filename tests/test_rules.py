from __future__ import annotations

import pandas as pd
import pytest

from src.rules import ChallengeConfig, evaluate_window


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


def test_pass(config: ChallengeConfig) -> None:
    equity = pd.Series([10_000, 10_200, 10_500, 10_800, 11_100], dtype=float)
    result = evaluate_window(equity, config)
    assert result.status == "PASS"
    assert result.end_day == 4


def test_fail_max_dd(config: ChallengeConfig) -> None:
    equity = pd.Series(
        [10_000, 10_500, 10_300, 10_100, 9_900, 9_700, 9_400, 9_200, 9_000],
        dtype=float,
    )
    result = evaluate_window(equity, config)
    assert result.status == "FAIL_MAX_DD"
    assert result.end_day == 6
    assert result.max_dd_pct < -10.0


def test_fail_daily_dd(config: ChallengeConfig) -> None:
    equity = pd.Series([10_000, 10_100, 10_050, 9_500], dtype=float)
    result = evaluate_window(equity, config)
    assert result.status == "FAIL_DAILY_DD"
    assert result.end_day == 3
    assert result.max_daily_dd_pct < -5.0


def test_fail_time(config: ChallengeConfig) -> None:
    equity = pd.Series([10_000.0] * (config.max_trading_days + 1))
    result = evaluate_window(equity, config)
    assert result.status == "FAIL_TIME"
    assert result.end_day == config.max_trading_days


def test_min_trading_days(config: ChallengeConfig) -> None:
    equity = pd.Series([10_000, 11_100, 11_200, 11_300, 11_400], dtype=float)
    result = evaluate_window(equity, config)
    assert result.status == "PASS"
    assert result.end_day == config.min_trading_days
