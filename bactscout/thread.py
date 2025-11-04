"""
Core processing module for individual sample analysis and QC evaluation.

This module handles the orchestration of quality control (QC) analysis for individual bacterial
samples. It coordinates calls to external tools (fastp for read QC, Sylph for species detection,
stringMLST for typing), aggregates results, and evaluates samples against configurable thresholds.

Key Responsibilities:
    - Sample processing orchestration (run_one_sample)
    - Quality metrics evaluation (handle_fastp_results, handle_species_coverage, etc.)
    - Species and coverage analysis
    - MLST typing integration
    - Result aggregation and final status determination

Workflow for Each Sample:
    1. Initialize blank result dictionary
    2. Run Sylph for species detection
    3. Run fastp for read quality and statistics
    4. Process fastp results with thresholds
    5. Handle species coverage estimation
    6. Evaluate genome size and coverage
    7. Run MLST if single species identified
    8. Determine final QC pass/fail status
    9. Write results to summary CSV

Key Classes:
    - None (functional module)

Key Functions:
    - run_one_sample(): Main orchestrator for processing a single sample
    - blank_sample_results(): Initialize result dictionary
    - handle_fastp_results(): Evaluate read quality metrics
    - handle_species_coverage(): Process species detection and abundance
    - handle_genome_size(): Calculate coverage and GC content metrics
    - handle_mlst_results(): Run and process MLST typing
    - final_status_pass(): Determine overall sample QC status

Dependencies:
    - bactscout.software.run_fastp: Read quality control
    - bactscout.software.run_sylph: Species detection
    - bactscout.software.run_stringmlst: MLST typing
    - bactscout.util: Formatting and output utilities
"""

import json
import os

from bactscout.resource_monitor import ResourceMonitor
from bactscout.software.run_fastp import run_command as run_fastp
from bactscout.software.run_stringmlst import run_command as run_mlst
from bactscout.software.run_sylph import extract_species_from_report
from bactscout.software.run_sylph import run_command as run_sylph
from bactscout.util import format_summary_headers, print_message


def blank_sample_results(sample_id):
    """
    Generate a blank results dictionary for a given sample.

    This function returns a dictionary containing default values for various sample metrics,
    including read counts, base counts, quality scores, GC content, species identification,
    coverage estimates, MLST typing, reference genome information, and extended FastP QC metrics
    (duplication rate, N-content, adapter detection). All fields are initialized to indicate
    that no reads have been processed and no analysis has been performed.

    Args:
        sample_id (str or int): Unique identifier for the sample.

    Returns:
        dict: A dictionary with default values for all expected sample result fields including:
            - Basic read metrics (counts, quality scores, lengths)
            - Species identification and abundance
            - Coverage estimates (sylph-based and calculated)
            - MLST typing results
            - GC content and genome size metrics
            - Contamination assessment
            - Extended FastP metrics (duplication, N-content, adapter detection)
    """
    return {
        "sample_id": sample_id,
        "a_final_status": "FAILED",
        "read_total_reads": 0,
        "read_total_bases": 0,
        "read_q20_bases": 0,
        "read_q30_bases": 0,
        "read_q20_rate": 0.0,
        "read_q30_rate": 0.0,
        "read_q30_status": "FAILED",
        "read_q30_message": "No reads processed. Cannot determine quality metrics.",
        "read1_mean_length": 0,
        "read2_mean_length": 0,
        "read_length_status": "FAILED",
        "read_length_message": "No reads processed. Cannot determine read lengths.",
        "gc_content": 0.0,
        "species": "",
        "species_abundance": "",
        "species_coverage": "",
        "coverage_estimate": 0,
        "genome_size_expected": 0,
        "coverage_status": "FAILED",
        "coverage_message": "No reads processed. Cannot estimate genome size or coverage.",
        "gc_content_lower": 0,
        "gc_content_upper": 0,
        "gc_content_status": "FAILED",
        "gc_content_message": "No reads processed. Cannot determine expected GC content range.",
        "species_status": "FAILED",
        "species_message": "No reads processed. Cannot determine species.",
        "mlst_st": None,
        "mlst_status": "WARNING",
        "mlst_message": "Cannot determine MLST.",
        "contamination_status": "FAILED",
        "contamination_message": "No reads processed. Cannot determine contamination.",
        "coverage_alt_estimate": 0,
        "coverage_alt_message": "No reads processed. Cannot estimate alternative coverage.",
        "coverage_alt_status": "FAILED",
        "genome_file_path": "",
        "genome_file": "",
        # Fastp QC Metrics - Duplication
        "duplication_rate": 0.0,
        "duplication_status": "FAILED",
        "duplication_message": "No reads processed. Cannot determine duplication rate.",
        # Fastp QC Metrics - N-Content
        "n_content_rate": 0.0,
        "n_content_status": "FAILED",
        "n_content_message": "No reads processed. Cannot determine N-content.",
        # Fastp QC Metrics - Adapter Detection
        "adapter_detection_status": "FAILED",
        "adapter_detection_message": "No reads processed. Cannot verify adapter detection.",
    }


