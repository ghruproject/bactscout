"""Tests for bactscout.thread module - MLST and QC evaluation."""

from unittest import mock

import pytest

from bactscout.thread import (
    blank_sample_results,
    final_status_pass,
    handle_mlst_results,
)


class TestHandleMLSTResults:
    """Tests for the handle_mlst_results function."""

    @pytest.fixture
    def sample_config(self):
        """Create a sample config with MLST species mapping."""
        return {
            "mlst_species": {
                "escherichia_coli": "Escherichia coli",
                "klebsiella_pneumoniae": "Klebsiella pneumoniae",
                "salmonella_enterica": "Salmonella enterica",
            },
            "bactscout_dbs_path": "/path/to/dbs",
        }

    @pytest.fixture
    def sample_final_results(self):
        """Create a blank sample results dictionary."""
        return blank_sample_results("sample_001")

    @pytest.fixture
    def sample_paths(self, tmp_path):
        """Create sample file paths."""
        return {
            "read1": str(tmp_path / "sample_001_R1.fastq.gz"),
            "read2": str(tmp_path / "sample_001_R2.fastq.gz"),
            "output_dir": str(tmp_path / "output"),
        }

    def test_valid_st_results_in_passed_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that valid ST (> 0) results in PASSED status."""
        mlst_result = {
            "stringmlst_results": {
                "ST": "1234",
                "Sample": "sample_001",
                "gapA": "1",
            }
        }

        with mock.patch("bactscout.thread.run_mlst", return_value=mlst_result):
            result = handle_mlst_results(
                sample_final_results,
                sample_config,
                "Escherichia coli",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        assert result["mlst_status"] == "PASSED"
        assert result["mlst_st"] == "1234"
        assert "Valid ST found" in result["mlst_message"]

    def test_zero_st_results_in_warning_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that ST of 0 (invalid/unknown) results in WARNING status."""
        mlst_result = {
            "stringmlst_results": {
                "ST": "0",
                "Sample": "sample_001",
            }
        }

        with mock.patch("bactscout.thread.run_mlst", return_value=mlst_result):
            result = handle_mlst_results(
                sample_final_results,
                sample_config,
                "Escherichia coli",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        assert result["mlst_status"] == "WARNING"
        assert result["mlst_st"] == "0"
        assert "No valid ST found" in result["mlst_message"]

    def test_missing_st_field_results_in_warning_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that missing ST field results in WARNING status."""
        mlst_result = {
            "stringmlst_results": {
                "Sample": "sample_001",
                "gapA": "1",
                # ST field is missing
            }
        }

        with mock.patch("bactscout.thread.run_mlst", return_value=mlst_result):
            result = handle_mlst_results(
                sample_final_results,
                sample_config,
                "Escherichia coli",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        assert result["mlst_status"] == "WARNING"
        assert result["mlst_st"] is None
        assert "No valid ST found" in result["mlst_message"]

    def test_empty_st_field_results_in_warning_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that empty ST field results in WARNING status."""
        mlst_result = {
            "stringmlst_results": {
                "ST": "",
                "Sample": "sample_001",
            }
        }

        with mock.patch("bactscout.thread.run_mlst", return_value=mlst_result):
            result = handle_mlst_results(
                sample_final_results,
                sample_config,
                "Escherichia coli",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        assert result["mlst_status"] == "WARNING"
        assert result["mlst_st"] is None
        assert "No valid ST found" in result["mlst_message"]

    def test_no_mlst_database_results_in_warning_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that species without MLST database results in WARNING status."""
        result = handle_mlst_results(
            sample_final_results,
            sample_config,
            "Unknown species",  # Not in config
            sample_paths["read1"],
            sample_paths["read2"],
            sample_paths["output_dir"],
            message=False,
            threads=1,
        )

        assert result["mlst_status"] == "WARNING"
        assert "No MLST database found" in result["mlst_message"]

    def test_novel_st_results_in_passed_status(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that novel ST (high number) results in PASSED status."""
        mlst_result = {
            "stringmlst_results": {
                "ST": "99999",
                "Sample": "sample_001",
            }
        }

        with mock.patch("bactscout.thread.run_mlst", return_value=mlst_result):
            result = handle_mlst_results(
                sample_final_results,
                sample_config,
                "Escherichia coli",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        assert result["mlst_status"] == "PASSED"
        assert result["mlst_st"] == "99999"
        assert "Valid ST found" in result["mlst_message"]

    def test_species_name_mapping_with_underscores(
        self, sample_config, sample_final_results, sample_paths
    ):
        """Test that species names with spaces are correctly mapped to underscored keys."""
        mlst_result = {
            "stringmlst_results": {
                "ST": "5678",
                "Sample": "sample_001",
            }
        }

        with mock.patch(
            "bactscout.thread.run_mlst", return_value=mlst_result
        ) as mock_mlst:
            handle_mlst_results(
                sample_final_results,
                sample_config,
                "Klebsiella pneumoniae",
                sample_paths["read1"],
                sample_paths["read2"],
                sample_paths["output_dir"],
                message=False,
                threads=1,
            )

        # Verify run_mlst was called with correct database path
        call_args = mock_mlst.call_args
        assert "/path/to/dbs/klebsiella_pneumoniae/klebsiella_pneumoniae" in str(
            call_args
        )


class TestFinalStatusPass:
    """Tests for the final_status_pass function."""

    def test_mlst_warning_does_not_cause_failed_status(self):
        """Test that MLST WARNING doesn't cause overall FAILED status."""
        results = blank_sample_results("sample_001")
        # Set all metrics to PASSED except MLST
        results["read_q30_status"] = "PASSED"
        results["read_length_status"] = "PASSED"
        results["coverage_status"] = "PASSED"
        results["coverage_alt_status"] = "PASSED"
        results["contamination_status"] = "PASSED"
        results["gc_content_status"] = "PASSED"
        results["species_status"] = "PASSED"
        results["mlst_status"] = "WARNING"

        final_status = final_status_pass(results)

        # MLST WARNING doesn't cause final to be WARNING/FAILED - it's informational
        # Final status should be PASSED since all critical metrics pass
        assert final_status == "PASSED"

    def test_mlst_warning_with_all_passed_metrics_result_in_passed(self):
        """Test that MLST WARNING doesn't affect overall QC pass if other metrics pass."""
        results = blank_sample_results("sample_001")
        # All critical metrics pass
        results["read_q30_status"] = "PASSED"
        results["read_length_status"] = "PASSED"
        results["coverage_status"] = "PASSED"
        results["coverage_alt_status"] = "PASSED"
        results["contamination_status"] = "PASSED"
        results["gc_content_status"] = "PASSED"
        results["species_status"] = "PASSED"
        results["mlst_status"] = "WARNING"

        final_status = final_status_pass(results)

        # MLST is informational and doesn't affect QC pass/fail
        # Overall status should be PASSED since all critical metrics pass
        assert final_status == "PASSED"

    def test_mlst_warning_does_not_override_failed_metrics(self):
        """Test that critical metric failures still result in FAILED even with MLST WARNING."""
        results = blank_sample_results("sample_001")
        # Set one critical metric to FAILED
        results["read_q30_status"] = "FAILED"
        results["read_length_status"] = "PASSED"
        results["coverage_status"] = "PASSED"
        results["coverage_alt_status"] = "PASSED"
        results["contamination_status"] = "PASSED"
        results["gc_content_status"] = "PASSED"
        results["species_status"] = "PASSED"
        results["mlst_status"] = "WARNING"

        final_status = final_status_pass(results)

        # Should be FAILED due to read_q30_status, not WARNING from MLST
        assert final_status == "FAILED"

    def test_no_mlst_status_defaults_to_passed(self):
        """Test that missing MLST status doesn't prevent PASSED overall status."""
        results = blank_sample_results("sample_001")
        # All metrics passed
        results["read_q30_status"] = "PASSED"
        results["read_length_status"] = "PASSED"
        results["coverage_status"] = "PASSED"
        results["coverage_alt_status"] = "PASSED"
        results["contamination_status"] = "PASSED"
        results["gc_content_status"] = "PASSED"
        results["species_status"] = "PASSED"
        # mlst_status is initialized to "FAILED" in blank_sample_results, set to "PASSED"
        results["mlst_status"] = "PASSED"

        final_status = final_status_pass(results)

        assert final_status == "PASSED"

    def test_mlst_passed_does_not_affect_passed_status(self):
        """Test that MLST PASSED status doesn't override other failures."""
        results = blank_sample_results("sample_001")
        # Set one critical metric to FAILED
        results["read_q30_status"] = "FAILED"
        results["read_length_status"] = "PASSED"
        results["coverage_status"] = "PASSED"
        results["coverage_alt_status"] = "PASSED"
        results["contamination_status"] = "PASSED"
        results["gc_content_status"] = "PASSED"
        results["species_status"] = "PASSED"
        results["mlst_status"] = "PASSED"

        final_status = final_status_pass(results)

        # Should be FAILED due to read_q30_status
        assert final_status == "FAILED"
