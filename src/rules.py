from __future__ import annotations

from dataclasses import dataclass


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


@dataclass
class RuleResult:
    passed: bool
    breach_day: int | None
    breach_reason: str | None
    reached_target: bool
    trading_days: int


def evaluate_rules(daily_pnl: list[float], config: ChallengeConfig) -> RuleResult:
    ...
