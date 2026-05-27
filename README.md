# prop-firm-simulator

Backtest a trading strategy against prop firm challenge rules using Monte Carlo resampling or sliding-window historical analysis.

---

## Features

- **Monte Carlo**: bootstrap-resamples daily returns N times; each run is evaluated against the full rule set
- **Historical**: slides a challenge-length window across the equity curve; every start date gets a pass/fail verdict
- Rule engine: daily drawdown, max drawdown from peak, profit target, min/max trading days — evaluated in priority order per day
- Trades CSV support: reconstructs daily equity from raw trade history
- Interactive HTML reports via Plotly (dark theme, no server required)
- Rich terminal output: progress bar, result tables

---

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10+ recommended. Tested on 3.9.6.

---

## Quick Start

**Monte Carlo — 10 000 simulated challenges:**

```bash
python simulate.py run \
  --equity  examples/sample_equity.csv \
  --config  presets/ftmo_100k.yaml \
  --out     report_mc.html \
  --runs    10000
```

```
╭─────────────────────────────────────╮
│ FTMO 100k — 10,000 Monte Carlo runs │
├──────────────────────┬──────────────┤
│ Pass Rate            │      38.42%  │
├──────────────────────┼──────────────┤
│ PASS                 │      38.42%  │
│ FAIL_TIME            │      43.17%  │
│ FAIL_MAX_DD          │      12.51%  │
│ FAIL_DAILY_DD        │       5.90%  │
├──────────────────────┼──────────────┤
│ Avg Days (Pass)      │        18.3  │
│ Avg Days (Fail)      │        22.7  │
╰──────────────────────┴──────────────╯
Report saved: report_mc.html
```

**Historical — sliding window across full equity history:**

```bash
python simulate.py history \
  --equity  examples/sample_equity.csv \
  --config  presets/ftmo_100k.yaml \
  --out     report_hist.html
```

```
╭────────────────────────────────────────────╮
│ FTMO 100k — Historical Windows (30-day)    │
├──────────────────┬────────┬────────────────┤
│ Status           │  Count │  Share         │
├──────────────────┼────────┼────────────────┤
│ Total            │    170 │  100.0%        │
│ PASS             │     68 │   40.0%        │
│ FAIL_MAX_DD      │     22 │   12.9%        │
│ FAIL_DAILY_DD    │      9 │    5.3%        │
│ FAIL_TIME        │     71 │   41.8%        │
╰──────────────────┴────────┴────────────────╯
Report saved: report_hist.html
```

**Load from a trades CSV instead of an equity CSV:**

```bash
python simulate.py run \
  --equity  examples/sample_trades.csv \
  --config  presets/ftmo_100k.yaml \
  --out     report_mc.html \
  --trades
```

---

## Input CSV Formats

### Equity curve

| column | type | description |
|--------|------|-------------|
| `date` | date | trading day (auto-detected format) |
| `equity` | float | account balance at end of day |

```
date,equity
2024-01-02,10000.00
2024-01-03,10082.57
2024-01-04,10082.60
```

Accepted date formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY`, `YYYYMMDD`, `DD-MM-YYYY` (with optional `HH:MM:SS`).

### Trades

| column | type | description |
|--------|------|-------------|
| `ticket` | int | unique trade ID |
| `open_time` | datetime | trade entry timestamp |
| `close_time` | datetime | trade exit timestamp |
| `profit` | float | realised P&L in account currency |

```
ticket,open_time,close_time,profit
200026,2024-01-02 10:00:00,2024-01-04 05:00:00,68.76
200029,2024-01-12 11:00:00,2024-01-14 05:00:00,302.41
200023,2024-01-11 13:00:00,2024-01-14 08:00:00,-177.50
```

Equity is reconstructed by summing `profit` per calendar day and computing the cumulative balance from `account_size`.

---

## Config YAML Reference

```yaml
name: "FTMO 100k"             # str     — label shown in reports
account_size: 100000          # float   — starting balance (account currency)
profit_target_pct: 10.0       # float   — profit target as % of account_size
max_drawdown_pct: 10.0        # float   — max total drawdown from peak as %
daily_drawdown_pct: 5.0       # float   — max single-day loss as %
max_trading_days: 30          # int     — window length; challenge fails beyond this
min_trading_days: 4           # int     — target cannot be claimed before this day (default: 0)
```

All percentage fields are evaluated against `account_size` (e.g. `daily_drawdown_pct: 5.0` on a 100 000 account = $5 000 daily limit).

### Rule evaluation order (per day)

```
1. daily_dd   = (equity[d] − equity[d−1]) / equity[d−1] × 100
               if < −daily_drawdown_pct  →  FAIL_DAILY_DD

