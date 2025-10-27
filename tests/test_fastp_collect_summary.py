"""
End-to-end tests for fastp metrics extraction and summary collection.

This test suite verifies the complete pipeline:
1. Raw fastp JSON data contains expected fields
2. Fastp metrics are correctly extracted
3. Metrics are properly processed with correct status determination
4. Summary collection pipeline works end-to-end

Uses anonymized sample data in tests/sample_output_data/
"""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from bactscout.summary import summary_dir
from bactscout.thread import get_fastp_results, handle_fastp_results


@pytest.fixture
def sample_output_dir():
    """Return the path to test sample output data."""
    return Path(__file__).parent / "sample_output_data"


@pytest.fixture
def sample_ids(sample_output_dir):
    """Return list of anonymized sample IDs."""
    samples = sorted([d.name for d in sample_output_dir.iterdir() if d.is_dir()])
    return samples


@pytest.fixture
def fastp_config():
    """Return fastp processing configuration."""
    return {
        "q30_pass_threshold": 0.80,  # 80%
        "read_length_pass_threshold": 100,  # 100bp
    }


class TestFastpRawDataVerification:
    """Test Phase 1: Verify raw fastp JSON data is valid."""

    def test_sample_directories_exist(self, sample_output_dir):
        """Verify sample directories exist."""
        assert sample_output_dir.exists(), f"Sample dir not found: {sample_output_dir}"
        samples = list(sample_output_dir.iterdir())
        assert len(samples) >= 5, f"Expected at least 5 samples, found {len(samples)}"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_fastp_json_exists(self, sample_output_dir, sample_id):
        """Verify fastp.json files exist for each sample."""
        fastp_files = list((sample_output_dir / sample_id).glob("*fastp.json"))
        assert len(fastp_files) > 0, f"No fastp.json found in {sample_id}"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_fastp_json_structure(self, sample_output_dir, sample_id):
        """Verify fastp JSON has expected structure."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        with open(fastp_file, "r", encoding="utf-8") as f:
            fastp_json = json.load(f)

        assert "summary" in fastp_json, "Missing 'summary' in fastp JSON"
        assert (
            "after_filtering" in fastp_json["summary"]
        ), "Missing 'after_filtering' in summary"

        after_filtering = fastp_json["summary"]["after_filtering"]
        assert "total_reads" in after_filtering, "Missing 'total_reads'"
        assert "read1_mean_length" in after_filtering, "Missing 'read1_mean_length'"
        assert "read2_mean_length" in after_filtering, "Missing 'read2_mean_length'"
        assert "q30_rate" in after_filtering, "Missing 'q30_rate'"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_fastp_metrics_values_valid(self, sample_output_dir, sample_id):
        """Verify fastp metrics have valid non-zero values."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        with open(fastp_file, "r", encoding="utf-8") as f:
            fastp_json = json.load(f)

        after_filtering = fastp_json["summary"]["after_filtering"]

        # Verify non-zero values
        assert (
            after_filtering.get("total_reads", 0) > 0
        ), f"{sample_id}: total_reads is 0 or missing"
        assert (
            after_filtering.get("read1_mean_length", 0) > 0
        ), f"{sample_id}: read1_mean_length is 0 or missing"
        assert (
            after_filtering.get("read2_mean_length", 0) > 0
        ), f"{sample_id}: read2_mean_length is 0 or missing"
        assert (
            after_filtering.get("q30_rate", 0.0) > 0
        ), f"{sample_id}: q30_rate is 0 or missing"


