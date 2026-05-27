from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass
class ChallengeConfig:
    name: str
    account_size: float
    profit_target_pct: float
    max_drawdown_pct: float
    daily_drawdown_pct: float
    max_trading_days: int
    min_trading_days: int = 0

    @property
    def profit_target_abs(self) -> float:
        return self.account_size * self.profit_target_pct / 100

    @property
    def max_drawdown_abs(self) -> float:
        return self.account_size * self.max_drawdown_pct / 100

    @property
    def daily_drawdown_abs(self) -> float:
        return self.account_size * self.daily_drawdown_pct / 100


_Status = Literal["PASS", "FAIL_MAX_DD", "FAIL_DAILY_DD", "FAIL_TIME"]


@dataclass
class SimResult:
    status: _Status
    end_day: int
    peak_equity: float
    final_equity: float
    max_dd_pct: float
    max_daily_dd_pct: float


def evaluate_window(equity_series: pd.Series, config: ChallengeConfig) -> SimResult:
    arr = equity_series.to_numpy(dtype=float)
    n = len(arr)
    initial = arr[0]

    running_peak = np.maximum.accumulate(arr)
    dd_pct = (arr - running_peak) / running_peak * 100

    daily_pct = np.empty(n)
    daily_pct[0] = 0.0
    daily_pct[1:] = (arr[1:] - arr[:-1]) / arr[:-1] * 100

    profit_pct = (arr - initial) / initial * 100
    days = np.arange(n)

    daily_breach = np.where((days >= 1) & (daily_pct < -config.daily_drawdown_pct))[0]
    max_dd_breach = np.where((days >= 1) & (dd_pct < -config.max_drawdown_pct))[0]
    time_breach = np.where(
        (days > config.max_trading_days) & (profit_pct < config.profit_target_pct)
    )[0]
    pass_breach = np.where(
        (days >= config.min_trading_days) & (profit_pct >= config.profit_target_pct)
    )[0]

    day_daily = int(daily_breach[0]) if len(daily_breach) else n
    day_max_dd = int(max_dd_breach[0]) if len(max_dd_breach) else n
    day_time = int(time_breach[0]) if len(time_breach) else n
    day_pass = int(pass_breach[0]) if len(pass_breach) else n

    min_day = min(day_daily, day_max_dd, day_time, day_pass)

    if min_day >= n:
        end_day = n - 1
        status: _Status = "FAIL_TIME"
    elif min_day == day_daily:
        end_day = day_daily
        status = "FAIL_DAILY_DD"
    elif min_day == day_max_dd:
        end_day = day_max_dd
        status = "FAIL_MAX_DD"
    elif min_day == day_time:
        end_day = day_time
        status = "FAIL_TIME"
    else:
        end_day = day_pass
        status = "PASS"

    return SimResult(
        status=status,
        end_day=end_day,
        peak_equity=float(running_peak[end_day]),
        final_equity=float(arr[end_day]),
        max_dd_pct=float(dd_pct[: end_day + 1].min()),
        max_daily_dd_pct=float(daily_pct[1 : end_day + 1].min()) if end_day >= 1 else 0.0,
    )