def run_one_sample(
    sample_id,
    read1_file,
    read2_file,
    output_dir,
    config,
    threads=1,
    message=False,
    report_resources=False,
    write_json=False,
):
    """
    Execute comprehensive QC analysis pipeline for a single bacterial sample.

    Orchestrates the complete analysis workflow including species detection, read quality
    evaluation, genome coverage estimation, and MLST typing. Integrates results from
    multiple external tools and evaluates samples against configurable quality thresholds.

    Args:
        sample_id (str): Unique identifier for the sample.
        read1_file (str): Path to the forward reads FASTQ file (R1).
        read2_file (str): Path to the reverse reads FASTQ file (R2).
        output_dir (str): Directory where sample output files and results will be saved.
        config (dict): Configuration dictionary containing thresholds, database paths, and tool settings.
        threads (int, optional): Number of threads for parallel execution. Defaults to 1.
        message (bool, optional): If True, print status messages. Defaults to False.
        report_resources (bool, optional): If True, track and report resource usage. Defaults to False.

    Returns:
        dict: Comprehensive results dictionary containing:
            - Sample identification and input metrics
            - Read quality scores (Q30, Q20 rates, read lengths)
            - Species identification and abundance
            - Coverage estimates (both sylph-based and calculated)
            - MLST typing results (if applicable)
            - GC content evaluation
            - Contamination assessment
            - Extended FastP metrics (duplication rate, N-content, adapter detection)
            - Overall QC pass/fail status with descriptive messages
            - Resource usage metrics if report_resources=True (threads, memory, duration)

    Workflow:
        1. Initialize blank results dictionary
        2. Run Sylph for species detection and abundance
        3. Run FastP for read QC and statistics
        4. Process FastP results (Q30, read length, duplication, N-content, adapters)
        5. Handle species coverage and contamination evaluation
        6. Calculate genome size and coverage metrics
        7. Run MLST if single species or dominant species identified
        8. Determine final QC pass/fail status
        9. Track resource usage if enabled
        10. Write summary CSV file

    Notes:
        - Creates sample output directory if it doesn't exist
        - Supports Nextflow environment variable detection (NXF_TASK_WORKDIR)
        - MLST analysis only performed for single-species or uncontaminated samples
        - Coverage evaluation uses both direct Sylph output and computed estimates
        - Final status determined by pass/fail evaluation of all QC metrics
        - Handles missing input files gracefully with error messages
    """
    # Start resource monitoring if requested
    resource_monitor = None
    if report_resources:
        resource_monitor = ResourceMonitor()
        resource_monitor.start()

    if message:
        print_message(f"Running analysis for {sample_id}", "info")
    # Create output directory if it doesn't exist #
    sample_output_dir = f"{output_dir}/{sample_id}"
    # Are we in Nextflow? Maybe check NXF_TASK_WORKDIR?
    if os.getenv("NXF_TASK_WORKDIR"):
        sample_output_dir = os.path.join(
            os.getenv("NXF_TASK_WORKDIR", ""), os.path.basename(sample_output_dir)
        )
        if message:
            print_message(
                f"Using Nextflow path for output: {sample_output_dir}", "info"
            )

    if not os.path.exists(sample_output_dir):
        os.makedirs(sample_output_dir, exist_ok=True)
    # Are we in Nextflow? Maybe check NXF_TASK_WORKDIR?
    if not os.path.exists(read1_file):
        read1_file = os.path.join(
            os.getenv("NXF_TASK_WORKDIR", ""), os.path.basename(read1_file)
        )
        if message:
            print_message(f"Using Nextflow path for R1: {read1_file}", "info")
    if not os.path.exists(read2_file):
        read2_file = os.path.join(
            os.getenv("NXF_TASK_WORKDIR", ""), os.path.basename(read2_file)
        )
        if message:
            print_message(f"Using Nextflow path for R2: {read2_file}", "info")

    # Check R1 and R2 files exist
    if not os.path.exists(read1_file):
        if message:
            print_message(f"Error: R1 file {read1_file} does not exist.", "error")
        return {"status": "failed", "message": f"R1 file {read1_file} not found."}
    if not os.path.exists(read2_file):
        if message:
            print_message(f"Error: R2 file {read2_file} does not exist.", "error")
        return {"status": "failed", "message": f"R2 file {read2_file} not found."}
    # Initialize final results with blank values
    final_results = blank_sample_results(sample_id)
    sylph_result = run_sylph(
        read1_file, read2_file, sample_output_dir, config, threads=threads
    )
    species_abundance, genome_file_path = extract_species_from_report(
        sylph_result.get("sylph_report")
    )
    final_results["genome_file_path"] = genome_file_path

    fastp_result = run_fastp(
        read1_file, read2_file, sample_output_dir, config, threads=threads
    )
    fastp_stats = get_fastp_results(fastp_result)
    fastp_stats = handle_fastp_results(fastp_stats, config)
    fastp_stats = handle_duplication_results(fastp_stats, config)
    fastp_stats = handle_n_content_results(fastp_stats, config)
    fastp_stats = handle_adapter_detection(fastp_stats, config)
    final_results.update(fastp_stats)

    final_results, species = handle_species_coverage(
        species_abundance, final_results, config
    )
    if species:
        final_results = handle_genome_size(species, fastp_stats, final_results, config)
    # If other species > 10% abundance, skip MLST
    not_contaminated = True
    has_multiple_species = len(species) > 1
    if has_multiple_species:
        # Sum up abundance of non-top species
        non_top_abundance = sum([s[1] for s in species_abundance[1:]])
        if non_top_abundance > config.get(
            "contamination_fail_threshold", config.get("contamination_threshold", 10)
        ):
            final_results["species_status"] = "FAILED"
            final_results["species_message"] = (
                f"Multiple species detected with significant abundance ({non_top_abundance:.2f}%). Skipping MLST."
            )
            not_contaminated = False

    # If no species were detected, ensure MLST is skipped and mark species as failed
    if not species:
        final_results["species_status"] = final_results.get("species_status", "FAILED")
        if not final_results.get("species_message"):
            final_results["species_message"] = "No species detected."
    else:
        # species is a list of detected species; use the top species for MLST
        if not_contaminated:
            top_species = species[0]
            final_results["species_status"] = "PASSED"
            if not has_multiple_species:
                final_results["species_message"] = "Single species detected."
            else:
                final_results["species_message"] = (
                    "Multiple species detected. Using the top species for MLST."
                )
                final_results["species_status"] = "WARNING"
            final_results = handle_mlst_results(
                final_results=final_results,
                config=config,
                species=top_species,
                read1_file=read1_file,
                read2_file=read2_file,
                sample_output_dir=sample_output_dir,
                message=message,
            )
        else:
            final_results["species_status"] = "FAILED"
    final_results["a_final_status"] = final_status_pass(final_results)

    # Stop resource monitoring and add stats to results
    if resource_monitor:
        resource_monitor.end()
        stats = resource_monitor.get_stats()
        final_results["resource_threads_peak"] = stats.get("peak_threads", 0)
        final_results["resource_memory_peak_mb"] = stats.get("peak_memory_mb", 0.0)
        final_results["resource_memory_avg_mb"] = stats.get("avg_memory_mb", 0.0)
        final_results["resource_duration_sec"] = stats.get("duration_sec", 0.0)

    write_summary_file(
        final_results, sample_id, sample_output_dir, write_json=write_json
    )

    return {
        "status": "success",
        "sample_id": sample_id,
        "results": final_results,
    }


