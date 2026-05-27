from __future__ import annotations

import pandas as pd
import pytest

from src.loader import load_equity_csv, trades_to_equity


def test_load_equity_csv(tmp_path: pytest.TempPathFactory) -> None:
    csv = tmp_path / "equity.csv"
    csv.write_text("date,equity\n2024-01-01,10000.00\n2024-01-02,10100.50\n2024-01-03,10250.75\n")

    df = load_equity_csv(str(csv))

    assert list(df.columns) == ["date", "equity"]
    assert len(df) == 3
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.api.types.is_float_dtype(df["equity"])
    assert df["equity"].iloc[0] == pytest.approx(10_000.00)
    assert df["date"].iloc[0] == pd.Timestamp("2024-01-01")


def test_load_equity_bad_columns(tmp_path: pytest.TempPathFactory) -> None:
    csv = tmp_path / "bad.csv"
    csv.write_text("timestamp,value\n2024-01-01,10000\n")

    with pytest.raises(ValueError, match="missing required columns"):
        load_equity_csv(str(csv))


def test_trades_to_equity() -> None:
    trades = pd.DataFrame(
        {
            "ticket": [1, 2, 3, 4, 5],
            "open_time": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]
            ),
            "close_time": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]
            ),
            "profit": [100.0, -50.0, 200.0, 75.0, -30.0],
        }
    )

    df = trades_to_equity(trades, initial_balance=10_000.0)

    assert list(df.columns) == ["date", "equity"]
    assert len(df) == 4
    assert df["equity"].iloc[0] == pytest.approx(10_100.0)
    assert df["equity"].iloc[1] == pytest.approx(10_250.0)
    assert df["equity"].iloc[2] == pytest.approx(10_325.0)
    assert df["equity"].iloc[3] == pytest.approx(10_295.0)
