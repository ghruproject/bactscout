import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.slow
def test_sample_data_qc(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    sample_dir = project_root / "sample_data"
    assert sample_dir.exists(), f"sample_data directory missing at {sample_dir}"

    output_dir = tmp_path / "qc_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(project_root / "bactscout.py"),
        "qc",
        str(sample_dir),
        "--output",
        str(output_dir),
        "--threads",
        "1",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)

    assert (
        result.returncode == 0
    ), f"Command failed with:\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"

    generated_files = list(output_dir.rglob("*.csv"))
    assert generated_files, f"QC run produced no output files in {output_dir}"
    assert any(
        p.suffix == ".csv" for p in generated_files
    ), "Expected CSV report not found"