def write_summary_file(
    final_results, sample_id, sample_output_dir, write_json: bool = False
):
    """
    Write sample analysis results to a CSV summary file with header validation.

    Creates a CSV file named '{sample_id}_summary.csv' containing all analysis results
    for the sample. Validates headers against expected schema from blank_sample_results()
    and formats output using preferred header ordering.

    Args:
        final_results (dict): Complete results dictionary with all QC metrics and analysis outcomes.
            Keys become CSV column headers, values become the data row.
        sample_id (str): Unique sample identifier used to name the output file.
        sample_output_dir (str): Directory path where the summary CSV will be saved.

    Returns:
        None

    Side Effects:
        - Creates {sample_id}_summary.csv in sample_output_dir
        - Prints warnings if headers don't match expected schema
        - Reports missing headers (expected but not found in results)
        - Reports extra headers (found in results but not expected)

    Notes:
        - Header validation uses set operations to identify discrepancies
        - Preferred header ordering applied via format_summary_headers()
        - Single row CSV format (header + one data row)
        - Handles missing values gracefully (empty strings in CSV)
    """
    final_output_file = os.path.join(sample_output_dir, f"{sample_id}_summary.csv")
    pref_header_list = format_summary_headers()
    with open(final_output_file, "w", encoding="utf-8") as f:
        # Write header
        headers = list(final_results.keys())
        # Warn if headers are not the same as blank_sample_results()
        if headers != list(blank_sample_results(sample_id).keys()):
            print_message(
                f"Warning: Headers in final results do not match expected headers for sample {sample_id}",
                "warning",
            )
            # Show the difference between actual and expected headers
            expected_headers = set(blank_sample_results(sample_id).keys())
            actual_headers = set(headers)
            missing_headers = expected_headers - actual_headers
            extra_headers = actual_headers - expected_headers
            if missing_headers:
                print_message(f"Missing headers: {missing_headers}", "warning")
            if extra_headers:
                print_message(f"Extra headers: {extra_headers}", "warning")
        # Sort: sample_id first, then *_status, then alphabetical
        headers = sorted(
            final_results.keys(),
            key=lambda x: (x != "sample_id", not x.endswith("_status"), x),
            # or: (0 if x == "sample_id" else 1, 0 if x.endswith("_status") else 1, x)
        )
        # Order by pref_header_list
        headers = sorted(
            headers,
            key=lambda x: pref_header_list.index(x)
            if x in pref_header_list
            else len(pref_header_list),
        )

        f.write(",".join(headers) + "\n")
        # Write values
        values = [
            str(final_results[h]) if final_results[h] is not None else ""
            for h in headers
        ]
        f.write(",".join(values) + "\n")

    # Optionally write a JSON copy of the summary for downstream tools
    if write_json:
        json_file = os.path.join(sample_output_dir, f"{sample_id}_summary.json")
        try:
            with open(json_file, "w", encoding="utf-8") as jf:
                json.dump(final_results, jf, ensure_ascii=False, indent=2)
        except Exception as e:
            print_message(f"Failed to write JSON summary {json_file}: {e}", "warning")


def handle_fastp_results(fastp_results, config):
    """
    Evaluate FastP read quality metrics against configurable thresholds.

    Assesses Q30 rate and read length using two-tier threshold system (WARNING/FAIL).
    Updates the fastp_results dictionary with status fields and descriptive messages.

    Args:
        fastp_results (dict): FastP metrics dictionary containing:
            - read_total_reads (int): Total number of reads processed
            - read_q30_rate (float): Proportion of bases with Q30+ quality (0.0-1.0)
            - read_mean_length (float): Average read length in base pairs
        config (dict): Configuration dictionary with thresholds:
            - q30_warn_threshold (float): Q30 rate below which WARNING is triggered (default: 0.70)
            - q30_fail_threshold (float): Q30 rate below which FAILED is triggered (default: 0.60)
            - read_length_warn_threshold (int): Read length below which WARNING is triggered (default: 100)
            - read_length_fail_threshold (int): Read length below which FAILED is triggered (default: 75)

    Returns:
        dict: Updated fastp_results dictionary with added fields:
            - read_q30_status (str): "PASSED", "WARNING", or "FAILED"
            - read_q30_message (str): Descriptive message with rate and thresholds
            - read_length_status (str): "PASSED", "WARNING", or "FAILED"
            - read_length_message (str): Descriptive message with length and thresholds

    Status Logic:
        - PASSED: Metric >= FAIL threshold (meets minimum quality)
        - WARNING: FAIL threshold > metric >= WARN threshold (borderline quality)
        - FAILED: Metric < WARN threshold OR total_reads == 0 (unacceptable quality)

    Notes:
        - Handles percentage values (>1) by converting to decimals for Q30
        - Zero total_reads results in automatic FAILED status
        - Backward compatible with legacy single-threshold configurations
    """
    # Handle Q30 thresholds with backward compatibility
    q30_fail_threshold = config.get("q30_fail_threshold", 0.60)
    q30_warn_threshold = config.get("q30_warn_threshold", 0.70)

    if q30_fail_threshold > 1:
        q30_fail_threshold /= 100
    if q30_warn_threshold > 1:
        q30_warn_threshold /= 100

    # Handle read length thresholds with backward compatibility
    read_length_fail_threshold = config.get("read_length_fail_threshold", 75)
    read_length_warn_threshold = config.get("read_length_warn_threshold", 100)

    # Q30 status and message
    total_reads = fastp_results.get("read_total_reads", 0)
    q30_rate = fastp_results.get("read_q30_rate", 0.0)

    if total_reads == 0:
        fastp_results["read_q30_status"] = "FAILED"
        fastp_results["read_q30_message"] = (
            "No reads processed. Cannot determine quality metrics."
        )
    elif q30_rate >= q30_fail_threshold:
        fastp_results["read_q30_status"] = "PASSED"
        fastp_results["read_q30_message"] = (
            f"Q30 rate {q30_rate:.2f} meets threshold ({q30_fail_threshold})."
        )
    elif q30_rate >= q30_warn_threshold:
        fastp_results["read_q30_status"] = "WARNING"
        fastp_results["read_q30_message"] = (
            f"Q30 rate {q30_rate:.2f} falls between warning ({q30_warn_threshold}) and fail ({q30_fail_threshold}) thresholds."
        )
    else:
        fastp_results["read_q30_status"] = "FAILED"
        fastp_results["read_q30_message"] = (
            f"Q30 rate {q30_rate:.2f} below warning threshold ({q30_warn_threshold})."
        )

    # Read length status and message
    read1_len = fastp_results.get("read1_mean_length", 0)
    read2_len = fastp_results.get("read2_mean_length", 0)

    if total_reads == 0:
        fastp_results["read_length_status"] = "FAILED"
        fastp_results["read_length_message"] = (
            "No reads processed. Cannot determine read lengths."
        )
    elif (
        read1_len >= read_length_fail_threshold
        and read2_len >= read_length_fail_threshold
    ):
        fastp_results["read_length_status"] = "PASSED"
        fastp_results["read_length_message"] = (
            f"Read1 mean length {read1_len}; Read2 mean length {read2_len} meet threshold (>{read_length_fail_threshold})."
        )
    elif (
        read1_len >= read_length_warn_threshold
        and read2_len >= read_length_warn_threshold
    ):
        fastp_results["read_length_status"] = "WARNING"
        fastp_results["read_length_message"] = (
            f"Read1 mean length {read1_len}; Read2 mean length {read2_len} falls between warning (>{read_length_warn_threshold}) and fail (>{read_length_fail_threshold}) thresholds."
        )
    else:
        fastp_results["read_length_status"] = "FAILED"
        fastp_results["read_length_message"] = (
            f"Read1 mean length {read1_len}; Read2 mean length {read2_len} below warning threshold (>{read_length_warn_threshold})."
        )

    return fastp_results


