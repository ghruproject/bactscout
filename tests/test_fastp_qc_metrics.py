"""
Comprehensive tests for TIER 1 & TIER 2 fastp QC metrics extraction and validation.

Tests cover:
- TIER 1: Duplication rate, insert size, filtering pass rate, N-content
- TIER 2: Quality trends, adapter detection, composition data
"""

from bactscout.thread import (
    blank_sample_results,
    get_fastp_results,
    handle_adapter_detection,
    handle_duplication_results,
    handle_filtering_results,
    handle_insert_size_results,
    handle_n_content_results,
    handle_quality_trends,
)


class TestDuplicationResults:
    """Test duplication rate extraction and validation."""

    def test_duplication_passed_below_warn_threshold(self):
        """Test PASSED status when duplication is below warn threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["duplication_rate"] = 0.15  # 15%, below 20% warn threshold

        config = {
            "duplication_warn_threshold": 0.20,
            "duplication_fail_threshold": 0.30,
        }
        results = handle_duplication_results(results, config)

        assert results["duplication_status"] == "PASSED"
        assert "below warning threshold" in results["duplication_message"]

    def test_duplication_warning_between_thresholds(self):
        """Test WARNING status when duplication is between warn and fail thresholds."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["duplication_rate"] = 0.25  # 25%, between 20% and 30%

        config = {
            "duplication_warn_threshold": 0.20,
            "duplication_fail_threshold": 0.30,
        }
        results = handle_duplication_results(results, config)

        assert results["duplication_status"] == "WARNING"
        assert "PCR bias" in results["duplication_message"]

    def test_duplication_failed_above_fail_threshold(self):
        """Test FAILED status when duplication exceeds fail threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["duplication_rate"] = 0.35  # 35%, above 30% fail threshold

        config = {
            "duplication_warn_threshold": 0.20,
            "duplication_fail_threshold": 0.30,
        }
        results = handle_duplication_results(results, config)

        assert results["duplication_status"] == "FAILED"
        assert "High PCR bias" in results["duplication_message"]

    def test_duplication_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["duplication_rate"] = 0.0

        config = {
            "duplication_warn_threshold": 0.20,
            "duplication_fail_threshold": 0.30,
        }
        results = handle_duplication_results(results, config)

        assert results["duplication_status"] == "FAILED"
        assert "No reads processed" in results["duplication_message"]


class TestInsertSizeResults:
    """Test insert size peak extraction and validation."""

    def test_insert_size_passed_within_range(self):
        """Test PASSED status when insert size is within expected range."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["insert_size_peak"] = 400  # Within 200-600bp range

        config = {"insert_size_min_threshold": 200, "insert_size_max_threshold": 600}
        results = handle_insert_size_results(results, config)

        assert results["insert_size_status"] == "PASSED"
        assert "within expected range" in results["insert_size_message"]

    def test_insert_size_warning_too_short(self):
        """Test WARNING status when insert size is below minimum."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["insert_size_peak"] = 150  # Below 200bp minimum

        config = {"insert_size_min_threshold": 200, "insert_size_max_threshold": 600}
        results = handle_insert_size_results(results, config)

        assert results["insert_size_status"] == "WARNING"
        assert "below minimum" in results["insert_size_message"]

    def test_insert_size_warning_too_long(self):
        """Test WARNING status when insert size is above maximum."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["insert_size_peak"] = 700  # Above 600bp maximum

        config = {"insert_size_min_threshold": 200, "insert_size_max_threshold": 600}
        results = handle_insert_size_results(results, config)

        assert results["insert_size_status"] == "WARNING"
        assert "above maximum" in results["insert_size_message"]

    def test_insert_size_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["insert_size_peak"] = 0

        config = {"insert_size_min_threshold": 200, "insert_size_max_threshold": 600}
        results = handle_insert_size_results(results, config)

        assert results["insert_size_status"] == "FAILED"
        assert "No reads processed" in results["insert_size_message"]


