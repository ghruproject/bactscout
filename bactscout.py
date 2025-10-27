#!/usr/bin/env python3
from pathlib import Path

import typer

from bactscout.main import main
from bactscout.preflight import check_databases, check_software, check_system_resources, load_config
from bactscout.summary import summary_dir
from bactscout.thread import run_one_sample
from bactscout.util import extract_sample_name, print_header, print_message

app = typer.Typer(rich_markup_mode="rich")


@app.command()
def qc(
    input_dir: str = typer.Argument(
        ..., help="Path to the input directory containing FASTQ files"
    ),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
    ),
    skip_preflight: bool = typer.Option(
        False, "--skip-preflight", help="Skip the preflight checks"
    ),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    config: str = typer.Option(
        "bactscout_config.yml", "--config", "-c", help="Path to the configuration file"
    ),
):
    """Main QC command"""
    main(
        input_dir,
        output_dir,
        threads,
        config_file=config,
        skip_preflight=skip_preflight,
    )


@app.command()
def collect(
    read1_file: str = typer.Argument(
        ..., help="Path to the R1 FASTQ file"
    ),
    read2_file: str = typer.Argument(
        ..., help="Path to the R2 FASTQ file"
    ),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
    ),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to pass to tools"),
    config: str = typer.Option(
        "bactscout_config.yml", "--config", "-c", help="Path to the configuration file"
    ),
    skip_preflight: bool = typer.Option(
        False, "--skip-preflight", help="Skip the preflight checks"
    ),
):
    """Process a single sample with paired-end reads"""
    config_dict = load_config(config)
    
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
            message=True,
        )
        
        if result and result.get("status") == "success":
            print_header("Sample Processing Complete")
            print_message(f"✅ Sample {sample_id} processed successfully", "success")
            print_message(f"Results saved to {output_dir}/{sample_id}/", "info")
        else:
            print_message(f"❌ Sample {sample_id} processing failed", "error")
            
    except (RuntimeError, OSError, ValueError) as exc:
        print_message(f"❌ Error processing sample {sample_id}: {exc}", "error")


@app.command()
def summary(
    input_dir: str = typer.Argument(
        ..., help="Path to the directory containing sample subdirectories"
    ),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
    ),
    config: str = typer.Option(
        "bactscout_config.yml", "--config", "-c", help="Path to the configuration file"
    ),
):
    """Generate a consolidated summary of all samples"""
    print_header("BactScout Summary Generator")

    # Create output directory if needed
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate the merged summary file
    output_file = output_path / "final_summary.csv"
    summary_dir(input_dir, str(output_file))

    print_message(f"Summary report generated: {output_file}", "success")


if __name__ == "__main__":
    app()