class TestFastpExtraction:
    """Test Phase 2: Verify fastp metrics are correctly extracted."""

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_extract_fastp_results(self, sample_output_dir, sample_id):
        """Test extraction of fastp metrics using get_fastp_results."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        # Extract using the FIXED function
        extracted = get_fastp_results(fastp_results)

        # Verify all expected fields are present
        assert (
            extracted.get("read_total_reads") is not None
        ), "read_total_reads not extracted"
        assert (
            extracted.get("read1_mean_length") is not None
        ), "read1_mean_length not extracted"
        assert (
            extracted.get("read2_mean_length") is not None
        ), "read2_mean_length not extracted"
        assert extracted.get("read_q30_rate") is not None, "read_q30_rate not extracted"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_extract_fastp_read_lengths(self, sample_output_dir, sample_id):
        """Test that read lengths are correctly extracted (main fix)."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)

        # THE KEY ASSERTIONS FOR THE FIX
        read1_len = extracted.get("read1_mean_length", 0) or 0
        read2_len = extracted.get("read2_mean_length", 0) or 0

        assert (
            read1_len > 0
        ), f"{sample_id}: read1_mean_length should be > 0, got {read1_len}"
        assert (
            read2_len > 0
        ), f"{sample_id}: read2_mean_length should be > 0, got {read2_len}"
        assert (
            read1_len <= 1000
        ), f"{sample_id}: read1_mean_length unrealistic: {read1_len}"
        assert (
            read2_len <= 1000
        ), f"{sample_id}: read2_mean_length unrealistic: {read2_len}"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_extract_all_fastp_fields(self, sample_output_dir, sample_id):
        """Test extraction of all fastp fields."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)

        # Verify all 9 expected fields are present
        expected_fields = [
            "read_total_reads",
            "read_total_bases",
            "read_q20_bases",
            "read_q30_bases",
            "read_q20_rate",
            "read_q30_rate",
            "read1_mean_length",
            "read2_mean_length",
        ]

        for field in expected_fields:
            assert field in extracted, f"{sample_id}: Missing field {field}"
            assert extracted[field] is not None, f"{sample_id}: Field {field} is None"


class TestFastpProcessing:
    """Test Phase 3: Verify fastp metrics are correctly processed."""

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_handle_fastp_results(self, sample_output_dir, sample_id, fastp_config):
        """Test processing of fastp results with handle_fastp_results."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)
        handled = handle_fastp_results(extracted.copy(), fastp_config)

        # Verify status fields are added
        assert "read_length_status" in handled, "read_length_status not set"
        assert "read_q30_status" in handled, "read_q30_status not set"
        assert "read_length_message" in handled, "read_length_message not set"
        assert "read_q30_message" in handled, "read_q30_message not set"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_read_length_status_passed(
        self, sample_output_dir, sample_id, fastp_config
    ):
        """Test that read length status is PASSED when above threshold."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)
        handled = handle_fastp_results(extracted.copy(), fastp_config)

        # All test samples should have read lengths > 100bp
        assert (
            handled.get("read_length_status") == "PASSED"
        ), f"{sample_id}: Expected PASSED status, got {handled.get('read_length_status')}"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_q30_status_passed(self, sample_output_dir, sample_id, fastp_config):
        """Test that Q30 status is PASSED when above threshold."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)
        handled = handle_fastp_results(extracted.copy(), fastp_config)

        # All test samples should have Q30 rate > 80%
        assert (
            handled.get("read_q30_status") == "PASSED"
        ), f"{sample_id}: Expected PASSED status, got {handled.get('read_q30_status')}"

    @pytest.mark.parametrize(
        "sample_id",
        ["sample_001", "sample_002", "sample_003", "sample_004", "sample_005"],
    )
    def test_extraction_consistency(self, sample_output_dir, sample_id, fastp_config):
        """Test that extraction and processing are consistent."""
        fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

        with open(fastp_file, "r", encoding="utf-8") as f:
            fastp_json = json.load(f)

        after_filtering = fastp_json["summary"]["after_filtering"]

        fastp_results = {
            "status": "success",
            "json_report": str(fastp_file),
            "sample": sample_id,
        }

        extracted = get_fastp_results(fastp_results)

        # Verify extracted values match raw JSON
        assert (
            extracted["read_total_reads"] == after_filtering["total_reads"]
        ), f"{sample_id}: total_reads mismatch"
        assert (
            extracted["read1_mean_length"] == after_filtering["read1_mean_length"]
        ), f"{sample_id}: read1_mean_length mismatch"
        assert (
            extracted["read2_mean_length"] == after_filtering["read2_mean_length"]
        ), f"{sample_id}: read2_mean_length mismatch"