def handle_duplication_results(fastp_results, config):
    """
    Evaluate read duplication rate against quality thresholds.

    High duplication rates indicate PCR bias, low library complexity, or sequencing artifacts.
    Uses two-tier threshold system to classify duplication severity.

    Args:
        fastp_results (dict): FastP metrics containing:
            - duplication_rate (float): Proportion of duplicate reads (0.0-1.0)
            - read_total_reads (int): Total reads processed
        config (dict): Configuration with thresholds:
            - duplication_warn_threshold (float): Rate above which WARNING triggered (default: 0.20 = 20%)
            - duplication_fail_threshold (float): Rate above which FAILED triggered (default: 0.30 = 30%)

    Returns:
        dict: Updated fastp_results with:
            - duplication_status (str): "PASSED", "WARNING", or "FAILED"
            - duplication_message (str): Descriptive message with rate and thresholds

    Status Logic:
        - PASSED: duplication_rate <= WARN threshold (acceptable duplication)
        - WARNING: WARN < duplication_rate <= FAIL threshold (moderate duplication, potential issues)
        - FAILED: duplication_rate > FAIL threshold OR total_reads == 0 (excessive duplication)

    Notes:
        - Duplication rates reported as both decimal and percentage in messages
        - Zero reads results in automatic FAILED status
        - Thresholds stored as decimals (0.20 = 20%)
    """
    duplication_warn_threshold = config.get("duplication_warn_threshold", 0.20)
    duplication_fail_threshold = config.get("duplication_fail_threshold", 0.30)

    duplication_rate = fastp_results.get("duplication_rate", 0.0)
    total_reads = fastp_results.get("read_total_reads", 0)

    if total_reads == 0:
        fastp_results["duplication_status"] = "FAILED"
        fastp_results["duplication_message"] = (
            "No reads processed. Cannot determine duplication rate."
        )
    elif duplication_rate <= duplication_warn_threshold:
        fastp_results["duplication_status"] = "PASSED"
        fastp_results["duplication_message"] = (
            f"Duplication rate {duplication_rate:.4f} ({duplication_rate*100:.2f}%) "
            f"is below warning threshold ({duplication_warn_threshold*100:.1f}%)."
        )
    elif duplication_rate <= duplication_fail_threshold:
        fastp_results["duplication_status"] = "WARNING"
        fastp_results["duplication_message"] = (
            f"Duplication rate {duplication_rate:.4f} ({duplication_rate*100:.2f}%) "
            f"falls between warning ({duplication_warn_threshold*100:.1f}%) and fail ({duplication_fail_threshold*100:.1f}%) thresholds. "
            f"May indicate PCR bias or library complexity issues."
        )
    else:
        fastp_results["duplication_status"] = "FAILED"
        fastp_results["duplication_message"] = (
            f"Duplication rate {duplication_rate:.4f} ({duplication_rate*100:.2f}%) "
            f"exceeds fail threshold ({duplication_fail_threshold*100:.1f}%). "
            f"High PCR bias detected."
        )

    return fastp_results


def handle_n_content_results(fastp_results, config):
    """
    Evaluate N-content (ambiguous base calls) in read data.

    High N-content indicates sequencing quality issues, base-calling uncertainty,
    or low-coverage regions. N bases represent positions where the sequencer could
    not confidently call A, T, G, or C.

    Args:
        fastp_results (dict): FastP metrics containing:
            - n_content_rate (float): Percentage of N bases in reads
            - read_total_reads (int): Total reads processed
        config (dict): Configuration with threshold:
            - n_content_threshold (float): Maximum acceptable N-content as fraction (default: 0.001 = 0.1%)

    Returns:
        dict: Updated fastp_results with:
            - n_content_status (str): "PASSED", "WARNING", or "FAILED"
            - n_content_message (str): Descriptive message with rate and threshold

    Status Logic:
        - PASSED: n_content_rate <= threshold * 100 (acceptable N-content)
        - WARNING: n_content_rate > threshold * 100 (elevated N-content, quality concerns)
        - FAILED: total_reads == 0 (no data to evaluate)

    Notes:
        - Threshold stored as fraction (0.001) but n_content_rate is percentage
        - Multiplies threshold by 100 for comparison with percentage rate
        - Zero reads results in automatic FAILED status
    """
    n_content_threshold = config.get("n_content_threshold", 0.001)

    n_content_rate = fastp_results.get("n_content_rate", 0.0)
    total_reads = fastp_results.get("read_total_reads", 0)

    if total_reads == 0:
        fastp_results["n_content_status"] = "FAILED"
        fastp_results["n_content_message"] = (
            "No reads processed. Cannot determine N-content."
        )
    elif n_content_rate <= (n_content_threshold * 100):
        fastp_results["n_content_status"] = "PASSED"
        fastp_results["n_content_message"] = (
            f"N-content {n_content_rate:.4f}% is below threshold ({n_content_threshold*100:.2f}%)."
        )
    else:
        fastp_results["n_content_status"] = "WARNING"
        fastp_results["n_content_message"] = (
            f"N-content {n_content_rate:.4f}% exceeds threshold ({n_content_threshold*100:.2f}%). "
            f"Indicates base-calling uncertainty."
        )

    return fastp_results


