"""
Main batch processing module for BactScout QC pipeline.

This module provides the primary entry point for batch processing multiple samples.
It handles sample discovery, orchestrates preflight validation, manages parallel
processing, and aggregates results across all samples.

Key Components:
    - main(): Batch processing orchestrator
    - locate_read_file_pairs(): Sample pair discovery
    - Progress tracking with rich formatting

Workflow:
    1. Load configuration
    2. Run preflight checks (unless skipped)
    3. Discover FASTQ file pairs in input directory
    4. Process each sample in parallel
    5. Merge individual sample results into consolidated summary
    6. Report processing statistics

Dependencies:
    - bactscout.preflight: Configuration and validation
    - bactscout.thread: Individual sample processing
    - bactscout.summary: Result aggregation
    - bactscout.util: Output formatting

Example:
    >>> from bactscout.main import main
    >>> main(
    ...     input_dir="./samples",
    ...     output_dir="./results",
    ...     max_threads=4
    ... )
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from bactscout.preflight import (
    load_config,
    preflight_check,
)
from bactscout.summary import summary_dir
from bactscout.thread import run_one_sample
from bactscout.util import print_header, print_message


def main(
    input_dir,
    output_dir,
    max_threads,
    skip_preflight: bool = False,
    config_file: str = "bactscout_config.yml",
    report_resources: bool = False,
):
    """
    Run the BactScout QC pipeline on multiple samples in batch mode.

    This is the main entry point for batch processing multiple FASTQ file pairs.
    It discovers all sample pairs in the input directory, performs preflight checks,
    and processes each sample in parallel using the specified number of threads.

    Args:
        input_dir (str): Path to directory containing paired-end FASTQ files.
            Files should follow naming pattern: <sample_id>_R1.fastq.gz and <sample_id>_R2.fastq.gz
        output_dir (str): Path to output directory where results will be saved.
            Each sample gets a subdirectory with its results.
        max_threads (int): Maximum number of parallel threads for processing samples.
            Each sample analysis will use 1 thread for internal operations.
        skip_preflight (bool, optional): Skip preflight validation checks. Defaults to False.
            When True, skips system resource, software availability, and database checks.
        config_file (str, optional): Path to BactScout configuration file.
            Defaults to "bactscout_config.yml".
        report_resources (bool, optional): Track and report thread and memory usage per sample.
            Defaults to False.

    Returns:
        None: Results are written to output_dir and printed to console.

    Raises:
        ValueError: If config file is invalid or database paths are incorrect.
        RuntimeError: If critical tools (fastp, sylph, stringMLST) are not available.
        OSError: If input/output directories cannot be accessed.

    Notes:
        - Preflight checks validate system resources, installed tools, and database availability
        - Sample processing runs in parallel threads for efficiency
        - Each sample generates: fastp QC report, Sylph species ID, MLST typing (if applicable)
        - Final summary merged across all samples and saved as final_summary.csv
        - Progress shown with rich formatting and spinner
        - Resource usage tracking includes peak thread count and memory consumption per sample
    """
    config = load_config(config_file)
    all_ok = preflight_check(skip_preflight, config)

    # Get all sample pairs
    sample_pairs = locate_read_file_pairs(input_dir)
    total_samples = len(sample_pairs)

    if total_samples == 0:
        print_message("No FASTQ file pairs found in input directory", "error")
        return

    if all_ok:
        print_header("Running Pipeline")
        print_message(f"Found {total_samples} sample pairs to process", "info")
        print_message(f"Using up to {max_threads} parallel threads", "info")

        # Process samples in parallel using ThreadPoolExecutor
        successful_samples = []
        failed_samples = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task(
                f"Processing {total_samples} samples...", total=total_samples
            )

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                # Submit all samples for processing
                future_to_sample = {
                    executor.submit(
                        run_one_sample,
                        sample,
                        reads["R1"],
                        reads["R2"],
                        output_dir,
                        config,
                        threads=1,
                        message=False,
                        report_resources=report_resources,
                        batch_worker_count=max_threads,
                    ): sample
                    for sample, reads in sample_pairs.items()
                }

                # Process completed tasks as they finish
                for future in as_completed(future_to_sample):
                    sample = future_to_sample[future]
                    try:
                        result = future.result()
                        if result and result.get("status") == "success":
                            successful_samples.append(sample)
                        else:
                            failed_samples.append(sample)
                            print_message(f"❌ Sample {sample} failed", "error")
                    except (RuntimeError, OSError, ValueError) as exc:
                        failed_samples.append(sample)
                        print_message(
                            f"❌ Sample {sample} generated an exception: {exc}", "error"
                        )
                    # Update progress
                    progress.update(task, advance=1)

        # Print final summary
        print_header("Pipeline Summary")
        print_message(f"Total samples processed: {total_samples}", "info")
        print_message(f"Successful: {len(successful_samples)}", "success")
        print_message(
            f"Failed: {len(failed_samples)}", "error" if failed_samples else "info"
        )

        if failed_samples:
            print_message(f"Failed samples: {', '.join(failed_samples)}", "warning")
        summary_dir(output_dir, os.path.join(output_dir, "final_summary.csv"))


def locate_read_file_pairs(directory):
    """
    Locate and return pairs of read files in the specified directory.

    Args:
        directory (str): Path to the directory containing FASTQ files.
    """

    read_pairs = {}
    # Regex to match sample names ending with _1 or _2 before extension
    pattern = re.compile(r"(.+?)(?:_R)?([12])(\.fastq(?:\.gz)?|\.fq(?:\.gz)?)$")

    for filename in os.listdir(directory):
        if filename.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
            match = pattern.match(filename)
            if match:
                base_name = match.group(1)
                if base_name.endswith("_"):
                    base_name = base_name[:-1]  # Remove trailing underscore
                read_type = "R1" if match.group(2) == "1" else "R2"
                if base_name not in read_pairs:
                    read_pairs[base_name] = {}
                read_pairs[base_name][read_type] = os.path.join(directory, filename)
    # Filter out incomplete pairs
    complete_pairs = {k: v for k, v in read_pairs.items() if "R1" in v and "R2" in v}
    return complete_pairs
