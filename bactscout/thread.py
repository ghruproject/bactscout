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
from bactscout.util import print_message


def blank_sample_results(sample_id):
    """
    Generate a blank results dictionary for a given sample.

    This function returns a dictionary containing default values for various sample metrics,
    including read counts, base counts, quality scores, GC content, species identification,
    coverage estimates, MLST typing, and reference genome information. All fields are
    initialized to indicate that no reads have been processed and no analysis has been performed.

    Args:
        sample_id (str or int): Unique identifier for the sample.

    Returns:
        dict: A dictionary with default values for all expected sample result fields.
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
        "mlst_status": "FAILED",
        "mlst_message": "Cannot determine MLST.",
        "contamination_status": "FAILED",
        "contamination_message": "No reads processed. Cannot determine contamination.",
        "coverage_alt_estimate": 0,
        "coverage_alt_message": "No reads processed. Cannot estimate alternative coverage.",
        "coverage_alt_status": "FAILED",
        "genome_file_path": "",
        "genome_file": "",
        "resource_threads_peak": 0,
        "resource_memory_peak_mb": 0.0,
        "resource_memory_avg_mb": 0.0,
        "resource_duration_sec": 0.0,
    }


def run_one_sample(
    sample_id, read1_file, read2_file, output_dir, config, threads=1, message=False, report_resources=False
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
            - Read quality scores (Q30, Q20 rates)
            - Species identification and abundance
            - Coverage estimates (both sylph-based and calculated)
            - MLST typing results (if applicable)
            - GC content evaluation
            - Contamination assessment
            - Overall QC pass/fail status with descriptive messages
            - Resource usage metrics if report_resources=True (threads, memory, duration)

    Notes:
        - Creates sample output directory if it doesn't exist
        - Calls external tools: Sylph (species), fastp (QC), stringMLST (typing)
        - MLST analysis only performed for single-species samples
        - Coverage evaluation uses both direct sylph output and computed estimates
        - Final status determined by pass/fail evaluation of all QC metrics
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

    if not os.path.exists(sample_output_dir):
        os.makedirs(sample_output_dir, exist_ok=True)

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
        if non_top_abundance > config.get("contamination_threshold", 10):
            final_results["species_status"] = "FAILED"
            final_results["species_message"] = (
                f"Multiple species detected with significant abundance ({non_top_abundance:.2f}%). Skipping MLST."
            )
            not_contaminated = False
    if not_contaminated:
        species = species[0]
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
            species=species,
            read1_file=read1_file,
            read2_file=read2_file,
            sample_output_dir=sample_output_dir,
            message=message,
            threads=threads,
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
    
    write_summary_file(final_results, sample_id, sample_output_dir)

    return {
        "status": "success",
        "sample_id": sample_id,
        "results": final_results,
    }


def write_summary_file(final_results, sample_id, sample_output_dir):
    """
    Writes a summary CSV file containing the results for a given sample.

    The function creates a CSV file named '{sample_id}_summary.csv' in the specified
    output directory. The file contains a single row with headers derived from the
    keys of `final_results` and a corresponding row of values.

    Args:
        final_results (dict): Dictionary containing result data, where keys are column headers
            and values are the corresponding data for the sample.
        sample_id (str): Identifier for the sample, used to name the output file.
        sample_output_dir (str): Directory path where the summary file will be saved.

    Returns:
        None
    """
    final_output_file = os.path.join(sample_output_dir, f"{sample_id}_summary.csv")
    with open(final_output_file, "w", encoding="utf-8") as f:
        # Write header
        headers = list(final_results.keys())
        # Warn if headers are not the same as blank_sample_results()
        if headers != list(blank_sample_results(sample_id).keys()):
            print_message(
                f"Warning: Headers in final results do not match expected headers for sample {sample_id}",
                "warning",
            )
        # Sort: sample_id first, then *_status, then alphabetical
        headers = sorted(
            final_results.keys(),
            key=lambda x: (x != "sample_id", not x.endswith("_status"), x),
            # or: (0 if x == "sample_id" else 1, 0 if x.endswith("_status") else 1, x)
        )
        f.write(",".join(headers) + "\n")
        # Write values
        values = [
            str(final_results[h]) if final_results[h] is not None else ""
            for h in headers
        ]
        f.write(",".join(values) + "\n")


def handle_fastp_results(fastp_results, config):
    """
    Updates fastp_results dictionary with status and messages for Q30 and read length metrics.

    Evaluates Q30 and read length against both WARNING and FAIL thresholds.
    Status is PASSED if above FAIL threshold, WARNING if between WARN and FAIL thresholds,
    and FAILED if below WARN threshold.

    Args:
        fastp_results (dict): Dictionary containing fastp metrics.
        config (dict): Configuration dictionary with thresholds:
            - q30_warn_threshold (float): Q30 rate below which WARNING is triggered (default: 0.60)
            - q30_fail_threshold (float): Q30 rate below which FAILED is triggered (default: 0.70)
            - read_length_warn_threshold (int): Read length below which WARNING is triggered (default: 80)
            - read_length_fail_threshold (int): Read length below which FAILED is triggered (default: 100)
            - q30_pass_threshold (float): Legacy threshold, used if warn/fail not present (default: 0.80)
            - read_length_pass_threshold (int): Legacy threshold, used if warn/fail not present (default: 100)

    Returns:
        dict: Updated fastp_results with status and message fields.
    """
    # Handle Q30 thresholds with backward compatibility
    q30_fail_threshold = config.get("q30_fail_threshold")
    q30_warn_threshold = config.get("q30_warn_threshold")

    if q30_fail_threshold is None:
        # Legacy mode: use pass_threshold as fail_threshold
        q30_fail_threshold = config.get("q30_pass_threshold", 0.80)
        q30_warn_threshold = q30_fail_threshold * 0.85  # Default warn at 85% of fail

    if q30_fail_threshold > 1:
        q30_fail_threshold /= 100
    if q30_warn_threshold > 1:
        q30_warn_threshold /= 100

    # Handle read length thresholds with backward compatibility
    read_length_fail_threshold = config.get("read_length_fail_threshold")
    read_length_warn_threshold = config.get("read_length_warn_threshold")

    if read_length_fail_threshold is None:
        # Legacy mode: use pass_threshold as fail_threshold
        read_length_fail_threshold = config.get("read_length_pass_threshold", 100)
        read_length_warn_threshold = (
            read_length_fail_threshold * 0.80
        )  # Default warn at 80% of fail

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


def handle_species_coverage(species_abundance, final_results, config):
    """
    Process Sylph species detection results and evaluate contamination and coverage.

    Integrates species abundance data from Sylph into the results, evaluates sample
    contamination based on the dominant species percentage, and assesses coverage against
    thresholds. Handles cases with no species detected, single species, or multiple species.

    Supports both WARNING and FAIL thresholds for coverage and contamination metrics.
    Status is PASSED if above FAIL threshold, WARNING if between WARN and FAIL thresholds,
    and FAILED if below WARN threshold.

    Args:
        species_abundance (list): List of tuples from Sylph containing:
            - species_abundance[i][0]: Species scientific name
            - species_abundance[i][1]: Percentage abundance of species (0-100)
            - species_abundance[i][2]: Estimated coverage from Sylph
        final_results (dict): Results dictionary to update with species and contamination data.
        config (dict): Configuration dictionary containing:
            - coverage_fail_threshold (int): Minimum coverage for PASS (default: 30)
            - coverage_warn_threshold (int): Minimum coverage for WARNING (default: 20)
            - contamination_fail_threshold (int): Minimum % of top species for PASS (default: 10)
            - contamination_warn_threshold (int): Minimum % of top species for WARNING (default: 5)
            - coverage_threshold (int): Legacy threshold for backward compatibility (default: 30)
            - contamination_threshold (int): Legacy threshold for backward compatibility (default: 10)

    Returns:
        tuple: (updated_final_results, species_list)
            - updated_final_results (dict): Results with species, coverage, and contamination status
            - species_list (list): Names of detected species sorted by abundance (empty if no species)

    Notes:
        - Evaluates contamination as (100 - top_species_percentage) exceeding threshold
        - Handles edge case where top_species is None (returns empty species list)
        - Multiple species warning includes note about using top species only
        - Coverage estimate set from Sylph's direct measurement (top_species[2])
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
        final_results["coverage_message"] = (
            f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x falls below warning threshold ({coverage_warn_threshold}x)."
        )
        final_results["coverage_status"] = "FAILED"

    # Evaluate contamination with WARNING and FAIL thresholds
    # Contamination is calculated as (100 - top_species_percentage)
    # Lower top species percentage = higher contamination
    if top_species and top_species[1] > (100 - contamination_fail_threshold):
        final_results["contamination_status"] = "PASSED"
        final_results["contamination_message"] = ""
    elif top_species and top_species[1] > (100 - contamination_warn_threshold):
        final_results["contamination_status"] = "WARNING"
        final_results["contamination_message"] = (
            f"Top species purity {top_species[1]:.2f}% falls between warning ({100 - contamination_warn_threshold}%) and fail ({100 - contamination_fail_threshold}%) thresholds."
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
    threads=1,
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
        - Invalid ST values (ST <= 0) marked as "WARNING"
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
            threads=threads,
        )
        # Check MLST results
        if mlst_result.get("stringmlst_results", {}).get("ST"):
            final_results["mlst_st"] = mlst_result["stringmlst_results"]["ST"]
            if int(final_results["mlst_st"]) > 0:
                final_results["mlst_status"] = "PASSED"
                final_results["mlst_message"] = (
                    f"Valid ST found: {mlst_result['stringmlst_results']['ST']}"
                )
            else:
                final_results["mlst_status"] = "WARNING"
                final_results["mlst_message"] = "No valid ST found."
        else:
            final_results["mlst_st"] = None
            final_results["mlst_status"] = "WARNING"
            final_results["mlst_message"] = "No valid ST found."
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
    """
    Evaluates genome coverage and GC content for a given sample based on species prediction and sequencing statistics.

    Parameters:
        species_list (list): List of detected species names, with the top species at index 0.
        fastp_stats (dict): Dictionary containing sequencing statistics, including 'total_bases' and 'gc_content'.
        final_results (dict): Dictionary to store the evaluation results and messages.
        config (dict): Configuration dictionary containing thresholds and expected genome size information.

    Returns:
        dict: Updated final_results dictionary with estimated coverage, expected genome size, coverage status/message,
              GC content range, and GC content status/message.

    Notes:
        - If multiple species are detected, only the top species is used for evaluation, and a warning is added.
        - Coverage is calculated as total_bases / expected_genome_size.
        - Coverage and GC content are evaluated against thresholds and expected ranges from config.
    """
    # Get expected genome size,
    coverage_cutoff = config.get("coverage_threshold", 30)
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
    if estimated_coverage >= coverage_cutoff:
        final_results["coverage_alt_status"] = "PASSED"
        final_results["coverage_alt_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x meets the threshold of {coverage_cutoff}x."
            + warning
        )
    else:
        final_results["coverage_alt_status"] = "FAILED"
        final_results["coverage_alt_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x below the threshold of {coverage_cutoff}x."
            + warning
        )
    final_results["gc_content_lower"] = gc_lower
    final_results["gc_content_upper"] = gc_upper
    if gc_lower > 0 and gc_upper > 0:
        if gc_lower <= fastp_stats.get("gc_content", 0) <= gc_upper:
            final_results["gc_content_status"] = "PASSED"
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% within expected range ({gc_lower}-{gc_upper}%)"
                + warning
            )
        else:
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% outside expected range ({gc_lower}-{gc_upper}%)"
                + warning
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
    """
    # get all keys that end with _status
    final_status = "PASSED"
    statuses = {k: v for k, v in final_results.items() if k.endswith("_status")}
    # If read length failed, final status is failed
    # A pass has to be no obvious contamination, good coverage, good read quality
    if (
        statuses.get("read_length_status") == "FAILED"
        or statuses.get("read_q30_status") == "FAILED"
        or statuses.get("contamination_status") == "FAILED"
        or statuses.get("gc_content_status") == "FAILED"
    ):
        final_status = "FAILED"
    # If both coverage and alt coverage failed, final status is failed, but if one passed, it's a warning
    if (
        statuses.get("coverage_status") == "FAILED"
        and statuses.get("coverage_alt_status") == "FAILED"
    ):
        final_status = "FAILED"
    elif (
        statuses.get("coverage_status") == "FAILED"
        or statuses.get("coverage_alt_status") == "FAILED"
    ):
        final_status = "WARNING"
    # If MLST failed, final status is warning
    if statuses.get("mlst_status") == "FAILED":
        if final_status != "FAILED":
            final_status = "WARNING"

    return final_status
