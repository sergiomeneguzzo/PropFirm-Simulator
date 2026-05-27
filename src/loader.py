from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from src.rules import FirmConfig


def load_equity_csv(path: Path) -> pd.DataFrame:
    ...


def load_config_yaml(path: Path) -> FirmConfig:
    ...
