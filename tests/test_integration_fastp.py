from pathlib import Path

import pytest

from bactscout.software.run_fastp import run_command


def test_run_command_real_sample_data(tmp_path):
    """Test run_command with real sample data from sample_data directory."""
    project_root = Path(__file__).resolve().parent.parent
    sample_dir = project_root / "sample_data"

    # Check if sample data exists
    if not sample_dir.exists():
        pytest.skip(f"sample_data directory not found at {sample_dir}")

    # Find FASTQ files in sample_data
    r1_files = list(sample_dir.glob("*_R1.fastq.gz"))
    if not r1_files:
        pytest.skip("No R1 FASTQ files found in sample_data")

    # Use the first sample
    r1 = r1_files[0]
    r2 = r1.parent / r1.name.replace("_R1", "_R2")

    if not r2.exists():
        pytest.skip(f"Matching R2 file not found: {r2}")

    output_dir = tmp_path / "fastp_output"

    # Run the actual command
    result = run_command(str(r1), str(r2), str(output_dir), message=False, threads=1)

    # Verify results
    assert result["status"] == "success"
    assert result["sample"] is not None

    # Check that output files were created
    json_report = Path(result["json_report"])
    html_report = Path(result["html_report"])
    log_file = Path(result["log_file"])

    assert json_report.exists(), f"JSON report not created: {json_report}"
    assert html_report.exists(), f"HTML report not created: {html_report}"
    assert log_file.exists(), f"Log file not created: {log_file}"

    # Verify JSON report has content
    assert json_report.stat().st_size > 0, "JSON report is empty"