2. peak_dd    = (equity[d] − running_peak) / running_peak × 100
               if < −max_drawdown_pct    →  FAIL_MAX_DD

3. if day > max_trading_days and profit < target  →  FAIL_TIME

4. if profit ≥ target and day ≥ min_trading_days  →  PASS
```

---

## Included Presets

| File | Account | Target | Max DD | Daily DD | Days |
|------|--------:|-------:|-------:|---------:|------|
| `presets/ftmo_100k.yaml` | $100 000 | 10% | 10% | 5% | 4 – 30 |
| `presets/ftmo_200k.yaml` | $200 000 | 10% | 10% | 5% | 4 – 30 |
| `presets/generic.yaml`   |  $50 000 |  8% |  8% | 4% | 5 – 60 |

---

## Output

Both commands write a self-contained HTML file (Plotly CDN, no backend required).

### Monte Carlo report (`run`)

```
┌─ Fig 1 ── Sampled Equity Curves ──────────────────────────────┐
│                                                               │
│  equity  ╭───────── target ─────────────────────             │
│  11 000 ─┤       ╭──╯  ╭────────╮   ←  PASS  (green)        │
│          │  ╭────╯     │        ╰──                          │
│  10 000 ─┼──╯──────────┼──── start ─────────────────         │
│          │             ╰───────────────────  FAIL  (red)     │
│   9 000 ─┤                                                   │
│          └────────────────────────────────── trading day     │
└───────────────────────────────────────────────────────────────┘
┌─ Fig 2 ── Final Equity Distribution ──────────────────────────┐
│  count                                                        │
│    ▐██▌                                                       │
│   ▐████▌  ▐█▌    ← vertical line at profit target            │
│  ▐██████▌▐███▌▐█▌                                            │
│  └──────────────────────────────────────── final equity      │
└───────────────────────────────────────────────────────────────┘
┌─ Fig 3 ── Outcome Breakdown ──────────────────────────────────┐
│  PASS          ████████████████████████  38.4%               │
│  FAIL_TIME     ████████████████████████████  43.2%           │
│  FAIL_MAX_DD   ██████  12.5%                                  │
│  FAIL_DAILY_DD ███  5.9%                                      │
└───────────────────────────────────────────────────────────────┘
```

### History report (`history`)

```
┌─ Full Equity Curve + Window Outcomes ─────────────────────────┐
│  equity                                                       │
│  14k ─┤                    ░░░░░░░░░░░░░░░░░  ← PASS         │
│       │          ▒▒▒▒▒▒▒▒▒░░░░░░░░░░░░░░░░░░░                │
│  10k ─┼──────────────────────────────────────  equity line   │
│       │  ████████▒▒▒▒▒▒▒▒                                    │
│   8k ─┤                                                       │
│       └──────────────────────────────────── date             │
│         ██ FAIL_MAX_DD  ▒▒ FAIL_TIME  ░░ PASS                │
└───────────────────────────────────────────────────────────────┘
```

Each coloured band represents a merged run of consecutive challenge windows with the same outcome. Hovering over a band shows start date, end date, worst drawdown, and final equity for that window group.

| Status | Colour |
|--------|--------|
| `PASS` | green `rgba(0,200,100,0.15)` |
| `FAIL_MAX_DD` | red `rgba(220,50,50,0.15)` |
| `FAIL_DAILY_DD` | orange `rgba(255,140,0,0.15)` |
| `FAIL_TIME` | grey `rgba(120,120,120,0.15)` |

---

## Roadmap

- **Multi-phase challenges** — chain Phase 1 → Phase 2 → funded account rules in a single simulation
- **Firm comparison** — run the same equity curve against multiple config files and rank by pass rate
- **Sensitivity analysis** — sweep a parameter (e.g. `daily_drawdown_pct` from 3% to 6%) and plot pass-rate curves
- **MT5 live integration** — pull open trade history directly from MetaTrader 5 via `MetaTrader5` Python package

---

## License

MIT