def handle_adapter_detection(fastp_results, config):
    """
    Updates fastp_results with adapter contamination status based on overrepresented sequences.

    Checks for presence of overrepresented sequences which may indicate adapter contamination
    or other contaminants that weren't properly removed.

    Args:
        fastp_results (dict): Dictionary containing fastp metrics with composition_data.
        config (dict): Configuration dictionary with thresholds:
            - adapter_overrep_threshold (int): Maximum number of overrepresented sequences allowed (default: 5)

    Returns:
        dict: Updated fastp_results with adapter_detection_status and adapter_detection_message.
    """
    adapter_overrep_threshold = config.get("adapter_overrep_threshold", 5)
    total_reads = fastp_results.get("read_total_reads", 0)

    # Get overrepresented sequences from composition_data
    composition_data = fastp_results.get("read1_before_filtering", {})
    overrep_sequences = composition_data.get("overrepresented_sequences", [])
    overrep_count = len(overrep_sequences) if overrep_sequences else 0

    if total_reads == 0:
        fastp_results["adapter_detection_status"] = "FAILED"
        fastp_results["adapter_detection_message"] = (
            "No reads processed. Cannot check for adapter contamination."
        )
    elif overrep_count == 0:
        fastp_results["adapter_detection_status"] = "PASSED"
        fastp_results["adapter_detection_message"] = (
            "No overrepresented sequences detected."
        )
    elif overrep_count <= adapter_overrep_threshold:
        fastp_results["adapter_detection_status"] = "WARNING"
        fastp_results["adapter_detection_message"] = (
            f"{overrep_count} overrepresented sequence(s) detected. "
            f"May indicate minor adapter contamination or repetitive sequences."
        )
    else:
        fastp_results["adapter_detection_status"] = "FAILED"
        fastp_results["adapter_detection_message"] = (
            f"{overrep_count} overrepresented sequences detected (threshold: {adapter_overrep_threshold}). "
            f"Indicates significant adapter contamination or other contaminants."
        )

    return fastp_results


def handle_species_coverage(species_abundance, final_results, config):
    """
    Process Sylph species detection results and evaluate contamination and coverage.

    Integrates species abundance data from Sylph into results, evaluates sample contamination
    based on dominant species percentage, and assesses genome coverage against quality thresholds.
    Handles cases with no species, single species, or multiple species detected.

    Args:
        species_abundance (list): Sorted list of tuples from Sylph (highest abundance first):
            - [0] (str): Species scientific name
            - [1] (float): Percentage abundance (0-100)
            - [2] (float): Estimated genome coverage from Sylph
        final_results (dict): Results dictionary to update with species and QC data.
        config (dict): Configuration with thresholds:
            - coverage_fail_threshold (int): Minimum coverage for PASS (default: 30x)
            - coverage_warn_threshold (int): Minimum coverage for WARNING (default: 20x)
            - contamination_fail_threshold (int): Maximum secondary species % for PASS (default: 10%)
            - contamination_warn_threshold (int): Maximum secondary species % for WARNING (default: 5%)

    Returns:
        tuple: (updated_final_results, species_list)
            - updated_final_results (dict): Results with added fields:
                * species_top: Most abundant species name
                * species_top_abundance: Abundance percentage of top species
                * species_count: Total number of species detected
                * coverage_estimate: Sylph coverage estimate for top species
                * coverage_status: "PASSED", "WARNING", or "FAILED"
                * coverage_message: Descriptive message
                * contamination_status: "PASSED", "WARNING", or "FAILED"
                * contamination_message: Descriptive message
            - species_list (list): Names of all detected species (empty if none)

    Status Logic - Coverage:
        - PASSED: coverage >= FAIL threshold
        - WARNING: WARN <= coverage < FAIL threshold
        - FAILED: coverage < WARN threshold OR no species detected

    Status Logic - Contamination:
        - PASSED: (100 - top_species_pct) <= WARN threshold (minimal secondary species)
        - WARNING: WARN < (100 - top_species_pct) <= FAIL threshold (moderate contamination)
        - FAILED: (100 - top_species_pct) > FAIL threshold (high contamination)

    Notes:
        - Contamination evaluated as percentage NOT belonging to top species
        - Coverage uses Sylph's direct estimate from top species
        - Multi-species samples flagged in contamination message
        - Backward compatible with legacy single-threshold config
        - Empty species_abundance results in FAILED coverage status
    """
    # Handle coverage thresholds with backward compatibility
    coverage_fail_threshold = config.get("coverage_fail_threshold")
    coverage_warn_threshold = config.get("coverage_warn_threshold")

    if coverage_fail_threshold is None:
        # Legacy mode: use threshold as fail_threshold
        coverage_fail_threshold = config.get("coverage_threshold", 30)
        coverage_warn_threshold = (
            coverage_fail_threshold * 0.67
        )  # Default warn at ~67% of fail

    # Handle contamination thresholds with backward compatibility
    contamination_fail_threshold = config.get("contamination_fail_threshold")
    contamination_warn_threshold = config.get("contamination_warn_threshold")

    if contamination_fail_threshold is None:
        # Legacy mode: use threshold as fail_threshold
        contamination_fail_threshold = config.get("contamination_threshold", 10)
        contamination_warn_threshold = (
            contamination_fail_threshold * 0.50
        )  # Default warn at 50% of fail

    if not species_abundance:
        final_results["coverage_status"] = "FAILED"
        final_results["contamination_status"] = "FAILED"
        final_results["coverage_message"] = (
            "No species detected. Cannot estimate genome size or coverage."
        )
        final_results["gc_content_message"] = (
            "No species detected. Cannot determine expected GC content range."
        )
        final_results["species_status"] = "FAILED"
        final_results["species_message"] = "No species detected."
        return final_results, []
    # species is the first element of the tuple, sorted by abundance
    species = [
        s[0] for s in sorted(species_abundance, key=lambda x: x[1], reverse=True)
    ]
    if len(species) == 1:
        final_results["species_status"] = "PASSED"
        final_results["species_message"] = ""
    elif len(species) > 1:
        final_results["species_status"] = "WARNING"
        final_results["species_message"] = (
            "Multiple species detected. Using the top species for genome size and coverage estimation."
        )
    final_results["species"] = ";".join(species)
    final_results["species_abundance"] = ";".join(
        [str(s[1]) for s in species_abundance]
    )
    final_results["species_coverage"] = ";".join([str(s[2]) for s in species_abundance])
    top_species = species_abundance[0] if species_abundance else None

    # Evaluate coverage with WARNING and FAIL thresholds
    if top_species and top_species[2] >= coverage_fail_threshold:
        final_results["coverage_status"] = "PASSED"
        final_results["coverage_estimate"] = round(top_species[2], 2)
        final_results["coverage_message"] = (
            f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x meets the threshold of {coverage_fail_threshold}x."
        )
    elif top_species and top_species[2] >= coverage_warn_threshold:
        final_results["coverage_status"] = "WARNING"
        final_results["coverage_estimate"] = round(top_species[2], 2)
        final_results["coverage_message"] = (
            f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x falls between warning ({coverage_warn_threshold}x) and fail ({coverage_fail_threshold}x) thresholds."
        )
    else:
        final_results["coverage_estimate"] = (
            round(top_species[2], 2) if top_species else 0
        )
        if top_species is None:
            final_results["coverage_message"] = (
                "No species detected. Cannot estimate genome size or coverage."
            )
        else:
            final_results["coverage_message"] = (
                f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x falls below warning threshold ({coverage_warn_threshold}x)."
            )
        final_results["coverage_status"] = "FAILED"

    # Evaluate contamination with WARNING and FAIL thresholds
    # Contamination is calculated as (100 - top_species_percentage)
    # Lower top species percentage = higher contamination
    if top_species and top_species[1] > (100 - contamination_fail_threshold):
        final_results["contamination_status"] = "PASSED"
        final_results["contamination_message"] = "OK"
    elif top_species and top_species[1] > (100 - contamination_warn_threshold):
        final_results["contamination_status"] = "WARNING"
        final_results["contamination_message"] = (
            f"Top species purity {top_species[1]:.2f}% falls between warning ({100 - contamination_warn_threshold}%) and fail ({100 - contamination_fail_threshold}%) thresholds."
        )
    else:
        if top_species is None:
            final_results["contamination_message"] = (
                "No species detected. Cannot determine contamination."
            )
        else:
            final_results["contamination_message"] = (
                f"Top species purity {top_species[1]:.2f}% falls below warning threshold ({100 - contamination_warn_threshold}%)."
            )
        final_results["contamination_status"] = "FAILED"
    return final_results, species


