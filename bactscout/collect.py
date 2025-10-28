"""Single sample collection and processing module."""

from typing import Optional

from bactscout.preflight import (
    check_databases,
    check_software,
    check_system_resources,
    load_config,
)
from bactscout.thread import run_one_sample
from bactscout.util import extract_sample_name, print_header, print_message


def collect_sample(
    read1_file: str,
    read2_file: str,
    output_dir: str,
    threads: int,
    config: str,
    skip_preflight: bool,
    report_resources: bool = False,
    kat_enabled: Optional[bool] = None,
    k_mer_size: Optional[int] = None,
) -> None:
    """
    Process a single sample with paired-end reads.

    Args:
        read1_file: Path to the R1 FASTQ file
        read2_file: Path to the R2 FASTQ file
        output_dir: Path to the output directory
        threads: Number of threads to use
        config: Path to the configuration file
        skip_preflight: Skip preflight checks if True
        report_resources: Track and report thread and memory usage if True
        kat_enabled: Enable/disable KAT analysis (overrides config)
        k_mer_size: K-mer size for KAT analysis (overrides config)

    Returns:
        None
    """
    config_dict = load_config(config)

    # Override KAT settings from CLI if provided
    if kat_enabled is not None:
        kat_config = config_dict.get("kat", {})  # type: ignore
        kat_config["enabled"] = kat_enabled  # type: ignore
        config_dict["kat"] = kat_config  # type: ignore

    if k_mer_size is not None:
        kat_config = config_dict.get("kat", {})  # type: ignore
        kat_config["k"] = k_mer_size  # type: ignore
        config_dict["kat"] = kat_config  # type: ignore

    if skip_preflight:
        all_ok = True
        print_message("Skipping preflight checks", "warning")
    else:
        print_header("Preflight Checks")
        all_ok = (
            check_system_resources(config_dict)
            and check_software(config_dict)
            and check_databases(config_dict)
        )

    if not all_ok:
        print_message("Preflight checks failed", "error")
        return

    # Extract sample name from R1 filename
    sample_id = extract_sample_name(read1_file)

    if not sample_id:
        print_message(f"Could not extract sample name from {read1_file}", "error")
        return

    print_header("Processing Single Sample")
    print_message(f"Sample ID: {sample_id}", "info")
    print_message(f"R1: {read1_file}", "info")
    print_message(f"R2: {read2_file}", "info")
    print_message(f"Using {threads} threads", "info")

    # Process the sample
    try:
        result = run_one_sample(
            sample_id,
            read1_file,
            read2_file,
            output_dir,
            config_dict,
            threads=threads,
            message=True,
            report_resources=report_resources,
        )

        if result and result.get("status") == "success":
            print_header("Sample Processing Complete")
            print_message(f"✅ Sample {sample_id} processed successfully", "success")
            print_message(f"Results saved to {output_dir}/{sample_id}/", "info")
        else:
            print_message(f"❌ Sample {sample_id} processing failed", "error")

    except (RuntimeError, OSError, ValueError) as exc:
        print_message(f"❌ Error processing sample {sample_id}: {exc}", "error")
