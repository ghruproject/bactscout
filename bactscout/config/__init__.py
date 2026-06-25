"""Packaged default configuration resources."""

from importlib.resources import files

DEFAULT_CONFIG = str(files(__package__).joinpath("bactscout_config.yml"))
DEFAULT_LONG_CONFIG = str(files(__package__).joinpath("bactscout_long_config.yml"))
DEFAULT_METRICS_FILE = str(files(__package__).joinpath("filtered_metrics.csv"))