class TestFilteringResults:
    """Test filtering pass rate extraction and validation."""

    def test_filtering_passed_above_threshold(self):
        """Test PASSED status when pass rate exceeds threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["filtering_pass_rate"] = 98.0  # 98%, above 95% threshold

        config = {"filtering_pass_rate_threshold": 0.95}
        results = handle_filtering_results(results, config)

        assert results["filtering_status"] == "PASSED"
        assert "meets threshold" in results["filtering_message"]

    def test_filtering_warning_below_threshold(self):
        """Test WARNING status when pass rate falls below threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["filtering_pass_rate"] = 90.0  # 90%, below 95% threshold

        config = {"filtering_pass_rate_threshold": 0.95}
        results = handle_filtering_results(results, config)

        assert results["filtering_status"] == "WARNING"
        assert "10.00% of reads were filtered out" in results["filtering_message"]

    def test_filtering_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["filtering_pass_rate"] = 0.0

        config = {"filtering_pass_rate_threshold": 0.95}
        results = handle_filtering_results(results, config)

        assert results["filtering_status"] == "FAILED"
        assert "No reads processed" in results["filtering_message"]


class TestNContentResults:
    """Test N-content (ambiguous bases) extraction and validation."""

    def test_n_content_passed_below_threshold(self):
        """Test PASSED status when N-content is below threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["n_content_rate"] = 0.05  # 0.05%, below 0.1% threshold

        config = {"n_content_threshold": 0.001}
        results = handle_n_content_results(results, config)

        assert results["n_content_status"] == "PASSED"
        assert "below threshold" in results["n_content_message"]

    def test_n_content_warning_above_threshold(self):
        """Test WARNING status when N-content exceeds threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["n_content_rate"] = 0.15  # 0.15%, above 0.1% threshold

        config = {"n_content_threshold": 0.001}
        results = handle_n_content_results(results, config)

        assert results["n_content_status"] == "WARNING"
        assert "base-calling uncertainty" in results["n_content_message"]

    def test_n_content_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["n_content_rate"] = 0.0

        config = {"n_content_threshold": 0.001}
        results = handle_n_content_results(results, config)

        assert results["n_content_status"] == "FAILED"
        assert "No reads processed" in results["n_content_message"]