class TestSummaryCollection:
    """Test Phase 4: Verify summary collection pipeline."""

    def test_summary_collection(self, sample_output_dir):
        """Test that summary_dir can collect samples successfully."""
        tmp_csv = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as tmp:
                tmp_csv = tmp.name

            # Collect summary
            summary_dir(sample_output_dir, tmp_csv)

            # Verify file was created
            assert Path(tmp_csv).exists(), f"Summary file not created: {tmp_csv}"

            # Verify file has content
            with open(tmp_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) > 0, "Summary file is empty"

        finally:
            if tmp_csv and Path(tmp_csv).exists():
                Path(tmp_csv).unlink()

    def test_summary_has_fastp_columns(self, sample_output_dir):
        """Test that summary has fastp-related columns."""
        tmp_csv = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as tmp:
                tmp_csv = tmp.name

            summary_dir(sample_output_dir, tmp_csv)

            with open(tmp_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if rows:
                first_row = rows[0]
                fastp_cols = [col for col in first_row.keys() if "read" in col.lower()]

                assert len(fastp_cols) > 0, "No fastp columns found in summary"

                # Check for specific columns
                expected_cols = [
                    "read_length_status",
                    "read_q30_status",
                    "read1_mean_length",
                    "read2_mean_length",
                ]
                for col in expected_cols:
                    assert col in first_row, f"Missing expected column: {col}"

        finally:
            if tmp_csv and Path(tmp_csv).exists():
                Path(tmp_csv).unlink()

    def test_summary_sample_count(self, sample_output_dir):
        """Test that summary contains all samples."""
        tmp_csv = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as tmp:
                tmp_csv = tmp.name

            summary_dir(sample_output_dir, tmp_csv)

            with open(tmp_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            # Should have at least 5 samples
            assert len(rows) >= 5, f"Expected at least 5 samples, got {len(rows)}"

        finally:
            if tmp_csv and Path(tmp_csv).exists():
                Path(tmp_csv).unlink()


class TestEndToEnd:
    """Test complete end-to-end pipeline."""

    def test_all_samples_pass_extraction(
        self, sample_output_dir, sample_ids, fastp_config
    ):
        """Test that all samples extract and pass status checks."""
        passed_count = 0

        for sample_id in sample_ids:
            fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

            fastp_results = {
                "status": "success",
                "json_report": str(fastp_file),
                "sample": sample_id,
            }

            extracted = get_fastp_results(fastp_results)
            handled = handle_fastp_results(extracted.copy(), fastp_config)

            if (
                handled.get("read_length_status") == "PASSED"
                and handled.get("read_q30_status") == "PASSED"
            ):
                passed_count += 1

        # All test samples should pass
        assert (
            passed_count >= 5
        ), f"Expected all 5 samples to pass, got {passed_count}/5"

    def test_extraction_pipeline_complete(self, sample_output_dir, sample_ids):
        """Test that entire extraction pipeline runs without errors."""
        config = {
            "q30_pass_threshold": 0.80,
            "read_length_pass_threshold": 100,
        }

        for sample_id in sample_ids:
            fastp_file = list((sample_output_dir / sample_id).glob("*fastp.json"))[0]

            # Should not raise any exceptions
            fastp_results = {
                "status": "success",
                "json_report": str(fastp_file),
                "sample": sample_id,
            }

            extracted = get_fastp_results(fastp_results)
            assert extracted is not None

            handled = handle_fastp_results(extracted.copy(), config)
            assert handled is not None