def handle_mlst_results(
    final_results,
    config,
    species,
    read1_file,
    read2_file,
    sample_output_dir,
    message,
):
    """
    Execute MLST typing analysis and update results with typing data.

    Performs Multi-Locus Sequence Typing (stringMLST) on samples with a single identified
    species. Maps the detected species to the appropriate MLST database directory and runs
    the typing analysis. Updates results with sequence type (ST) information and status.

    Args:
        final_results (dict): Results dictionary to update with MLST findings.
        config (dict): Configuration dictionary containing:
            - mlst_species (dict): Mapping of species database names to scientific names
            - bactscout_dbs_path (str): Path to the MLST database directory
        species (str): Scientific name of the identified species (e.g., "Escherichia coli").
        read1_file (str): Path to forward reads FASTQ file.
        read2_file (str): Path to reverse reads FASTQ file.
        sample_output_dir (str): Directory for MLST output files.
        message (bool): If True, print warning messages.
        threads (int, optional): Number of threads for stringMLST. Defaults to 1.

    Returns:
        dict: Updated final_results dictionary with:
            - mlst_st: Sequence type number (or None if not found)
            - mlst_status: "PASSED" (valid ST), "WARNING" (no ST found), or original status
            - mlst_message: Descriptive message about MLST results

    Notes:
        - Only processes species with available MLST databases
        - Species name mapping handles variations (e.g., with/without subspecies)
        - Sets status to "WARNING" if database not found or ST not identified
        - Invalid ST values (ST < 0) marked as "WARNING"
    """
    # Run ARIBA if a single species is identified
    # Need to determine the species_db path
    species_key = None
    # This locates the  correct fodler name for the mlst Db in cases where species exactly matches.
    # e.g klebsiella_pneumoniae: 'Klebsiella pneumoniae'
    for key, value in config["mlst_species"].items():
        if value == species:
            species_key = key
            break
    # In case the species name has a number at the end e.g Escherichia coli#1 or Neisseria spp.
    # In this case species dir will be species.replace(" ", "_").lower()
    if not species_key:
        species_simple = species.replace(" ", "_").lower()
        if species_simple in config["mlst_species"]:
            species_key = species_simple

    if species_key:
        species_db_path = os.path.join(
            config["bactscout_dbs_path"], species_key, species_key
        )
        mlst_result = run_mlst(
            read1_file,
            read2_file,
            species_db_path,
            sample_output_dir,
            config,
        )
        # If mlst_results has error key, MLST failed
        if mlst_result.get("error"):
            final_results["mlst_st"] = None
            final_results["mlst_status"] = "WARNING"
            final_results["mlst_message"] = (
                f"MLST analysis failed: {mlst_result['error']}"
            )
            if message:
                print_message(
                    f"MLST analysis failed for species: {species}. Error: {mlst_result['error']}",
                    "warning",
                )
            return final_results
        # Check MLST results
        stringmlst_results = mlst_result.get("stringmlst_results", {})

        # Check if there's an error in the MLST results
        if "error" in stringmlst_results:
            final_results["mlst_st"] = None
            final_results["mlst_status"] = "WARNING"
            final_results["mlst_message"] = (
                f"MLST analysis failed: {stringmlst_results['error']}"
            )
        # Check if ST field exists (even if empty)
        elif "ST" in stringmlst_results:
            st_value = stringmlst_results["ST"]
            # Store the ST value, but convert empty/whitespace to None
            final_results["mlst_st"] = (
                st_value if st_value and st_value.strip() else None
            )

            # Try to validate the ST value
            if st_value and st_value.strip():  # Non-empty string
                try:
                    st_int = int(st_value.strip())
                    if st_int > 0:
                        final_results["mlst_status"] = "PASSED"
                        final_results["mlst_message"] = f"Valid ST found: {st_value}"
                    elif st_int == 0:
                        final_results["mlst_status"] = "PASSED"
                        final_results["mlst_message"] = "Novel ST found."
                    else:
                        final_results["mlst_status"] = "WARNING"
                        final_results["mlst_message"] = (
                            f"No valid ST found (ST={st_value})."
                        )
                except ValueError:
                    # ST is not a number (e.g., "-" or "N/A")
                    final_results["mlst_status"] = "WARNING"
                    final_results["mlst_message"] = (
                        f"No valid ST found (ST={st_value})."
                    )
            else:
                # ST field is empty
                final_results["mlst_status"] = "WARNING"
                final_results["mlst_message"] = "No valid ST found (empty ST field)."
        else:
            # No ST field in results
            final_results["mlst_st"] = None
            final_results["mlst_status"] = "WARNING"
            final_results["mlst_message"] = "No valid ST found (ST field missing)."
    else:
        final_results["mlst_message"] = (
            "No MLST database found for species. Install via config.yml."
        )
        final_results["mlst_status"] = "WARNING"
        if message:
            print_message(
                f"No MLST database found for species: {species}. Skipping MLST.",
                "warning",
            )
    return final_results


