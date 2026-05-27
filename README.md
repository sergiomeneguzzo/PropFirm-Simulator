# prop-firm-simulator

Simulate prop firm challenge outcomes against your trading history using Monte Carlo resampling or sliding-window historical analysis.

## Installation

```bash
pip install -r requirements.txt
```

## Commands

### `run` — Monte Carlo simulation

Resamples daily returns from your equity curve and runs N independent challenge simulations.

```bash
python simulate.py run \
  --equity examples/sample_equity.csv \
  --config presets/ftmo_100k.yaml \
  --out report.html \
  --runs 10000
```

### `history` — Sliding window historical analysis

Walks a window of `max_trading_days` across your full equity history and evaluates each window against the firm rules.

```bash
python simulate.py history \
  --equity examples/sample_equity.csv \
  --config presets/ftmo_100k.yaml \
  --out report.html
```

## Options

| Option | Commands | Description |
|--------|----------|-------------|
| `--equity` | both | Path to equity curve CSV (`date`, `equity` columns) |
| `--config` | both | Path to YAML firm config file |
| `--out` | both | Output HTML report path |
| `--runs` | `run` only | Monte Carlo iterations (default: 10000) |

## Presets

| File | Account | Daily Loss | Total Loss | Target |
|------|---------|------------|------------|--------|
| `presets/ftmo_100k.yaml` | $100,000 | 5% | 10% | 10% |
| `presets/ftmo_200k.yaml` | $200,000 | 5% | 10% | 10% |
| `presets/generic.yaml` | $50,000 | 4% | 8% | 8% |

## Equity CSV format

```csv
date,equity
2024-01-02,100000.00
2024-01-03,100320.50
```

## Project structure

```
simulate.py        CLI entry point
src/
  rules.py         FirmConfig dataclass + rule evaluation
  loader.py        CSV and YAML loaders
  engine.py        Monte Carlo and historical analysis engines
  report.py        HTML report generation
presets/           Built-in firm configs
examples/          Sample input files
tests/             Test suite
```
