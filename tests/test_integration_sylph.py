"""Integration tests for StringMLST with real downloaded data."""

from pathlib import Path

import pytest

from bactscout.software.run_sylph import run_command
from tests.util_test import download_fastq_files

# Use a cache directory that persists across test runs
CACHE_DIR = Path(__file__).parent / "cached_fastqs"
R1_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R1.fastq.gz"
R2_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R2.fastq.gz"
R1_FILE = "Sample_25067cebsemb_R1.fastq.gz"
R2_FILE = "Sample_25067cebsemb_R2.fastq.gz"


def test_sylph_real_download(tmp_path):
    """
    Integration test: Download real FASTQ files and run Sylph.

    Uses cached downloads to avoid re-downloading on subsequent runs.
    Mark as slow/integration to skip in regular test runs.

    Run with: pytest -m slow or pytest -m integration
    """
    # Download/use cached FASTQ files
    r1, r2 = download_fastq_files(CACHE_DIR, R1_FILE, R1_URL, R2_FILE, R2_URL)

    # Verify files exist and have content
    assert r1.exists(), f"R1 file not found: {r1}"
    assert r2.exists(), f"R2 file not found: {r2}"
    assert r1.stat().st_size > 0, "R1 file is empty"
    assert r2.stat().st_size > 0, "R2 file is empty"

    # Find species database
    project_root = Path(__file__).resolve().parent.parent

    config = {
        "bactscout_dbs_path": str(project_root / "bactscout_dbs"),
        "sylph_db": "gtdb-r226-c1000-dbv1.syldb",
    }
    db_path = Path(config["bactscout_dbs_path"]) / config["sylph_db"]

    if not db_path.exists():
        pytest.skip(f"Species database not found at {db_path}")

    output_dir = tmp_path / "sylph_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run Sylph on the downloaded files
    result = run_command(
        str(r1), str(r2), str(output_dir), config, message=True, threads=2
    )
    # Verify results
    assert "sylph_report" in result

    # Verify output file exists and has content
    report_file = Path(result["sylph_report"])
    assert report_file.exists(), f"Sylph report not found: {report_file}"
    assert report_file.stat().st_size > 0, "Sylph report file is empty"

    # Read and verify Sylph results
    with open(report_file, encoding="utf-8") as f:
        lines = f.readlines()
        print(lines)
        assert len(lines) >= 1, "Sylph report should have at least a header"

        # Check header exists
        if len(lines) > 0:
            header = lines[0].strip()
            assert len(header) > 0, "Sylph report header is empty"

        print(f"Sylph report has {len(lines)} lines")
        if len(lines) > 1:
            print(f"First result line:\n{lines[1]}")


def test_cached_files_exist():
    """Test that verifies cached files are available (or can be downloaded)."""
    try:
        r1, r2 = download_fastq_files(CACHE_DIR, R1_FILE, R1_URL, R2_FILE, R2_URL)
        assert r1.exists()
        assert r2.exists()
        print(f"Cache directory: {CACHE_DIR}")
        print(f"R1 size: {r1.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"R2 size: {r2.stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        pytest.skip(f"Could not access cached files: {e}")
