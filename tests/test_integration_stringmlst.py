"""Integration tests for StringMLST with real downloaded data."""

from pathlib import Path

import pytest

from bactscout.software.run_stringmlst import run_command
from tests.util_test import download_fastq_files

# Use a cache directory that persists across test runs
CACHE_DIR = Path(__file__).parent / "cached_fastqs"
R1_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R1.fastq.gz"
R2_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R2.fastq.gz"
R1_FILE = "Sample_25067cebsemb_R1.fastq.gz"
R2_FILE = "Sample_25067cebsemb_R2.fastq.gz"


def test_stringmlst_real_download(tmp_path):
    """
    Integration test: Download real FASTQ files and run StringMLST.

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
    db_dir = project_root / "bactscout_dbs" / "klebsiella_pneumoniae"

    if not db_dir.exists():
        pytest.skip(f"Species database not found at {db_dir}")

    output_dir = tmp_path / "stringmlst_output"

    # Run StringMLST on the downloaded files
    result = run_command(
        str(r1), str(r2), str(db_dir), str(output_dir), message=True, threads=2
    )

    # Verify results
    assert result["sample_name"] is not None
    assert "stringmlst_results" in result

    # Check output directory was created
    assert Path(result["output_dir"]).exists()

    # Check if there was an error first
    if "error" in result.get("stringmlst_results", {}):
        error_msg = result["stringmlst_results"]["error"]
        pytest.fail(f"StringMLST execution failed: {error_msg}")

    # Verify output file exists and has content
    output_file = Path(result["output_dir"]) / "mlst.tsv"
    if output_file.exists():
        assert output_file.stat().st_size > 0, "MLST output file is empty"

        # Read and verify MLST results
        with open(output_file, encoding="utf-8") as f:
            lines = f.readlines()
            assert (
                len(lines) >= 2
            ), "MLST output should have header and at least one result"

            # Check header
            header = lines[0].strip()
            assert "Sample" in header or "ST" in header, "Expected MLST header columns"

            print(f"MLST results:\n{lines[1]}")
    else:
        pytest.fail("MLST output file not created and no error reported")


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
