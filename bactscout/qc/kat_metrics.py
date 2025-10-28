"""
KAT (K-mer Analysis Toolkit) integration module for BactScout.

This module handles k-mer analysis including histogram distribution, GC×coverage
patterns, and contamination detection. All metrics are extracted from KAT outputs
and made available as numeric columns in QC reports.

Functions:
    - get_kat_binary(): Locate KAT executable in environment
    - run_kat_subcommands(): Execute KAT hist/gcp/comp/sect on sample reads
    - parse_kat_hist(): Extract k-mer distribution metrics from histogram
    - parse_kat_gcp(): Extract GC×coverage patterns from matrix
    - parse_kat_comp(): Extract k-mer sharing metrics from composition
    - parse_kat_sect(): Extract sector coverage metrics
    - compute_kat_flags(): Derive boolean flags from metrics
    - run_kat_analysis(): Orchestrate full KAT analysis pipeline
"""

import logging
import os
import subprocess
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def get_kat_binary() -> Optional[str]:
    """
    Locate KAT executable in the environment.

    Returns:
        str: Path to KAT binary if found, None otherwise.

    Notes:
        - Checks PATH for 'kat' command
        - Returns None if not found (graceful degradation)
    """
    try:
        result = subprocess.run(
            ["which", "kat"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            kat_path = result.stdout.strip()
            logger.info("Found KAT at: %s", kat_path)
            return kat_path
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    logger.warning("KAT binary not found in PATH. KAT analysis will be skipped.")
    return None


def get_kat_version(kat_binary: str) -> Optional[str]:
    """
    Get version of installed KAT.

    Args:
        kat_binary (str): Path to KAT executable

    Returns:
        str: Version string or None if unavailable
    """
    try:
        result = subprocess.run(
            [kat_binary, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            # Parse version from output (typically "kat version X.X.X")
            for line in result.stdout.split("\n"):
                if "version" in line.lower():
                    return line.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def run_kat_hist(
    kat_binary: str,
    read1_file: str,
    read2_file: str,
    output_dir: str,
    k: int = 27,
    threads: int = 4,
) -> Optional[str]:
    """
    Run KAT histogram analysis on sequencing reads.

    Args:
        kat_binary (str): Path to KAT executable
        read1_file (str): Path to R1 FASTQ file
        read2_file (str): Path to R2 FASTQ file
        output_dir (str): Output directory for results
        k (int): K-mer size (default 27)
        threads (int): Number of threads to use (default 4)

    Returns:
        str: Path to output matrix file or None if failed
    """
    output_file = os.path.join(output_dir, f"kat_hist_k{k}")

    try:
        cmd = [
            kat_binary,
            "hist",
            "-t",
            str(threads),
            "-k",
            str(k),
            "-o",
            output_file,
            read1_file,
            read2_file,
        ]
        logger.info("Running KAT histogram with k=%s", k)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
            check=False,
        )
        if result.returncode == 0:
            matrix_file = f"{output_file}.hist.gnuplot"
            if os.path.exists(matrix_file):
                logger.info("KAT histogram completed: %s", matrix_file)
                return matrix_file
            logger.warning("Expected KAT histogram output not found: %s", matrix_file)
        else:
            logger.warning("KAT histogram failed: %s", result.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("KAT histogram error: %s", str(e))

    return None


def run_kat_gcp(
    kat_binary: str,
    read1_file: str,
    read2_file: str,
    output_dir: str,
    k: int = 27,
    threads: int = 4,
) -> Optional[str]:
    """
    Run KAT GC×coverage analysis on sequencing reads.

    Args:
        kat_binary (str): Path to KAT executable
        read1_file (str): Path to R1 FASTQ file
        read2_file (str): Path to R2 FASTQ file
        output_dir (str): Output directory for results
        k (int): K-mer size (default 27)
        threads (int): Number of threads to use (default 4)

    Returns:
        str: Path to output GCP file or None if failed
    """
    output_file = os.path.join(output_dir, f"kat_gcp_k{k}")

    try:
        cmd = [
            kat_binary,
            "gcp",
            "-t",
            str(threads),
            "-k",
            str(k),
            "-o",
            output_file,
            read1_file,
            read2_file,
        ]
        logger.info("Running KAT gcp with k=%s", k)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
            check=False,
        )
        if result.returncode == 0:
            gcp_file = f"{output_file}.gcp.gnuplot"
            if os.path.exists(gcp_file):
                logger.info("KAT gcp completed: %s", gcp_file)
                return gcp_file
            logger.warning("Expected KAT gcp output not found: %s", gcp_file)
        else:
            logger.warning("KAT gcp failed: %s", result.stderr)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("KAT gcp error: %s", str(e))

    return None


def parse_kat_hist(hist_file: str, config: Dict) -> Dict[str, float]:
    """
    Parse KAT histogram file to extract k-mer distribution metrics.

    Args:
        hist_file (str): Path to KAT histogram file (.histo)
        config (dict): Configuration dict with thresholds

    Returns:
        dict: Metrics including:
            - kat_total_kmers (int): Total distinct k-mers
            - kat_total_kmer_instances (int): Sum of all k-mer frequencies
            - kat_error_peak_cov (float): Coverage at error peak
            - kat_error_peak_prop (float): Proportion of instances in error peak
            - kat_main_peak_cov (float): Coverage at main genomic peak
            - kat_main_peak_height (int): Count of k-mers at main peak
            - kat_unique_kmers_prop (float): Proportion of singletons
            - kat_median_kmer_cov (float): Median k-mer coverage
            - kat_mean_kmer_cov (float): Mean k-mer coverage

    Notes:
        - Histogram format: coverage (int) \t count (int) per line
        - Error region: coverage ≤ error_cov_cutoff
        - Gracefully handles missing/corrupted files
    """
    metrics = {
        "kat_total_kmers": 0,
        "kat_total_kmer_instances": 0,
        "kat_error_peak_cov": 0.0,
        "kat_error_peak_prop": 0.0,
        "kat_main_peak_cov": 0.0,
        "kat_main_peak_height": 0,
        "kat_unique_kmers_prop": 0.0,
        "kat_median_kmer_cov": 0.0,
        "kat_mean_kmer_cov": 0.0,
    }

    if not os.path.exists(hist_file):
        logger.warning("Histogram file not found: %s", hist_file)
        return metrics

    try:
        # Read histogram data
        rows = []
        with open(hist_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        cov = int(parts[0])
                        count = int(parts[1])
                        rows.append((cov, count))
                    except ValueError:
                        continue

        if not rows:
            logger.warning("No valid data in histogram file: %s", hist_file)
            return metrics

        # Calculate totals
        total_distinct = sum(count for cov, count in rows)
        total_instances = sum(cov * count for cov, count in rows)

        metrics["kat_total_kmers"] = total_distinct
        metrics["kat_total_kmer_instances"] = total_instances

        if total_instances == 0:
            return metrics

        # Error peak analysis
        error_cov_cutoff = (
            config.get("kat", {}).get("thresholds", {}).get("error_cov_cutoff", 4)
        )
        error_instances = sum(
            cov * count for cov, count in rows if cov <= error_cov_cutoff
        )
        error_peak_prop = (
            error_instances / total_instances if total_instances > 0 else 0.0
        )

        # Find error peak coverage (mode within error region)
        error_rows = [(cov, count) for cov, count in rows if cov <= error_cov_cutoff]
        if error_rows:
            error_peak_cov, _ = max(error_rows, key=lambda x: x[1])
            metrics["kat_error_peak_cov"] = float(error_peak_cov)

        metrics["kat_error_peak_prop"] = error_peak_prop

        # Main peak analysis (among non-error region)
        main_rows = [(cov, count) for cov, count in rows if cov > error_cov_cutoff]
        if main_rows:
            main_peak_cov, main_peak_height = max(main_rows, key=lambda x: x[1])
            metrics["kat_main_peak_cov"] = float(main_peak_cov)
            metrics["kat_main_peak_height"] = main_peak_height

        # Singleton proportion
        singleton_count = sum(count for cov, count in rows if cov == 1)
        singleton_prop = singleton_count / total_distinct if total_distinct > 0 else 0.0
        metrics["kat_unique_kmers_prop"] = singleton_prop

        # Mean coverage
        mean_cov = total_instances / total_distinct if total_distinct > 0 else 0.0
        metrics["kat_mean_kmer_cov"] = mean_cov

        # Median coverage (cumulative approach)
        cumsum = 0
        target = total_distinct / 2
        for cov, count in sorted(rows, key=lambda x: x[0]):
            cumsum += count
            if cumsum >= target:
                metrics["kat_median_kmer_cov"] = float(cov)
                break

        logger.info(
            "Parsed histogram: %d distinct, %d instances",
            total_distinct,
            total_instances,
        )
        return metrics

    except OSError as e:
        logger.error("Error parsing histogram: %s", str(e))
        return metrics


def parse_kat_gcp(gcp_file: str, config: Dict) -> Dict[str, float]:
    """
    Parse KAT GC vs coverage matrix to extract contamination indicators.

    Args:
        gcp_file (str): Path to KAT GCP matrix file (.mx)
        config (dict): Configuration with multi-modal threshold

    Returns:
        dict: Metrics including:
            - kat_gcp_num_bins (int): Number of non-empty GC×cov bins
            - kat_gcp_top_bin_prop (float): Proportion in largest bin
            - kat_gcp_multi_modal (int): 1 if multiple high-coverage clusters, else 0
            - kat_gcp_lowcov_gc_prop (float): Proportion of low-cov + extreme GC

    Notes:
        - GCP matrix format: GC% (X-axis) vs coverage (Y-axis)
        - Multi-modal indicates possible contamination
        - Low coverage + extreme GC suggests foreign DNA
    """
    metrics = {
        "kat_gcp_num_bins": 0,
        "kat_gcp_top_bin_prop": 0.0,
        "kat_gcp_multi_modal": 0,
        "kat_gcp_lowcov_gc_prop": 0.0,
    }

    if not os.path.exists(gcp_file):
        logger.warning("GCP file not found: %s", gcp_file)
        return metrics

    try:
        # Parse matrix (typically tab-separated or space-separated values)
        bins = {}
        total_instances = 0

        with open(gcp_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split()
                if len(parts) >= 3:
                    try:
                        gc = float(parts[0])
                        cov = float(parts[1])
                        count = int(parts[2])

                        bins[(gc, cov)] = count
                        total_instances += count
                    except (ValueError, IndexError):
                        continue

        if not bins:
            logger.warning("No valid data in GCP file: %s", gcp_file)
            return metrics

        metrics["kat_gcp_num_bins"] = len(bins)

        # Top bin proportion
        if total_instances > 0:
            max_count = max(bins.values())
            metrics["kat_gcp_top_bin_prop"] = max_count / total_instances

        # Multi-modality check: count high-proportion bins at distinct GC bands
        multi_modal_threshold = (
            config.get("kat", {})
            .get("thresholds", {})
            .get("gcp_multi_modal_bin_prop", 0.1)
        )

        high_bins = {
            (gc, cov): count
            for (gc, cov), count in bins.items()
            if (count / total_instances) >= multi_modal_threshold
        }

        if len(high_bins) >= 2:
            metrics["kat_gcp_multi_modal"] = 1

        # Low coverage + extreme GC proportion
        main_peak_cov = (
            config.get("kat", {}).get("thresholds", {}).get("main_cov_low", 10)
        )
        lowcov_threshold = main_peak_cov * 0.2

        lowcov_extreme_gc = sum(
            count
            for (gc, cov), count in bins.items()
            if cov < lowcov_threshold and (gc < 0.25 or gc > 0.75)
        )

        metrics["kat_gcp_lowcov_gc_prop"] = (
            lowcov_extreme_gc / total_instances if total_instances > 0 else 0.0
        )

        logger.info(
            "Parsed GCP: %d bins, multi-modal=%d",
            len(bins),
            metrics["kat_gcp_multi_modal"],
        )
        return metrics

    except OSError as e:
        logger.error("Error parsing GCP: %s", str(e))
        return metrics


def parse_kat_comp(comp_file: str, config: Dict) -> Dict[str, float]:  # pylint: disable=unused-argument
    """
    Parse KAT composition analysis output.

    Placeholder for composition metrics extraction.

    Args:
        comp_file (str): Path to KAT comp output
        config (dict): Configuration (unused in placeholder)

    Returns:
        dict: Composition metrics (empty in placeholder)
    """
    return {}


def parse_kat_sect(sect_file: str, config: Dict) -> Dict[str, float]:  # pylint: disable=unused-argument
    """
    Parse KAT sector coverage analysis output.

    Placeholder for sector metrics extraction.

    Args:
        sect_file (str): Path to KAT sect output
        config (dict): Configuration (unused in placeholder)

    Returns:
        dict: Sector metrics (empty in placeholder)
    """
    return {}


def compute_kat_flags(metrics: Dict, config: Dict) -> Dict[str, int]:
    """
    Compute boolean flags from KAT metrics based on thresholds.

    Args:
        metrics (dict): KAT metrics from parsers
        config (dict): Configuration with thresholds

    Returns:
        dict: Boolean flags (0/1):
            - kat_flag_low_coverage
            - kat_flag_high_error
            - kat_flag_contamination
    """
    flags = {
        "kat_flag_low_coverage": 0,
        "kat_flag_high_error": 0,
        "kat_flag_contamination": 0,
    }

    try:
        thresholds = config.get("kat", {}).get("thresholds", {})

        # Low coverage flag
        main_cov_low = thresholds.get("main_cov_low", 10)
        if metrics.get("kat_main_peak_cov", 0) < main_cov_low:
            flags["kat_flag_low_coverage"] = 1

        # High error flag
        error_prop_warn = thresholds.get("error_prop_warn", 0.05)
        if metrics.get("kat_error_peak_prop", 0) > error_prop_warn:
            flags["kat_flag_high_error"] = 1

        # Contamination flag
        multi_modal = metrics.get("kat_gcp_multi_modal", 0)
        lowcov_gc_prop = metrics.get("kat_gcp_lowcov_gc_prop", 0)

        if multi_modal == 1 or lowcov_gc_prop > 0.02:
            flags["kat_flag_contamination"] = 1

        logger.info("Computed flags: %s", flags)
        return flags

    except OSError as e:
        logger.error("Error computing flags: %s", str(e))
        return flags


def run_kat_analysis(
    read1_file: str,
    read2_file: str,
    output_dir: str,
    config: Dict,
    threads: int = 1,
) -> Dict[str, float]:
    """
    Run complete KAT analysis pipeline (hist + gcp) and parse outputs.

    Args:
        read1_file (str): Path to R1 reads
        read2_file (str): Path to R2 reads
        output_dir (str): Sample output directory
        config (dict): Configuration with KAT settings
        threads (int): Number of threads

    Returns:
        dict: All KAT metrics and flags combined, or empty dict if KAT disabled/not found

    Notes:
        - Gracefully degradates if KAT not available
        - Returns zeros/defaults if any subcommand fails
        - Logs all operations for reproducibility
    """
    results = {}

    # Check if KAT is enabled in config
    kat_config = config.get("kat", {})
    if not kat_config.get("enabled", False):
        logger.info("KAT analysis disabled in config")
        return results

    # Get KAT binary
    kat_binary = get_kat_binary()
    if not kat_binary:
        logger.warning("KAT not available, skipping k-mer analysis")
        return results

    # Get KAT version for reproducibility
    kat_version = get_kat_version(kat_binary)
    logger.info("Using KAT: %s", kat_version)

    k = kat_config.get("k", 27)

    # Run histogram analysis
    if kat_config.get("run", {}).get("hist", True):
        hist_file = run_kat_hist(
            kat_binary, read1_file, read2_file, output_dir, k, threads
        )
        if hist_file:
            results.update(parse_kat_hist(hist_file, config))

    # Run GC×coverage analysis
    if kat_config.get("run", {}).get("gcp", True):
        gcp_file = run_kat_gcp(
            kat_binary, read1_file, read2_file, output_dir, k, threads
        )
        if gcp_file:
            results.update(parse_kat_gcp(gcp_file, config))

    # Compute flags
    flags = compute_kat_flags(results, config)
    results.update(flags)

    # Store KAT metadata for reproducibility
    results["kat_k"] = k
    results["kat_version"] = kat_version or "unknown"

    logger.info("KAT analysis complete: %d metrics extracted", len(results))
    return results
