"""Batch processing entry point for long-read QC."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from bactscout.long.collect import extract_long_sample_name, run_one_long_sample
from bactscout.long.preflight import preflight_check_long
from bactscout.long.summary import summary_dir_long
from bactscout.preflight import load_config
from bactscout.util import print_header, print_message


def locate_long_read_files(directory):
    """Locate single FASTQ files for long-read batch mode."""
    read_files = {}
    duplicates = {}
    for filename in sorted(os.listdir(directory)):
        if not filename.endswith((".fastq", ".fq", ".fastq.gz", ".fq.gz")):
            continue
        sample_id = extract_long_sample_name(filename)
        full_path = os.path.join(directory, filename)
        if sample_id in read_files:
            duplicates.setdefault(sample_id, [read_files[sample_id]])
            duplicates[sample_id].append(full_path)
        else:
            read_files[sample_id] = full_path
    return read_files, duplicates


def main_long(
    input_dir,
    output_dir,
    max_threads,
    platform,
    skip_preflight: bool = False,
    config_file: str = "bactscout_long_config.yml",
    report_resources: bool = False,
):
    """Run the long-read QC pipeline in batch mode."""
    config = load_config(config_file)
    all_ok = preflight_check_long(skip_preflight, config)
    if not all_ok:
        print_message("Preflight checks failed. Exiting.", "error")
        return

    read_files, duplicates = locate_long_read_files(input_dir)
    total_samples = len(read_files)
    if duplicates:
        for sample_id, files in duplicates.items():
            print_message(
                f"Multiple FASTQ files detected for sample '{sample_id}': {', '.join(files)}",
                "error",
            )
        print_message("Concatenate long-read FASTQs upstream and retry.", "error")
        return

    if total_samples == 0:
        print_message("No long-read FASTQ files found in input directory", "error")
        return

    print_header("Running Long-Read Pipeline")
    print_message(f"Found {total_samples} long-read samples to process", "info")
    print_message(f"Using up to {max_threads} parallel threads", "info")

    successful_samples = []
    failed_samples = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        task = progress.add_task(f"Processing {total_samples} long-read samples...", total=total_samples)
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            future_to_sample = {
                executor.submit(
                    run_one_long_sample,
                    sample_id,
                    reads_file,
                    output_dir,
                    config,
                    platform,
                    threads=1,
                    message=False,
                    report_resources=report_resources,
                    batch_worker_count=max_threads,
                ): sample_id
                for sample_id, reads_file in read_files.items()
            }
            for future in as_completed(future_to_sample):
                sample_id = future_to_sample[future]
                try:
                    result = future.result()
                    if result and result.get("status") == "success":
                        successful_samples.append(sample_id)
                    else:
                        failed_samples.append(sample_id)
                        print_message(f"Sample {sample_id} failed", "error")
                except (RuntimeError, OSError, ValueError) as exc:
                    failed_samples.append(sample_id)
                    print_message(f"Sample {sample_id} generated an exception: {exc}", "error")
                progress.update(task, advance=1)

    print_header("Long-Read Pipeline Summary")
    print_message(f"Total samples processed: {total_samples}", "info")
    print_message(f"Successful: {len(successful_samples)}", "success")
    print_message(f"Failed: {len(failed_samples)}", "error" if failed_samples else "info")
    if failed_samples:
        print_message(f"Failed samples: {', '.join(failed_samples)}", "warning")
    summary_dir_long(output_dir, os.path.join(output_dir, "final_summary_long.csv"))
