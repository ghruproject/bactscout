import shutil
import subprocess
import os
from pathlib import Path

def run_command(r1, r2, output_dir, config, message=False):
    """
    Run FastP on paired-end FASTQ files for quality control and generate reports.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        output_dir (str): Path to the output directory where results will be saved.
        config (dict): Configuration dictionary containing FastP settings.
    """
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract sample name from R1 file
    r1_path = Path(r1)
    sample_name = r1_path.stem.replace('_R1', '').replace('.fastq', '').replace('.fq', '')
    
    # Define output files
    json_report = os.path.join(output_dir, f"{sample_name}.fastp.json")
    log_file = os.path.join(output_dir, f"{sample_name}.fastp.log")
    
    # Get FastP command
    cmd = get_command()
    
    # Build FastP command arguments
    fastp_args = [
        "--in1", r1,
        "--in2", r2,
        "--json", json_report,
        "--thread", str(config.get("threads", 4)),
        "--detect_adapter_for_pe",  # Auto-detect adapters for paired-end reads
    ]
    
    # Add optional parameters from config
    if config.get("disable_trimming", True):
        # For QC-only mode (no trimming output)
        fastp_args.extend([
            "--disable_adapter_trimming",
            "--disable_quality_filtering", 
            "--disable_length_filtering"
        ])
    else:
        # If trimming is enabled, add trimmed output files
        trimmed_r1 = os.path.join(output_dir, f"{sample_name}_R1.trimmed.fastq.gz")
        trimmed_r2 = os.path.join(output_dir, f"{sample_name}_R2.trimmed.fastq.gz")
        fastp_args.extend([
            "--out1", trimmed_r1,
            "--out2", trimmed_r2
        ])
    
    # Add quality thresholds if specified
    if "quality_threshold" in config:
        fastp_args.extend(["--qualified_quality_phred", str(config["quality_threshold"])])
    
    if "min_length" in config:
        fastp_args.extend(["--length_required", str(config["min_length"])])
    
    # Combine command and arguments
    full_cmd = cmd + fastp_args if isinstance(cmd, list) else [cmd] + fastp_args
    
    try:
        if message:
            print(f"Running FastP for sample: {sample_name}")
            print(f"Command: {' '.join(full_cmd)}")

        # Run FastP and capture output
        with open(log_file, "w") as log:
            result = subprocess.run(
                full_cmd, 
                stdout=log, 
                stderr=subprocess.STDOUT,
                check=True,
                text=True
            )
        if message:
            print(f"FastP completed successfully for {sample_name}")
        if message:
            print(f"  - JSON report: {json_report}")
            print(f"  - Log file: {log_file}")
        
        return {
            "sample": sample_name,
            "status": "success",
            "json_report": json_report,
            "log_file": log_file
        }
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Error running FastP for {sample_name}: {e}"
        print(error_msg)
        
        # Write error to log file
        with open(log_file, "a") as log:
            log.write(f"\nERROR: {error_msg}\n")
        
        return {
            "sample": sample_name,
            "status": "failed",
            "error": str(e),
            "log_file": log_file
        }


def get_command():
    """
    Get the FastP command, trying different methods to locate it.
    
    Returns:
        str or list: FastP command or command list with pixi/conda prefix
    """
    # Try to find fastp in PATH
    cmd = shutil.which("fastp")
    
    if cmd is not None:
        return cmd
    
    # If not found, try with pixi
    if shutil.which("pixi"):
        return ["pixi", "run", "--", "fastp"]
    
    # Last resort - assume it's in PATH but not detected
    return "fastp"
