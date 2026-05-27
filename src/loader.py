from __future__ import annotations

import pandas as pd
import yaml

from src.rules import ChallengeConfig

_REQUIRED_CONFIG_FIELDS: frozenset[str] = frozenset({
    "name",
    "account_size",
    "profit_target_pct",
    "max_drawdown_pct",
    "daily_drawdown_pct",
    "max_trading_days",
})

_EQUITY_REQUIRED_COLS: frozenset[str] = frozenset({"date", "equity"})
_TRADES_REQUIRED_COLS: frozenset[str] = frozenset({"ticket", "open_time", "close_time", "profit"})

_DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y%m%d",
    "%d-%m-%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
)


def _parse_date_column(series: pd.Series, source: str) -> pd.Series:
    try:
        parsed = pd.to_datetime(series, format="mixed", dayfirst=False)
        if parsed.notna().all():
            return parsed
    except Exception:
        pass

    for fmt in _DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt, errors="raise")
            if parsed.notna().all():
                return parsed
        except Exception:
            continue

    raise ValueError(
        f"Cannot parse date column in '{source}'. "
        f"Supported formats: {', '.join(_DATE_FORMATS[:5])} (with optional HH:MM:SS)."
    )


def _assert_columns(actual: list[str], required: frozenset[str], source: str) -> None:
    missing = required - set(actual)
    if missing:
        raise ValueError(
            f"'{source}' is missing required columns: {sorted(missing)}. "
            f"Found columns: {sorted(actual)}."
        )


def load_config(path: str) -> ChallengeConfig:
    try:
        with open(path) as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError:
        raise ValueError(f"Config file not found: '{path}'.")
    except yaml.YAMLError as exc:
        raise ValueError(f"Failed to parse YAML config '{path}': {exc}.")

    if not isinstance(data, dict):
        raise ValueError(f"Config file '{path}' must contain a YAML mapping at the top level.")

    missing = _REQUIRED_CONFIG_FIELDS - data.keys()
    if missing:
        raise ValueError(
            f"Config '{path}' is missing required fields: {sorted(missing)}."
        )

    try:
        return ChallengeConfig(
            name=str(data["name"]),
            account_size=float(data["account_size"]),
            profit_target_pct=float(data["profit_target_pct"]),
            max_drawdown_pct=float(data["max_drawdown_pct"]),
            daily_drawdown_pct=float(data["daily_drawdown_pct"]),
            max_trading_days=int(data["max_trading_days"]),
            min_trading_days=int(data.get("min_trading_days", 0)),
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Config '{path}' contains an invalid field value: {exc}.")


def load_equity_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise ValueError(f"Equity CSV not found: '{path}'.")
    except Exception as exc:
        raise ValueError(f"Failed to read equity CSV '{path}': {exc}.")

    _assert_columns(df.columns.tolist(), _EQUITY_REQUIRED_COLS, path)

    df = df[["date", "equity"]].copy()

    df["date"] = _parse_date_column(df["date"], path)

    if df["date"].isna().any():
        raise ValueError(f"Equity CSV '{path}': 'date' column contains unparseable values.")

    try:
        df["equity"] = pd.to_numeric(df["equity"], errors="raise")
    except Exception:
        raise ValueError(f"Equity CSV '{path}': 'equity' column contains non-numeric values.")

    if df["equity"].isna().any():
        raise ValueError(f"Equity CSV '{path}': 'equity' column contains missing values.")

    return df.sort_values("date").reset_index(drop=True)


def load_trades_csv(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        raise ValueError(f"Trades CSV not found: '{path}'.")
    except Exception as exc:
        raise ValueError(f"Failed to read trades CSV '{path}': {exc}.")

    _assert_columns(df.columns.tolist(), _TRADES_REQUIRED_COLS, path)

    df = df[["ticket", "open_time", "close_time", "profit"]].copy()

    df["open_time"] = _parse_date_column(df["open_time"], path)
    df["close_time"] = _parse_date_column(df["close_time"], path)

    if df["open_time"].isna().any():
        raise ValueError(f"Trades CSV '{path}': 'open_time' column contains unparseable values.")
    if df["close_time"].isna().any():
        raise ValueError(f"Trades CSV '{path}': 'close_time' column contains unparseable values.")

    try:
        df["profit"] = pd.to_numeric(df["profit"], errors="raise")
    except Exception:
        raise ValueError(f"Trades CSV '{path}': 'profit' column contains non-numeric values.")

    if df["profit"].isna().any():
        raise ValueError(f"Trades CSV '{path}': 'profit' column contains missing values.")

    return df.sort_values("close_time").reset_index(drop=True)


def trades_to_equity(trades_df: pd.DataFrame, initial_balance: float) -> pd.DataFrame:
    if trades_df.empty:
        raise ValueError("trades_df is empty; cannot reconstruct an equity curve.")

    _assert_columns(trades_df.columns.tolist(), frozenset({"close_time", "profit"}), "trades_df")

    daily = trades_df.copy()
    daily["date"] = daily["close_time"].dt.normalize()

    daily_pnl = daily.groupby("date", as_index=False)["profit"].sum()
    daily_pnl = daily_pnl.sort_values("date")

    full_range = pd.date_range(daily_pnl["date"].iloc[0], daily_pnl["date"].iloc[-1], freq="D")
    daily_pnl = (
        daily_pnl.set_index("date")
        .reindex(full_range, fill_value=0.0)
        .rename_axis("date")
        .reset_index()
    )

    daily_pnl["equity"] = initial_balance + daily_pnl["profit"].cumsum()
    return daily_pnl[["date", "equity"]].reset_index(drop=True)
