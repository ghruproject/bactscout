import os
import shutil
import subprocess

from bactscout.util import extract_sample_name, print_message


def run_command(r1, r2, output_dir, message=False, threads=1):
    """
    Run FastP on paired-end FASTQ files for quality control and generate reports.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        output_dir (str): Path to the output directory where results will be saved.
        message (bool): Whether to print progress messages.
        threads (int): Number of threads to use for processing.
    """

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract sample name from R1 file
    sample_name = extract_sample_name(r1)

    # Define output files
    json_report = os.path.join(output_dir, f"{sample_name}.fastp.json")
    html_report = os.path.join(output_dir, f"{sample_name}.fastp.html")
    log_file = os.path.join(output_dir, f"{sample_name}.fastp.log")

    # Get FastP command
    cmd = get_command()

    # Build FastP command arguments
    fastp_args = [
        "--in1",
        r1,
        "--in2",
        r2,
        "--json",
        json_report,
        "--html",
        html_report,  # Write HTML output to the output directory
        "--thread",
        str(threads),
        "--detect_adapter_for_pe",  # Auto-detect adapters for paired-end reads
    ]

    fastp_args.extend(
        [
            "--disable_adapter_trimming",
            "--disable_quality_filtering",
            "--disable_length_filtering",
        ]
    )

    # Combine command and arguments
    full_cmd = cmd + fastp_args if isinstance(cmd, list) else [cmd] + fastp_args

    try:
        if message:
            print_message(f"Running FastP for sample: {sample_name}")
            print_message(f"Command: {' '.join(full_cmd)}")

        # Run FastP and capture output
        with open(log_file, "w", encoding="utf-8") as log:
            subprocess.run(
                full_cmd, stdout=log, stderr=subprocess.STDOUT, check=True, text=True
            )
        if message:
            print_message(f"FastP completed successfully for {sample_name}")
        if message:
            print_message(f"  - JSON report: {json_report}")
            print_message(f"  - HTML report: {html_report}")
            print_message(f"  - Log file: {log_file}")

        return {
            "sample": sample_name,
            "status": "success",
            "json_report": json_report,
            "html_report": html_report,
            "log_file": log_file,
        }

    except subprocess.CalledProcessError as e:
        error_msg = f"Error running FastP for {sample_name}: {e}"
        print_message(error_msg, "error")

        # Write error to log file
        with open(log_file, "a", encoding="utf-8") as log:
            log.write(f"\nERROR: {error_msg}\n")

        return {
            "sample": sample_name,
            "status": "failed",
            "error": str(e),
            "log_file": log_file,
        }


def get_command():
    """
    Get the FastP command, trying different methods to locate it.

    Returns:
        list: FastP command as a list for subprocess
    """
    # Try to find fastp in PATH
    cmd = shutil.which("fastp")

    if cmd is not None:
        return [cmd]

    # If not found, try with pixi
    if shutil.which("pixi"):
        return ["pixi", "run", "--", "fastp"]

    # Last resort - assume it's in PATH but not detected
    return ["fastp"]
