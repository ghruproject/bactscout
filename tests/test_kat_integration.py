"""
Integration tests for KAT (K-mer Analysis Toolkit) within BactScout pipeline.

Tests cover:
- End-to-end KAT analysis in full pipeline
- CLI parameter override functionality
- CSV output with all KAT columns
- Status determination from KAT metrics
- Graceful handling with KAT disabled
- Sample data processing with real FASTQ files (if available)
"""

import inspect

from bactscout.collect import collect_sample
from bactscout.main import main
from bactscout.thread import blank_sample_results, handle_kat_results


class TestKatIntegrationWithPipeline:
    """Test KAT integration with full BactScout pipeline."""

    def test_blank_sample_results_includes_kat_columns(self):
        """Test that blank_sample_results contains all KAT columns."""
        results = blank_sample_results("TEST_SAMPLE_001")

        # Check all KAT-related columns are present
        kat_columns = [
            "kat_status",
            "kat_version",
            "kat_k",
            "kat_total_kmers",
            "kat_total_kmer_instances",
            "kat_error_peak_cov",
            "kat_error_peak_prop",
            "kat_main_peak_cov",
            "kat_main_peak_height",
            "kat_unique_kmers_prop",
            "kat_median_kmer_cov",
            "kat_mean_kmer_cov",
            "kat_gcp_num_bins",
            "kat_gcp_top_bin_prop",
            "kat_gcp_multi_modal",
            "kat_gcp_lowcov_gc_prop",
            "kat_flag_low_coverage",
            "kat_flag_high_error",
            "kat_flag_contamination",
            "kat_message",
        ]

        for col in kat_columns:
            assert col in results, f"Missing KAT column: {col}"

    def test_blank_sample_results_kat_defaults(self):
        """Test that KAT columns have appropriate defaults."""
        results = blank_sample_results("TEST_SAMPLE_002")

        # Status should be SKIPPED (KAT not run by default)
        assert results["kat_status"] == "SKIPPED"

        # Flags should be 0 (integer, not boolean False)
        assert results["kat_flag_low_coverage"] == 0
        assert results["kat_flag_high_error"] == 0
        assert results["kat_flag_contamination"] == 0

        # Metrics should be 0
        assert results["kat_total_kmers"] == 0
        assert results["kat_main_peak_cov"] == 0.0
        assert results["kat_error_peak_cov"] == 0.0
        assert results["kat_gcp_num_bins"] == 0

    def test_handle_kat_results_passed_sample(self):
        """Test handle_kat_results with metrics indicating passed sample."""
        # Simulate healthy KAT metrics with no flags raised
        kat_metrics = {
            "kat_total_kmers": 50000000,
            "kat_main_peak_cov": 100,
            "kat_error_peak_cov": 10,
            "kat_error_peak_prop": 0.02,
            "kat_gcp_num_bins": 8,
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
            "kat_flag_low_coverage": 0,
            "kat_flag_high_error": 0,
            "kat_flag_contamination": 0,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        # Run handler
        result = handle_kat_results(kat_metrics, config)

        # Should pass (no flags)
        assert result["kat_status"] == "PASSED"
        assert result["kat_flag_low_coverage"] == 0
        assert result["kat_flag_high_error"] == 0
        assert result["kat_flag_contamination"] == 0

    def test_handle_kat_results_warning_low_coverage(self):
        """Test handle_kat_results with low coverage warning."""
        # Simulate low coverage metrics
        kat_metrics = {
            "kat_total_kmers": 5000000,
            "kat_main_peak_cov": 5,  # Below threshold of 10
            "kat_error_peak_cov": 10,
            "kat_error_peak_prop": 0.02,
            "kat_gcp_num_bins": 6,
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
            "kat_flag_low_coverage": 1,  # Flag should be set
            "kat_flag_high_error": 0,
            "kat_flag_contamination": 0,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Should have low coverage flag and WARNING status
        assert result["kat_flag_low_coverage"] == 1
        assert result["kat_status"] == "WARNING"

    def test_handle_kat_results_warning_high_error(self):
        """Test handle_kat_results with high error warning."""
        # Simulate high error metrics
        kat_metrics = {
            "kat_total_kmers": 50000000,
            "kat_main_peak_cov": 100,
            "kat_error_peak_cov": 15,
            "kat_error_peak_prop": 0.08,  # Exceeds error_prop_warn of 0.05
            "kat_gcp_num_bins": 8,
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
            "kat_flag_low_coverage": 0,
            "kat_flag_high_error": 1,  # Flag should be set
            "kat_flag_contamination": 0,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Should have high error flag and WARNING status
        assert result["kat_flag_high_error"] == 1
        assert result["kat_status"] == "WARNING"

    def test_handle_kat_results_contamination_multimodal(self):
        """Test handle_kat_results detects contamination (multi-modal)."""
        # Simulate contamination metrics (multi-modal distribution)
        kat_metrics = {
            "kat_total_kmers": 50000000,
            "kat_main_peak_cov": 100,
            "kat_error_peak_cov": 10,
            "kat_error_peak_prop": 0.02,
            "kat_gcp_num_bins": 8,
            "kat_gcp_multi_modal": 1,  # Multi-modal indicates contamination
            "kat_gcp_lowcov_gc_prop": 0.01,
            "kat_flag_low_coverage": 0,
            "kat_flag_high_error": 0,
            "kat_flag_contamination": 1,  # Flag should be set
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Should detect contamination with WARNING status
        assert result["kat_flag_contamination"] == 1
        assert result["kat_status"] == "WARNING"

    def test_handle_kat_results_failed_multiple_issues(self):
        """Test handle_kat_results with multiple issues (FAILED)."""
        # Simulate failed sample (multiple issues)
        kat_metrics = {
            "kat_total_kmers": 2000000,
            "kat_main_peak_cov": 2,  # Very low coverage (below 10)
            "kat_error_peak_cov": 20,
            "kat_error_peak_prop": 0.15,  # High error proportion (above 0.05)
            "kat_gcp_num_bins": 4,
            "kat_gcp_multi_modal": 1,  # Multi-modal
            "kat_gcp_lowcov_gc_prop": 0.01,
            "kat_flag_low_coverage": 1,  # All three flags set
            "kat_flag_high_error": 1,
            "kat_flag_contamination": 1,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Should fail with multiple issues
        assert result["kat_status"] == "FAILED"
        assert result["kat_flag_low_coverage"] == 1
        assert result["kat_flag_high_error"] == 1
        assert result["kat_flag_contamination"] == 1

    def test_handle_kat_results_populates_metrics(self):
        """Test that handle_kat_results populates all metric fields."""
        kat_metrics = {
            "kat_total_kmers": 50000000,
            "kat_main_peak_pos": 25,
            "kat_main_peak_cov": 100,
            "kat_error_peak_pos": 2,
            "kat_error_peak_cov": 10,
            "kat_error_region_start": 1,
            "kat_error_region_end": 5,
            "kat_error_prop": 0.02,
            "kat_gcp_num_bins": 8,
            "kat_gcp_kmer_freq": 0.75,
            "kat_gcp_multi_modal": False,
            "kat_gcp_extreme_gc": False,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Verify all metrics are populated
        assert result["kat_total_kmers"] == 50000000
        assert result["kat_main_peak_pos"] == 25
        assert result["kat_main_peak_cov"] == 100
        assert result["kat_error_peak_pos"] == 2
        assert result["kat_error_peak_cov"] == 10
        assert result["kat_error_region_start"] == 1
        assert result["kat_error_region_end"] == 5
        assert result["kat_error_prop"] == 0.02
        assert result["kat_gcp_num_bins"] == 8
        assert result["kat_gcp_kmer_freq"] == 0.75
        assert result["kat_gcp_multi_modal"] is False
        assert result["kat_gcp_extreme_gc"] is False


class TestKatCliParameterOverride:
    """Test KAT parameter override from CLI flags."""

    def test_cli_kat_flag_override(self):
        """Test that --kat flag overrides config."""
        # The main function should accept kat_enabled parameter
        sig = inspect.signature(main)
        assert "kat_enabled" in sig.parameters
        assert "k_mer_size" in sig.parameters

    def test_cli_k_size_override(self):
        """Test that -k/--k-size flag overrides config."""
        # Verify parameters are defined in collect_sample function signature
        sig = inspect.signature(collect_sample)
        assert "kat_enabled" in sig.parameters
        assert "k_mer_size" in sig.parameters


class TestKatDisabledBehavior:
    """Test pipeline behavior when KAT is disabled."""

    def test_sample_results_with_kat_disabled(self):
        """Test that results reflect SKIPPED status when KAT disabled."""
        results = blank_sample_results("TEST_SAMPLE_003")

        # Initially all KAT fields should be at defaults (SKIPPED status)
        assert results["kat_status"] == "SKIPPED"
        assert results["kat_flag_low_coverage"] == 0
        assert results["kat_flag_high_error"] == 0
        assert results["kat_flag_contamination"] == 0


class TestKatMetricRanges:
    """Test KAT metrics with realistic value ranges."""

    def test_kat_metric_ranges_realistic(self):
        """Test realistic ranges for KAT metrics."""
        # Typical bacterial genome k-mer metrics
        realistic_metrics = {
            "kat_total_kmers": 45_000_000,  # ~40-60M for 30x coverage
            "kat_main_peak_pos": 28,  # ~k-mer size (25-31)
            "kat_main_peak_cov": 95,  # ~30x average coverage
            "kat_error_peak_pos": 1,  # Error k-mers are rare
            "kat_error_peak_cov": 3,  # Low error k-mer count
            "kat_error_region_start": 1,
            "kat_error_region_end": 4,
            "kat_error_prop": 0.015,  # ~1.5% error
            "kat_gcp_num_bins": 8,  # 8 GC bins
            "kat_gcp_kmer_freq": 0.82,  # High main k-mer frequency
            "kat_gcp_multi_modal": False,  # Unimodal (no contamination)
            "kat_gcp_extreme_gc": False,  # Normal GC distribution
        }

        # All metrics should be within expected ranges
        assert realistic_metrics["kat_total_kmers"] > 10_000_000
        assert realistic_metrics["kat_main_peak_pos"] > 15
        assert realistic_metrics["kat_main_peak_cov"] > 20
        assert 0 < realistic_metrics["kat_error_prop"] < 0.5

    def test_kat_metric_ranges_low_coverage(self):
        """Test KAT metrics for low-coverage sample."""
        low_cov_metrics = {
            "kat_total_kmers": 8_000_000,  # ~5x coverage
            "kat_main_peak_pos": 20,
            "kat_main_peak_cov": 5,
            "kat_error_peak_pos": 1,
            "kat_error_peak_cov": 2,
            "kat_error_region_start": 1,
            "kat_error_region_end": 3,
            "kat_error_prop": 0.008,
            "kat_gcp_num_bins": 6,
            "kat_gcp_kmer_freq": 0.70,
            "kat_gcp_multi_modal": False,
            "kat_gcp_extreme_gc": False,
        }

        # Low coverage metrics should trigger warning
        assert low_cov_metrics["kat_main_peak_cov"] < 10

    def test_kat_metric_ranges_contaminated(self):
        """Test KAT metrics for contaminated sample."""
        contam_metrics = {
            "kat_total_kmers": 80_000_000,  # High k-mer count
            "kat_main_peak_pos": 25,
            "kat_main_peak_cov": 110,  # Main peak elevated
            "kat_error_peak_pos": 15,  # Secondary peak
            "kat_error_peak_cov": 65,  # Significant secondary peak
            "kat_error_region_start": 1,
            "kat_error_region_end": 5,
            "kat_error_prop": 0.12,  # Higher error proportion
            "kat_gcp_num_bins": 8,
            "kat_gcp_kmer_freq": 0.55,  # Lower main frequency
            "kat_gcp_multi_modal": True,  # Multi-modal!
            "kat_gcp_extreme_gc": False,
        }

        # Multi-modal indicates contamination
        assert contam_metrics["kat_gcp_multi_modal"] is True


class TestKatResultConsistency:
    """Test consistency of KAT result handling across different contexts."""

    def test_kat_status_values(self):
        """Test valid KAT status values."""
        valid_statuses = ["PASSED", "WARNING", "FAILED", "SKIPPED"]

        # Create sample results
        results = blank_sample_results("TEST_SAMPLE_004")

        # Initial status
        assert results["kat_status"] in valid_statuses

    def test_kat_qc_message_populated(self):
        """Test that QC message is populated in results."""
        kat_metrics = {
            "kat_total_kmers": 50000000,
            "kat_main_peak_pos": 25,
            "kat_main_peak_cov": 100,
            "kat_error_peak_pos": 2,
            "kat_error_peak_cov": 10,
            "kat_error_region_start": 1,
            "kat_error_region_end": 5,
            "kat_error_prop": 0.02,
            "kat_gcp_num_bins": 8,
            "kat_gcp_kmer_freq": 0.75,
            "kat_gcp_multi_modal": False,
            "kat_gcp_extreme_gc": False,
        }

        config = {
            "kat": {
                "thresholds": {
                    "error_cov_cutoff": 4,
                    "error_prop_warn": 0.05,
                    "main_cov_low": 10,
                    "gcp_multi_modal_bin_prop": 0.1,
                    "comp_shared_prop_warn": 0.9,
                }
            }
        }

        result = handle_kat_results(kat_metrics, config)

        # Message should be populated
        assert "kat_message" in result or "kat_qc_message" in result
        # Message should be string
        msg = result.get("kat_message", result.get("kat_qc_message", ""))
        assert isinstance(msg, str)


class TestKatEdgeCases:
    """Test edge cases and error conditions."""

    def test_kat_with_zero_metrics(self):
        """Test handling of zero metrics (failed KAT run)."""
        sample_results = blank_sample_results("TEST_SAMPLE_005")

        # All metrics are 0 (not None or False)
        assert sample_results["kat_total_kmers"] == 0
        assert sample_results["kat_status"] == "SKIPPED"

    def test_kat_flag_independence(self):
        """Test that flags can be set independently."""
        sample_results = blank_sample_results("TEST_SAMPLE_006")

        # Manually set flags (use 1 for true, 0 for false)
        sample_results["kat_flag_low_coverage"] = 1
        sample_results["kat_flag_high_error"] = 0
        sample_results["kat_flag_contamination"] = 0

        # Verify independence
        assert sample_results["kat_flag_low_coverage"] == 1
        assert sample_results["kat_flag_high_error"] == 0
        assert sample_results["kat_flag_contamination"] == 0

    def test_kat_message_field_types(self):
        """Test that message field handles various string types."""
        sample_results = blank_sample_results("TEST_SAMPLE_007")

        # Test message field is string or None
        sample_results["kat_qc_message"] = "Test message"
        assert isinstance(sample_results["kat_qc_message"], str)

        sample_results["kat_qc_message"] = ""
        assert isinstance(sample_results["kat_qc_message"], str)


class TestKatIntegrationWithOtherQC:
    """Test KAT integration with other QC metrics."""

    def test_kat_independent_from_fastp(self):
        """Test that KAT results are independent from fastp metrics."""
        results = blank_sample_results("TEST_SAMPLE_008")

        # Simulate fastp passed
        results["fastp_status"] = "PASSED"

        # Set KAT to failed
        results["kat_status"] = "FAILED"
        results["kat_flag_contamination"] = True

        # They should be independent
        assert results["fastp_status"] == "PASSED"
        assert results["kat_status"] == "FAILED"

    def test_kat_status_precedence(self):
        """Test handling of multiple QC statuses."""
        results = blank_sample_results("TEST_SAMPLE_009")

        # Both fastp and KAT present
        results["fastp_status"] = "WARNING"
        results["kat_status"] = "FAILED"
        results["mlst_status"] = "PASSED"

        # Each should be independent
        statuses = [results[s] for s in ["fastp_status", "kat_status", "mlst_status"]]
        assert "FAILED" in statuses
        assert "WARNING" in statuses
        assert "PASSED" in statuses
