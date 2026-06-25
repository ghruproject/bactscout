"""Console-script wrapper for the source-level BactScout CLI."""

import importlib.util
from pathlib import Path


def _load_source_app():
    script_path = Path(__file__).resolve().parent.parent / "bactscout.py"
    spec = importlib.util.spec_from_file_location("_bactscout_source_cli", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load BactScout CLI from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


app = _load_source_app()
