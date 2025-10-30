"""Integration test for collect_sample function with real sample data."""

import json
from pathlib import Path

import pytest

from bactscout.collect import collect_sample
from tests.util_test import download_fastq_files

# Use a cache directory that persists across test runs
CACHE_DIR = Path(__file__).parent / "cached_fastqs"
R1_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R1.fastq.gz"
R2_URL = "https://pub-e661bf7ded744bd79c156d3a4f4323ef.r2.dev/Sample_25067cebsemb_R2.fastq.gz"
R1_FILE = "Sample_25067cebsemb_R1.fastq.gz"
R2_FILE = "Sample_25067cebsemb_R2.fastq.gz"


@pytest.mark.integration
@pytest.mark.slow
def test_collect_sample_with_sample_data(tmp_path):
    """
    Integration test: Run collect_sample on sample_data files.

    Uses the sample_data directory with real FASTQ files to test
    the complete collection workflow.
    """
    project_root = Path(__file__).resolve().parent.parent
    sample_dir = project_root / "sample_data"

    if not sample_dir.exists():
        pytest.skip(f"sample_data directory not found at {sample_dir}")

    # Find R1 and R2 files in sample_data
    r1_files = list(sample_dir.glob("*_R1.fastq.gz"))
    r2_files = list(sample_dir.glob("*_R2.fastq.gz"))

    if not r1_files or not r2_files:
        pytest.skip(f"No paired FASTQ files found in {sample_dir}")

    r1_file = str(r1_files[0])
    r2_file = str(r2_files[0])

    output_dir = tmp_path / "collect_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Path to config file
    config_file = project_root / "bactscout_config.yml"

    if not config_file.exists():
        pytest.skip(f"Config file not found at {config_file}")

    # Run collect_sample
    try:
        collect_sample(
            read1_file=r1_file,
            read2_file=r2_file,
            output_dir=str(output_dir),
            threads=2,
            config=str(config_file),
            skip_preflight=False,
            report_resources=False,
        )
    except Exception as e:
        pytest.fail(f"collect_sample failed: {e}")

    # Verify output files were created
    output_files = list(output_dir.rglob("*"))
    assert len(output_files) > 0, f"No output files created in {output_dir}"

    print(f"Generated {len(output_files)} output files in {output_dir}")


@pytest.mark.integration
@pytest.mark.slow
def test_collect_sample_with_cache_data(tmp_path):
    """
    Integration test: Run collect_sample on cached FASTQ files.

    Uses the sample_data directory with real FASTQ files to test
    the complete collection workflow.
    """
    r1, r2 = download_fastq_files(CACHE_DIR, R1_FILE, R1_URL, R2_FILE, R2_URL)
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / "bactscout_config.yml"
    output_dir = tmp_path / "collect_output_cache"

    # Run collect_sample
    collect_sample(
        read1_file=r1,
        read2_file=r2,
        output_dir=str(output_dir),
        threads=4,
        config=str(config_file),
        skip_preflight=False,
        report_resources=True,
    )

    # Verify output files were created
    output_files = list(output_dir.rglob("*"))
    assert len(output_files) > 0, f"No output files created in {output_dir}"
    # Check if resources are reported in output Sample_25067cebsemb_summary.csv  ; resource_memory_peak_mb > 0
    summary_file = (
        output_dir / "Sample_25067cebsemb" / "Sample_25067cebsemb_summary.csv"
    )
    assert summary_file.exists(), f"Summary file not found: {summary_file}"
    with open(summary_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "resource_memory_peak_mb" in content, "Resource memory peak not reported"
        lines = content.splitlines()
        header = lines[0].split(",")
        mem_index = header.index("resource_memory_peak_mb")
        data = lines[1].split(",")
        peak_mem = float(data[mem_index])
        assert peak_mem > 0, "Peak memory usage should be greater than 0"
    mlst_file = output_dir / "Sample_25067cebsemb" / "mlst.tsv"
    assert mlst_file.exists(), f"MLST file not found: {mlst_file}"
    assert mlst_file.stat().st_size > 0, "MLST file is empty"

    # Check FastP JSON report
    fastp_json = output_dir / "Sample_25067cebsemb" / "Sample_25067cebsemb.fastp.json"
    assert fastp_json.exists(), f"FastP JSON report not found: {fastp_json}"
    with open(fastp_json, "r", encoding="utf-8") as f:
        fastp_data = json.load(f)
        assert "summary" in fastp_data, "FastP JSON missing 'summary' key"
        assert (
            "before_filtering" in fastp_data["summary"]
        ), "FastP JSON missing 'before_filtering'"
        total_reads = fastp_data["summary"]["before_filtering"]["total_reads"]
        assert total_reads > 0, f"Expected total_reads > 0, got {total_reads}"
        print(f"FastP total_reads: {total_reads}")

    print(f"Generated {len(output_files)} output files in {output_dir}")


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
