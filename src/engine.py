from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.rules import ChallengeConfig, SimResult, evaluate_window


@dataclass
class MonteCarloResult:
    pass_rate: float
    failure_breakdown: dict[str, float]
    avg_days_pass: float
    avg_days_fail: float
    all_results: list[SimResult]
    sampled_curves: list[pd.Series]


@dataclass
class WindowResult:
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    result: SimResult


@dataclass
class HistoryResult:
    equity_df: pd.DataFrame
    windows: list[WindowResult] = field(default_factory=list)


def run_montecarlo(
    equity_df: pd.DataFrame,
    config: ChallengeConfig,
    runs: int,
) -> MonteCarloResult:
    equity_vals = equity_df["equity"].to_numpy(dtype=float)
    returns = equity_vals[1:] / equity_vals[:-1]

    if len(returns) == 0:
        raise ValueError("equity_df must have at least 2 rows to extract daily returns.")

    rng = np.random.default_rng()

    resampled = rng.choice(returns, size=(runs, config.max_trading_days), replace=True)

    initial = float(config.account_size)
    cum_prod = np.cumprod(resampled, axis=1)

    equity_paths = np.empty((runs, config.max_trading_days + 1), dtype=float)
    equity_paths[:, 0] = initial
    equity_paths[:, 1:] = initial * cum_prod

    all_results = [evaluate_window(pd.Series(equity_paths[i]), config) for i in range(runs)]

    passes = [r for r in all_results if r.status == "PASS"]
    fails = [r for r in all_results if r.status != "PASS"]

    pass_rate = len(passes) / runs * 100

    status_counts: dict[str, int] = {}
    for r in all_results:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    failure_breakdown = {s: c / runs * 100 for s, c in status_counts.items()}

    avg_days_pass = float(np.mean([r.end_day for r in passes])) if passes else 0.0
    avg_days_fail = float(np.mean([r.end_day for r in fails])) if fails else 0.0

    n_sample = min(50, runs)
    sample_idx = rng.choice(runs, size=n_sample, replace=False)
    sampled_curves = [pd.Series(equity_paths[i], dtype=float) for i in sample_idx]

    return MonteCarloResult(
        pass_rate=pass_rate,
        failure_breakdown=failure_breakdown,
        avg_days_pass=avg_days_pass,
        avg_days_fail=avg_days_fail,
        all_results=all_results,
        sampled_curves=sampled_curves,
    )


def run_history(
    equity_df: pd.DataFrame,
    config: ChallengeConfig,
) -> HistoryResult:
    window_size = config.max_trading_days + 1
    n = len(equity_df)

    if n < window_size:
        return HistoryResult(equity_df=equity_df)

    dates = equity_df["date"].to_numpy()
    equity_vals = equity_df["equity"].to_numpy(dtype=float)

    windows: list[WindowResult] = []
    for i in range(n - config.max_trading_days):
        equity_series = pd.Series(equity_vals[i : i + window_size])
        result = evaluate_window(equity_series, config)
        windows.append(
            WindowResult(
                start_date=pd.Timestamp(dates[i]),
                end_date=pd.Timestamp(dates[i + result.end_day]),
                result=result,
            )
        )

    return HistoryResult(equity_df=equity_df, windows=windows)
