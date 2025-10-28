"""
Comprehensive unit tests for KAT (K-mer Analysis Toolkit) metrics module.

Tests cover:
- Binary detection and version extraction
- KAT command execution with error handling
- Histogram parser with various input formats
- GC×coverage matrix parser
- Flag computation from metrics
- Full pipeline orchestration
- Edge cases: empty files, malformed data, missing KAT
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from bactscout.qc.kat_metrics import (
    compute_kat_flags,
    get_kat_binary,
    get_kat_version,
    parse_kat_gcp,
    parse_kat_hist,
    run_kat_analysis,
)


class TestGetKatBinary:
    """Test KAT binary detection."""

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_binary_found(self, mock_run):
        """Test successful KAT binary detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="/usr/bin/kat")
        result = get_kat_binary()
        assert result == "/usr/bin/kat"

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_binary_not_found(self, mock_run):
        """Test KAT binary not in PATH."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_kat_binary()
        assert result is None

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_binary_timeout(self, mock_run):
        """Test timeout when searching for KAT binary."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("which", 5)
        result = get_kat_binary()
        assert result is None


class TestGetKatVersion:
    """Test KAT version extraction."""

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_version_found(self, mock_run):
        """Test successful version extraction."""
        mock_run.return_value = MagicMock(returncode=0, stdout="kat version 2.4.2\n")
        result = get_kat_version("/usr/bin/kat")
        assert result == "kat version 2.4.2"

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_version_not_found(self, mock_run):
        """Test when version output is not available."""
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_kat_version("/usr/bin/kat")
        assert result is None

    @patch("bactscout.qc.kat_metrics.subprocess.run")
    def test_kat_version_timeout(self, mock_run):
        """Test timeout when getting version."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("kat", 5)
        result = get_kat_version("/usr/bin/kat")
        assert result is None


class TestParseKatHist:
    """Test histogram parser."""

    def test_parse_histogram_normal(self):
        """Test parsing normal histogram output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            # Write histogram data: coverage, count
            f.write("1 100\n")  # 100 k-mers at coverage 1
            f.write("2 200\n")  # 200 k-mers at coverage 2
            f.write("10 500\n")  # 500 k-mers at coverage 10
            f.write("50 300\n")  # 300 k-mers at coverage 50
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            assert result["kat_total_kmers"] == 1100  # 100+200+500+300
            assert (
                result["kat_total_kmer_instances"] == 20500
            )  # 1*100+2*200+10*500+50*300
            assert result["kat_error_peak_cov"] == 2  # Max in error region (cov<=4)
            assert result["kat_main_peak_cov"] == 10  # Max by count in main region (cov>4)
            assert result["kat_main_peak_height"] == 500

            os.unlink(f.name)

    def test_parse_histogram_with_comments(self):
        """Test parsing histogram with comment lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("# Coverage Count\n")
            f.write("1 50\n")
            f.write("10 100\n")
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            assert result["kat_total_kmers"] == 150
            assert result["kat_total_kmer_instances"] == 1050  # 1*50 + 10*100

            os.unlink(f.name)

    def test_parse_histogram_empty_file(self):
        """Test parsing empty histogram file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            # Should return defaults
            assert result["kat_total_kmers"] == 0
            assert result["kat_total_kmer_instances"] == 0

            os.unlink(f.name)

    def test_parse_histogram_missing_file(self):
        """Test parsing non-existent histogram file."""
        config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
        result = parse_kat_hist("/nonexistent/file.hist", config)

        # Should return defaults
        assert result["kat_total_kmers"] == 0

    def test_parse_histogram_median_calculation(self):
        """Test median k-mer coverage calculation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            # Create bimodal distribution to test median
            f.write("1 10\n")  # 10 k-mers
            f.write("2 20\n")  # 20 k-mers
            f.write("3 30\n")  # 30 k-mers (cumsum: 60)
            f.write("4 40\n")  # 40 k-mers (cumsum: 100) <- median should cross here
            f.write("5 50\n")  # 50 k-mers
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 1}}}
            result = parse_kat_hist(f.name, config)

            # Total = 150, median position = 75
            # Cumsum: 10, 30, 60, 100 -> median is at coverage 4
            assert result["kat_median_kmer_cov"] == 4.0

            os.unlink(f.name)


class TestParseKatGcp:
    """Test GC×coverage parser."""

    def test_parse_gcp_normal(self):
        """Test parsing normal GCP matrix."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gcp", delete=False) as f:
            # GC%, Coverage, Count
            f.write("0.45 10 100\n")  # 100 reads at GC=45%, cov=10
            f.write("0.50 20 500\n")  # 500 reads at GC=50%, cov=20 (main)
            f.write("0.55 10 100\n")  # 100 reads at GC=55%, cov=10
            f.flush()

            config = {
                "kat": {
                    "thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}
                }
            }
            result = parse_kat_gcp(f.name, config)

        assert result["kat_gcp_num_bins"] == 3
        assert result["kat_gcp_top_bin_prop"] == 500 / 700  # 500/(100+500+100)
        assert result["kat_gcp_multi_modal"] == 1  # Multiple bins >= 10% threshold            os.unlink(f.name)

    def test_parse_gcp_multimodal(self):
        """Test detection of multi-modal contamination."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gcp", delete=False) as f:
            # Two distinct peaks (contamination)
            f.write("0.40 15 300\n")  # Peak 1: GC=40%, cov=15
            f.write("0.60 15 250\n")  # Peak 2: GC=60%, cov=15 (high proportion)
            f.flush()

            config = {
                "kat": {
                    "thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}
                }
            }
            result = parse_kat_gcp(f.name, config)

            assert result["kat_gcp_multi_modal"] == 1  # Multimodal detected

            os.unlink(f.name)

    def test_parse_gcp_extreme_gc(self):
        """Test detection of extreme GC + low coverage (alien DNA)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gcp", delete=False) as f:
            # Normal reads
            f.write("0.50 20 1000\n")  # Main peak
            # Alien DNA: low coverage + extreme GC
            f.write("0.10 1 50\n")  # Low GC, low coverage
            f.write("0.90 1 40\n")  # High GC, low coverage
            f.flush()

            config = {
                "kat": {
                    "thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}
                }
            }
            result = parse_kat_gcp(f.name, config)

            assert result["kat_gcp_lowcov_gc_prop"] > 0.08  # Detects alien DNA

            os.unlink(f.name)

    def test_parse_gcp_empty_file(self):
        """Test parsing empty GCP file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gcp", delete=False) as f:
            f.flush()

            config = {
                "kat": {
                    "thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}
                }
            }
            result = parse_kat_gcp(f.name, config)

            # Should return defaults
            assert result["kat_gcp_num_bins"] == 0

            os.unlink(f.name)

    def test_parse_gcp_missing_file(self):
        """Test parsing non-existent GCP file."""
        config = {
            "kat": {"thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}}
        }
        result = parse_kat_gcp("/nonexistent/file.gcp", config)

        # Should return defaults
        assert result["kat_gcp_num_bins"] == 0


class TestComputeKatFlags:
    """Test flag computation."""

    def test_no_flags_raised(self):
        """Test when no flags should be raised."""
        metrics = {
            "kat_main_peak_cov": 20.0,
            "kat_error_peak_prop": 0.02,
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
        }
        config = {
            "kat": {
                "thresholds": {
                    "main_cov_low": 10,
                    "error_prop_warn": 0.05,
                }
            }
        }

        result = compute_kat_flags(metrics, config)

        assert result["kat_flag_low_coverage"] == 0
        assert result["kat_flag_high_error"] == 0
        assert result["kat_flag_contamination"] == 0

    def test_low_coverage_flag(self):
        """Test low coverage flag."""
        metrics = {
            "kat_main_peak_cov": 5.0,  # Below threshold of 10
            "kat_error_peak_prop": 0.02,
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
        }
        config = {
            "kat": {
                "thresholds": {
                    "main_cov_low": 10,
                    "error_prop_warn": 0.05,
                }
            }
        }

        result = compute_kat_flags(metrics, config)

        assert result["kat_flag_low_coverage"] == 1

    def test_high_error_flag(self):
        """Test high error flag."""
        metrics = {
            "kat_main_peak_cov": 20.0,
            "kat_error_peak_prop": 0.08,  # Above threshold of 0.05
            "kat_gcp_multi_modal": 0,
            "kat_gcp_lowcov_gc_prop": 0.01,
        }
        config = {
            "kat": {
                "thresholds": {
                    "main_cov_low": 10,
                    "error_prop_warn": 0.05,
                }
            }
        }

        result = compute_kat_flags(metrics, config)

        assert result["kat_flag_high_error"] == 1

    def test_contamination_flag(self):
        """Test contamination flag from multimodal."""
        metrics = {
            "kat_main_peak_cov": 20.0,
            "kat_error_peak_prop": 0.02,
            "kat_gcp_multi_modal": 1,  # Multimodal detected
            "kat_gcp_lowcov_gc_prop": 0.01,
        }
        config = {
            "kat": {
                "thresholds": {
                    "main_cov_low": 10,
                    "error_prop_warn": 0.05,
                }
            }
        }

        result = compute_kat_flags(metrics, config)

        assert result["kat_flag_contamination"] == 1

    def test_multiple_flags(self):
        """Test when multiple flags are raised."""
        metrics = {
            "kat_main_peak_cov": 3.0,  # Low
            "kat_error_peak_prop": 0.10,  # High
            "kat_gcp_multi_modal": 1,  # Multimodal
            "kat_gcp_lowcov_gc_prop": 0.01,
        }
        config = {
            "kat": {
                "thresholds": {
                    "main_cov_low": 10,
                    "error_prop_warn": 0.05,
                }
            }
        }

        result = compute_kat_flags(metrics, config)

        assert result["kat_flag_low_coverage"] == 1
        assert result["kat_flag_high_error"] == 1
        assert result["kat_flag_contamination"] == 1


class TestRunKatAnalysis:
    """Test full pipeline orchestration."""

    def test_kat_disabled(self):
        """Test graceful handling when KAT is disabled."""
        config = {"kat": {"enabled": False}}

        result = run_kat_analysis(
            read1_file="/path/to/r1.fastq",
            read2_file="/path/to/r2.fastq",
            output_dir="/output",
            config=config,
            threads=4,
        )

        # Should return empty results when disabled
        assert len(result) == 0 or result.get("kat_total_kmers", 0) == 0

    @patch("bactscout.qc.kat_metrics.get_kat_binary")
    def test_kat_binary_not_found_graceful(self, mock_get_binary):
        """Test graceful degradation when KAT is not installed."""
        mock_get_binary.return_value = None

        config = {"kat": {"enabled": True}}

        result = run_kat_analysis(
            read1_file="/path/to/r1.fastq",
            read2_file="/path/to/r2.fastq",
            output_dir="/output",
            config=config,
            threads=4,
        )

        # Should return empty results, not crash
        assert isinstance(result, dict)

    @patch("bactscout.qc.kat_metrics.run_kat_gcp")
    @patch("bactscout.qc.kat_metrics.run_kat_hist")
    @patch("bactscout.qc.kat_metrics.get_kat_version")
    @patch("bactscout.qc.kat_metrics.get_kat_binary")
    def test_kat_pipeline_success(self, mock_binary, mock_version, mock_hist, mock_gcp):
        """Test successful KAT pipeline."""
        mock_binary.return_value = "/usr/bin/kat"
        mock_version.return_value = "kat version 2.4.2"
        mock_hist.return_value = "/output/kat_hist.gnuplot"
        mock_gcp.return_value = "/output/kat_gcp.gnuplot"

        config = {
            "kat": {
                "enabled": True,
                "k": 27,
                "run": {"hist": True, "gcp": True},
                "thresholds": {"error_cov_cutoff": 4, "error_prop_warn": 0.05},
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock output files
            hist_file = os.path.join(tmpdir, "kat_hist.gnuplot")
            gcp_file = os.path.join(tmpdir, "kat_gcp.gnuplot")

            with open(hist_file, "w") as f:
                f.write("1 100\n10 500\n")
            with open(gcp_file, "w") as f:
                f.write("0.50 10 200\n")

            mock_hist.return_value = hist_file
            mock_gcp.return_value = gcp_file

            result = run_kat_analysis(
                read1_file="/path/to/r1.fastq",
                read2_file="/path/to/r2.fastq",
                output_dir=tmpdir,
                config=config,
                threads=4,
            )

            # Should have results from both hist and gcp
            assert "kat_total_kmers" in result
            assert "kat_gcp_num_bins" in result
            assert result.get("kat_version") == "kat version 2.4.2"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_histogram_single_coverage_level(self):
        """Test histogram with all k-mers at single coverage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            f.write("10 1000\n")  # All k-mers at coverage 10
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            assert result["kat_total_kmers"] == 1000
            assert result["kat_median_kmer_cov"] == 10.0
            assert result["kat_mean_kmer_cov"] == 10.0

            os.unlink(f.name)

    def test_histogram_high_coverage_distribution(self):
        """Test very high coverage k-mers."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            f.write("1 10\n")
            f.write("1000 5\n")  # Some k-mers at 1000x coverage
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            assert result["kat_total_kmers"] == 15
            assert result["kat_total_kmer_instances"] == 5010  # 1*10 + 1000*5

            os.unlink(f.name)

    def test_gcp_single_bin(self):
        """Test GCP with single bin (perfect sample)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gcp", delete=False) as f:
            f.write("0.50 20 1000\n")  # Single peak
            f.flush()

            config = {
                "kat": {
                    "thresholds": {"gcp_multi_modal_bin_prop": 0.1, "main_cov_low": 10}
                }
            }
            result = parse_kat_gcp(f.name, config)

            assert result["kat_gcp_num_bins"] == 1
            assert result["kat_gcp_top_bin_prop"] == 1.0
            assert result["kat_gcp_multi_modal"] == 0

            os.unlink(f.name)

    def test_malformed_histogram_line(self):
        """Test histogram with malformed data lines."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".hist", delete=False) as f:
            f.write("1 100\n")
            f.write("invalid line\n")  # Malformed
            f.write("2 200\n")
            f.write("\n")  # Empty line
            f.write("10 500\n")
            f.flush()

            config = {"kat": {"thresholds": {"error_cov_cutoff": 4}}}
            result = parse_kat_hist(f.name, config)

            # Should skip malformed lines and parse valid ones
            assert result["kat_total_kmers"] == 800  # 100+200+500

            os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
