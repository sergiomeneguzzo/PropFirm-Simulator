from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FirmConfig:
    name: str
    account_size: float
    max_daily_loss_pct: float
    max_total_loss_pct: float
    profit_target_pct: float
    min_trading_days: int
    max_trading_days: int
    trailing_drawdown: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def max_daily_loss_abs(self) -> float:
        return self.account_size * self.max_daily_loss_pct / 100

    @property
    def max_total_loss_abs(self) -> float:
        return self.account_size * self.max_total_loss_pct / 100

    @property
    def profit_target_abs(self) -> float:
        return self.account_size * self.profit_target_pct / 100


@dataclass
class RuleResult:
    passed: bool
    breach_day: int | None
    breach_reason: str | None
    reached_target: bool
    trading_days: int


def evaluate_rules(daily_pnl: list[float], config: FirmConfig) -> RuleResult:
    ...
