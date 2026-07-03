"""Version information for BactScout read QC Pipeline."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re


def _version_from_pyproject() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_section = False
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            project_section = True
            continue
        if project_section and stripped.startswith("["):
            break
        if project_section:
            match = re.match(r'version\s*=\s*"([^"]+)"', stripped)
            if match:
                return match.group(1)
    raise RuntimeError(f"Could not read project version from {pyproject}")


def _version_info(version_string: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version_string)[:3])


try:
    __version__ = _version_from_pyproject()
except (FileNotFoundError, RuntimeError):
    try:
        __version__ = version("bactscout")
    except PackageNotFoundError:
        raise

__version_info__ = _version_info(__version__)
