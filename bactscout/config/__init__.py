"""Packaged default configuration resources."""

import os
from importlib.resources import files
from pathlib import Path

DEFAULT_CONFIG = str(files(__package__).joinpath("bactscout_config.yml"))
DEFAULT_LONG_CONFIG = str(files(__package__).joinpath("bactscout_long_config.yml"))
DEFAULT_METRICS_FILE = str(files(__package__).joinpath("filtered_metrics.csv"))


def default_database_destination() -> Path:
    repo_database = Path(__file__).resolve().parents[2] / "bactscout_dbs"
    if (repo_database.parent / "pixi.toml").exists() and repo_database.exists():
        return repo_database

    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix:
        return Path(conda_prefix) / "share" / "bactscout" / "db"

    from platformdirs import user_data_path

    return user_data_path("bactscout") / "db"
