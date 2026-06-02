"""Single-sample long-read collection and processing module."""

import csv
import os

from bactscout.long.evaluate import evaluate_long
from bactscout.long.nanoq import run_nanoq
from bactscout.long.preflight import preflight_check_long
from bactscout.preflight import load_config
from bactscout.resource_monitor import ResourceMonitor
from bactscout.software.run_sylph import extract_species_from_report
from bactscout.software.run_sylph import run_command_single as run_sylph_single
from bactscout.thread import get_expected_genome_size
from bactscout.util import print_header, print_message


def extract_long_sample_name(filename: str) -> str:
    """Extract a long-read sample name by stripping only FASTQ extensions."""
    basename = os.path.basename(filename)
    for ext in (".fastq.gz", ".fq.gz", ".fastq", ".fq"):
        if basename.endswith(ext):
            return basename[: -len(ext)]
    return basename


def blank_long_results(sample_id: str, platform: str) -> dict:
    """Return a blank results record for a long-read sample."""
    return {
        "sample_id": sample_id,
        "platform": platform,
        "status": "FAILED",
        "read_count": 0,
        "total_bases": 0,
        "n50": 0,
        "mean_len": 0,
        "median_len": 0,
        "mean_q": "",
        "median_q": "",
        "top_taxon": "",
        "expected_genome_size": "",
        "coverage_estimate_sylph": "",
        "coverage_estimate_calc": "",
        "contamination_pct": "",
        "flag_quality": "FAILED",
        "flag_n50": "FAILED",
        "flag_coverage": "FAILED",
        "flag_contam": "FAILED",
        "flag_coverage_calc": "FAILED",
        "flag_coverage_sylph": "FAILED",
        "reasons": "No reads processed.",
    }


def write_long_summary_file(final_results, sample_id, sample_output_dir):
    """Write a per-sample long-read summary CSV."""
    output_file = os.path.join(sample_output_dir, f"{sample_id}_long_summary.csv")
    preferred_headers = list(blank_long_results(sample_id, final_results["platform"]).keys()) + [
        "resource_threads_peak",
        "resource_memory_peak_mb",
        "resource_memory_avg_mb",
        "resource_duration_sec",
    ]
    headers = [header for header in preferred_headers if header in final_results]
    extras = [header for header in final_results.keys() if header not in headers]
    headers.extend(sorted(extras))

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(final_results)


def run_one_long_sample(
    sample_id,
    reads_file,
    output_dir,
    config,
    platform,
    threads=1,
    message=False,
    report_resources=False,
    batch_worker_count=None,
):
    """Execute long-read QC analysis for a single sample."""
    resource_monitor = None
    if report_resources:
        resource_monitor = ResourceMonitor(worker_threads_override=batch_worker_count)
        resource_monitor.start()

    if message:
        print_message(f"Running long-read analysis for {sample_id}", "info")

    sample_output_dir = os.path.join(output_dir, sample_id)
    if not os.path.exists(sample_output_dir):
        os.makedirs(sample_output_dir, exist_ok=True)

    if not os.path.exists(reads_file):
        return {"status": "failed", "message": f"Reads file {reads_file} not found."}

    final_results = blank_long_results(sample_id, platform)
    read_stats = run_nanoq(reads_file, sample_output_dir, threads=threads)
    final_results.update(read_stats)

    sylph_result = run_sylph_single(
        reads_file,
        sample_output_dir,
        config,
        message=message,
        threads=threads,
    )
    species_abundance, _genome_file_path = extract_species_from_report(
        sylph_result.get("sylph_report")
    )

    top_species = species_abundance[0] if species_abundance else None
    top_taxon = top_species[0] if top_species else ""
    coverage_sylph = round(top_species[2], 2) if top_species else None
    contamination = round(max(0.0, 100 - top_species[1]), 2) if top_species else None
    expected_genome_size = None
    coverage_calc = None
    if top_taxon:
        expected_genome_size, _gc_lower, _gc_upper = get_expected_genome_size(top_taxon, config)
        if expected_genome_size > 0:
            coverage_calc = round(read_stats["total_bases"] / expected_genome_size, 2)
        else:
            expected_genome_size = None

    verdict = evaluate_long(
        read_stats,
        coverage_calc,
        coverage_sylph,
        contamination,
        config,
        platform,
    )

    final_results.update(
        {
            "top_taxon": top_taxon,
            "expected_genome_size": expected_genome_size or "",
            "coverage_estimate_sylph": coverage_sylph if coverage_sylph is not None else "",
            "coverage_estimate_calc": coverage_calc if coverage_calc is not None else "",
            "contamination_pct": contamination if contamination is not None else "",
            **verdict,
        }
    )

    if resource_monitor:
        resource_monitor.end()
        stats = resource_monitor.get_stats()
        final_results["resource_threads_peak"] = stats.get("peak_threads", 0)
        final_results["resource_memory_peak_mb"] = int(round(stats.get("peak_memory_mb", 0.0)))
        final_results["resource_memory_avg_mb"] = int(round(stats.get("avg_memory_mb", 0.0)))
        final_results["resource_duration_sec"] = round(stats.get("duration_sec", 0.0), 2)

    write_long_summary_file(final_results, sample_id, sample_output_dir)
    return {"status": "success", "sample_id": sample_id, "results": final_results}


def collect_sample_long(
    reads_file: str,
    output_dir: str,
    threads: int,
    config: str,
    platform: str,
    skip_preflight: bool,
    report_resources: bool = False,
) -> None:
    """Process a single long-read sample."""
    config_dict = load_config(config)
    all_ok = preflight_check_long(skip_preflight, config_dict)
    if not all_ok:
        print_message("Preflight checks failed. Exiting.", "error")
        return

    sample_id = extract_long_sample_name(reads_file)
    if not sample_id:
        print_message(f"Could not extract sample name from {reads_file}", "error")
        return

    print_header("Processing Single Long-Read Sample")
    print_message(f"Sample ID: {sample_id}", "info")
    print_message(f"Reads: {reads_file}", "info")
    print_message(f"Platform: {platform}", "info")
    print_message(f"Using {threads} threads", "info")

    result = run_one_long_sample(
        sample_id,
        reads_file,
        output_dir,
        config_dict,
        platform,
        threads=threads,
        message=True,
        report_resources=report_resources,
    )
    if result and result.get("status") == "success":
        print_header("Long-Read Sample Processing Complete")
        print_message(f"Sample {sample_id} processed successfully", "success")
        print_message(f"Results saved to {output_dir}/{sample_id}/", "info")
    else:
        print_message(f"Sample {sample_id} processing failed", "error")