def handle_genome_size(species_list, fastp_stats, final_results, config):
    """Evaluate genome coverage and GC content for the top predicted species.

    Parameters
    ----------
    species_list : list
        Detected species names (top species at index 0). Only the top species is used
        for genome-size and GC evaluations; a short warning text is appended when multiple
        species are present.
    fastp_stats : dict
        Sequencing metrics. Expected keys: ``read_total_bases`` (int) and ``gc_content`` (float).
    final_results : dict
        Results dictionary updated in-place. Keys written include ``coverage_alt_estimate``,
        ``genome_size_expected``, ``coverage_alt_status``, ``coverage_alt_message``,
        ``gc_content_lower``, ``gc_content_upper``, and possibly ``gc_content_status``/``gc_content_message``.
    config : dict
        Configuration options used by this function. Recognised keys:
            - ``coverage_threshold`` (int, default 30)
            - ``metrics_file`` (path used by :func:`get_expected_genome_size`)
            - ``gc_fail_percentage`` (float or int): tolerance for GC warnings; values >1 are
              treated as percentages and divided by 100.

    Notes
    -----
    - Calls :func:`get_expected_genome_size` to obtain expected genome size and GC bounds.
    - Coverage is computed as ``read_total_bases / expected_genome_size`` when values are available
      and stored (rounded) in ``coverage_alt_estimate``; ``coverage_alt_status`` is set to
      "PASSED" when the estimate meets ``coverage_threshold`` otherwise "FAILED".
    - GC bounds are stored in ``gc_content_lower`` and ``gc_content_upper``. When both bounds
      are > 0 the function will set ``gc_content_status`` to "PASSED" or "WARNING" when the
      GC content is within the exact bounds or within the expanded tolerance, respectively.
      If the GC content is outside the tolerance range the function sets ``gc_content_message``
      but does not change an existing ``gc_content_status`` (it is left as-initialised).

    Returns
    -------
    dict
        The updated ``final_results`` dictionary.
    """
    # Get expected genome size,
    # Use two-tier coverage thresholds when available (warn/fail). Fall back to legacy
    # `coverage_threshold` for backward compatibility.
    coverage_fail_threshold = config.get("coverage_fail_threshold")
    coverage_warn_threshold = config.get("coverage_warn_threshold")

    if coverage_fail_threshold is None:
        # Legacy single-threshold mode
        coverage_fail_threshold = config.get("coverage_threshold", 30)
        coverage_warn_threshold = coverage_fail_threshold * 0.67
    species = species_list[0]  # Use the top species only
    warning = ""
    if len(species_list) > 1:
        warning = "Warning: Multiple species detected. Using the top species."
    expected_genome_size, gc_lower, gc_upper = get_expected_genome_size(species, config)
    # Get estimated coverage and eval fastp results
    if expected_genome_size > 0 and fastp_stats.get("read_total_bases", 0) > 0:
        estimated_coverage = fastp_stats["read_total_bases"] / expected_genome_size
    else:
        estimated_coverage = 0
    final_results["coverage_alt_estimate"] = round(estimated_coverage, 2)
    final_results["genome_size_expected"] = expected_genome_size
    # Evaluate alternate coverage using WARN/FAIL thresholds
    if estimated_coverage >= coverage_fail_threshold:
        final_results["coverage_alt_status"] = "PASSED"
        final_results["coverage_alt_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x meets the threshold of {coverage_fail_threshold}x."
            + warning
        )
    elif estimated_coverage >= coverage_warn_threshold:
        final_results["coverage_alt_status"] = "WARNING"
        final_results["coverage_alt_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x falls between warning ({coverage_warn_threshold}x) and pass ({coverage_fail_threshold}x) thresholds."
            + warning
        )
    else:
        final_results["coverage_alt_status"] = "FAILED"
        final_results["coverage_alt_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x below the warning threshold ({coverage_warn_threshold}x)."
            + warning
        )
    final_results["gc_content_lower"] = gc_lower
    final_results["gc_content_upper"] = gc_upper
    gc_fail_percentage = config.get("gc_fail_percentage", 5)
    if gc_fail_percentage > 1:
        gc_fail_percentage /= 100
    if gc_lower > 0 and gc_upper > 0:
        if gc_lower <= fastp_stats.get("gc_content", 0) <= gc_upper:
            final_results["gc_content_status"] = "PASSED"
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% within expected range ({gc_lower}-{gc_upper}%)"
            )
        elif (
            gc_lower - (gc_lower * gc_fail_percentage)
            <= fastp_stats.get("gc_content", 0)
            <= gc_upper + (gc_upper * gc_fail_percentage)
        ):
            final_results["gc_content_status"] = "WARNING"
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% near expected range ({gc_lower}-{gc_upper}%)"
            )
        else:
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% outside expected range ({gc_lower}-{gc_upper}%)"
            )
    return final_results