class TestQualityTrends:
    """Test quality end-drop detection."""

    def test_quality_trend_passed_low_drop(self):
        """Test PASSED status when quality drop is within threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        # Simulate 151-cycle quality curve with small drop in last 20 cycles
        # Quality stays at 35 for most of curve, then drops 3 points in last 20 cycles (35 -> 32)
        results["quality_curves_mean"] = [35] * 141 + [
            35,
            34,
            34,
            33,
            33,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
            32,
        ]

        config = {"quality_end_drop_threshold": 5}
        results = handle_quality_trends(results, config)

        assert results["quality_trend_status"] == "PASSED"
        assert "acceptable" in results["quality_trend_message"]

    def test_quality_trend_warning_high_drop(self):
        """Test WARNING status when quality drop exceeds threshold."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        # Simulate 151-cycle quality curve with large drop in last 20 cycles
        results["quality_curves_mean"] = [35] * 131 + [
            35,
            34,
            33,
            32,
            31,
            30,
            25,
            20,
            15,
            10,
            8,
            6,
            4,
            2,
            0,
            -2,
            -4,
            -6,
            -8,
            -10,
        ]

        config = {"quality_end_drop_threshold": 5}
        results = handle_quality_trends(results, config)

        assert results["quality_trend_status"] == "WARNING"
        assert "end-drop detected" in results["quality_trend_message"]
        assert "sequencer degradation" in results["quality_trend_message"]

    def test_quality_trend_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["quality_curves_mean"] = []

        config = {"quality_end_drop_threshold": 5}
        results = handle_quality_trends(results, config)

        assert results["quality_trend_status"] == "FAILED"
        assert "No reads processed" in results["quality_trend_message"]

    def test_quality_trend_short_curve(self):
        """Test FAILED status when quality curve is too short."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["quality_curves_mean"] = [35, 34, 33]  # Only 3 cycles

        config = {"quality_end_drop_threshold": 5}
        results = handle_quality_trends(results, config)

        assert results["quality_trend_status"] == "FAILED"
        assert "No reads processed" in results["quality_trend_message"]


class TestAdapterDetection:
    """Test adapter detection flag verification."""

    def test_adapter_detection_passed_flag_present(self):
        """Test PASSED status when adapter detection flag is present."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["adapter_detection_flag"] = True

        config = {}
        results = handle_adapter_detection(results, config)

        assert results["adapter_detection_status"] == "PASSED"
        assert "enabled" in results["adapter_detection_message"]

    def test_adapter_detection_warning_flag_absent(self):
        """Test WARNING status when adapter detection flag is not present."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 1000000
        results["adapter_detection_flag"] = False

        config = {}
        results = handle_adapter_detection(results, config)

        assert results["adapter_detection_status"] == "WARNING"
        assert "not enabled" in results["adapter_detection_message"]

    def test_adapter_detection_no_reads(self):
        """Test FAILED status when no reads were processed."""
        results = blank_sample_results("sample_001")
        results["read_total_reads"] = 0
        results["adapter_detection_flag"] = False

        config = {}
        results = handle_adapter_detection(results, config)

        assert results["adapter_detection_status"] == "FAILED"
        assert "No reads processed" in results["adapter_detection_message"]


class TestFastpResultsExtraction:
    """Test extraction of new metrics from fastp JSON."""

    def test_extraction_sets_all_new_fields(self):
        """Test that get_fastp_results extracts all new metric fields."""
        fastp_result = {"status": "success", "json_report": "/tmp/test_fastp.json"}

        # Mock JSON content
        import json
        import os
        import tempfile

        fastp_data = {
            "summary": {
                "before_filtering": {"total_reads": 1000000},
                "after_filtering": {
                    "total_reads": 950000,
                    "total_bases": 100000000,
                    "q20_bases": 95000000,
                    "q30_bases": 90000000,
                    "q20_rate": 0.95,
                    "q30_rate": 0.90,
                    "read1_mean_length": 150,
                    "read2_mean_length": 150,
                    "gc_content": 0.50,
                },
            },
            "duplication": {"rate": 0.15},
            "insert_size": {"peak": 400},
            "filtering_result": {
                "total_reads": 1000000,
                "too_many_N": 500,
            },
            "quality_curves": {"mean": [35] * 151},
            "command": "fastp --detect_adapter_for_pe ...",
            "content_curves": {
                "A": [0.25] * 151,
                "T": [0.25] * 151,
                "G": [0.25] * 151,
                "C": [0.25] * 151,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(fastp_data, f)
            temp_file = f.name

        try:
            fastp_result["json_report"] = temp_file
            results = get_fastp_results(fastp_result)

            # Check all new fields are present
            assert "duplication_rate" in results
            assert "insert_size_peak" in results
            assert "filtering_pass_rate" in results
            assert "n_content_rate" in results
            assert "quality_curves_mean" in results
            assert "adapter_detection_flag" in results
            assert "composition_data" in results

            # Check values
            assert results["duplication_rate"] == 0.15
            assert results["insert_size_peak"] == 400
            assert results["filtering_pass_rate"] == 95.0  # 950000/1000000 * 100
            assert results["n_content_rate"] == 0.05  # 500/1000000 * 100
            assert len(results["quality_curves_mean"]) == 151
            assert results["adapter_detection_flag"] is True
            assert "A" in results["composition_data"]
        finally:
            os.unlink(temp_file)

    def test_extraction_handles_missing_fields(self):
        """Test that extraction handles missing fields gracefully."""
        fastp_result = {"status": "success", "json_report": "/tmp/test_fastp.json"}

        # Minimal JSON with missing optional fields
        import json
        import os
        import tempfile

        fastp_data = {
            "summary": {
                "before_filtering": {"total_reads": 1000000},
                "after_filtering": {
                    "total_reads": 950000,
                    "total_bases": 100000000,
                    "q20_bases": 95000000,
                    "q30_bases": 90000000,
                    "q20_rate": 0.95,
                    "q30_rate": 0.90,
                    "read1_mean_length": 150,
                    "read2_mean_length": 150,
                    "gc_content": 0.50,
                },
            },
            # Missing duplication, insert_size, filtering_result, quality_curves, command, content_curves
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(fastp_data, f)
            temp_file = f.name

        try:
            fastp_result["json_report"] = temp_file
            results = get_fastp_results(fastp_result)

            # Check defaults for missing fields
            assert results["duplication_rate"] == 0.0
            assert results["insert_size_peak"] == 0
            assert results["filtering_pass_rate"] == 95.0  # Still calculated
            assert results["n_content_rate"] == 0.0
            assert results["quality_curves_mean"] == []
            assert results["adapter_detection_flag"] is False
            assert results["composition_data"] == {}
        finally:
            os.unlink(temp_file)