def get_fastp_results(fastp_results):
    """
    Extracts quality metrics from a fastp JSON report after filtering.

    Parameters:
        fastp_results (dict): Dictionary containing fastp run information.
            Expected keys:
                - "status": Should be "success" if fastp ran successfully.
                - "json_report": Path to the fastp JSON report file.

    Returns:
        dict: Dictionary of metrics from the 'after_filtering' section of the fastp report, including:
            - total_reads (int): Number of reads after filtering.
            - total_bases (int): Number of bases after filtering.
            - q20_bases (int): Number of bases with quality >= Q20.
            - q30_bases (int): Number of bases with quality >= Q30.
            - q20_rate (float): Percentage of bases with quality >= Q20.
            - q30_rate (float): Percentage of bases with quality >= Q30.
            - read1_mean_length (int): Mean length of read 1 after filtering.
            - read2_mean_length (int): Mean length of read 2 after filtering.
            - gc_content (float): GC content percentage after filtering (rounded to 4 decimals).

    If the fastp run was unsuccessful or the report file is missing, returns a dictionary with zeroed/default values for all metrics.
    """
    failed = {
        "read_total_reads": 0,
        "read_total_bases": 0,
        "read_q20_bases": 0,
        "read_q30_bases": 0,
        "read_q20_rate": 0.0,
        "read_q30_rate": 0.0,
        "read1_mean_length": 0,
        "read2_mean_length": 0,
        "gc_content": 0.0,
    }
    if fastp_results.get("status") != "success":
        return failed
    fastp_json = fastp_results.get("json_report")
    if not fastp_json or not os.path.exists(fastp_json):
        return failed

    with open(fastp_json, encoding="utf-8") as f:
        data = json.load(f)

    after_filtering = data.get("summary").get("after_filtering", failed)
    # Rename keys to match expected output
    after_filtering_rename = {
        "read_total_reads": after_filtering.get("total_reads", 0),
        "read_total_bases": after_filtering.get("total_bases", 0),
        "read_q20_bases": after_filtering.get("q20_bases", 0),
        "read_q30_bases": after_filtering.get("q30_bases", 0),
        "read_q20_rate": after_filtering.get("q20_rate", 0.0),
        "read_q30_rate": after_filtering.get("q30_rate", 0.0),
        "read1_mean_length": after_filtering.get("read1_mean_length", 0),
        "read2_mean_length": after_filtering.get("read2_mean_length", 0),
    }
    after_filtering_rename["gc_content"] = round(
        float(after_filtering["gc_content"] * 100), 4
    )

    duplication_rate = 0.0
    if "duplication" in data:
        duplication_rate = data["duplication"].get("rate", 0.0)
    after_filtering_rename["duplication_rate"] = duplication_rate

    n_content_rate = 0.0
    filtering_result = data.get("filtering_result", {})
    if filtering_result.get("total_reads", 0) > 0:
        too_many_n = filtering_result.get("too_many_N", 0)
        total_reads = filtering_result.get("total_reads", 0)
        n_content_rate = (too_many_n / total_reads) * 100.0
    after_filtering_rename["n_content_rate"] = n_content_rate

    return after_filtering_rename


def get_expected_genome_size(species, config):
    """
    Retrieves the expected genome size and GC content range for a given species from a metrics CSV file.

    Args:
        species (str): The scientific name of the species (e.g., "Streptococcus agalactiae").
        config (dict): Configuration dictionary containing the path to the metrics file under the key "metrics_file".

    Returns:
        tuple:
            genome_size (float): The expected genome size (average of lower and upper bounds) for the species.
            gc_lower (int): The lower bound of GC content percentage for the species.
            gc_upper (int): The upper bound of GC content percentage for the species.

    Notes:
        - The metrics file is expected to contain lines in the format:
            <species_name>,Genome_Size,<lower>,<upper>
            <species_name>,GC_Content,<lower>,<upper>
        - Species names in the file should use underscores instead of spaces or periods.
        - If no matching entry is found, returns zeros for all values.
    """
    metrics_file = config.get("metrics_file")
    safe_species_name = species.replace(" ", "_").replace(".", "_")
    genome_size = 0
    gc_lower = 0
    gc_upper = 0
    with open(metrics_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            # Line should be line Streptococcus_agalactiae,Genome_Size,<lower>,<upper>
            if line.startswith(safe_species_name) and "Genome_Size" in line:
                genome_size = (int(parts[2]) + int(parts[3])) / 2
            # Also return GC Content, from Streptococcus_agalactiae,GC_Content,35,37
            if line.startswith(safe_species_name) and "GC_Content" in line:
                gc_lower = int(parts[2])
                gc_upper = int(parts[3])
    return genome_size, gc_lower, gc_upper


def final_status_pass(final_results):
    """
    Look at statuses from all other status columns and determine final status.

    Determines final QC pass/fail/warning status based on all individual metric statuses.

    Critical failures (read quality, contamination, GC content, critical fastp metrics)
    result in FAILED status. Any individual FAILED status in critical metrics causes FAILED.
    WARNINGs accumulate to overall WARNING status if no critical failures.

    Note: MLST status is informational only and does not affect final QC pass/fail determination.
    Species WARNING status can contribute to overall WARNING but not FAILED.

    Metrics are only evaluated if data is available (i.e., read_total_reads > 0).
    """
    # get all keys that end with _status
    final_status = "PASSED"
    statuses = {k: v for k, v in final_results.items() if k.endswith("_status")}

    # Critical metrics - failure in any of these means FAILED final status
    total_reads = final_results.get("read_total_reads", 0)

    # Always-critical metrics (even if no reads)
    critical_metrics = [
        "read_length_status",
        "read_q30_status",
        "contamination_status",
        "gc_content_status",
    ]

    # New TIER metrics - only critical if reads were actually processed
    if total_reads > 0:
        critical_metrics.extend(
            [
                "duplication_status",  # TIER 1: High duplication is critical
                "n_content_status",  # TIER 1: High N-content is concerning
            ]
        )

    for metric in critical_metrics:
        if statuses.get(metric) == "FAILED":
            final_status = "FAILED"
            break

    # If final status not already FAILED, check coverage
    if final_status != "FAILED":
        # If both coverage metrics failed, final status is failed
        if (
            statuses.get("coverage_status") == "FAILED"
            and statuses.get("coverage_alt_status") == "FAILED"
        ):
            final_status = "FAILED"
        # If one coverage metric failed, it's a warning
        elif (
            statuses.get("coverage_status") == "FAILED"
            or statuses.get("coverage_alt_status") == "FAILED"
        ):
            final_status = "WARNING"

    # Check for warnings in non-critical metrics if not already FAILED
    if final_status != "FAILED":
        # Always-evaluable warning metrics
        warning_metrics = [
            "species_status",  # Species identification issues
        ]

        for metric in warning_metrics:
            if statuses.get(metric) == "FAILED":
                if final_status != "FAILED":
                    final_status = "WARNING"
            elif statuses.get(metric) == "WARNING":
                if final_status == "PASSED":
                    final_status = "WARNING"

    return final_status
