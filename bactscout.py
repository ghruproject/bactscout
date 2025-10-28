#!/usr/bin/env python3
from pathlib import Path

import typer

from bactscout.collect import collect_sample
from bactscout.main import main
from bactscout.summary import summary_dir
from bactscout.util import print_header, print_message

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
    report_resources: bool = typer.Option(
        False, "--report-resources", help="Track and report thread and memory usage per sample"
    ),
):
    """Main QC command"""
    main(
        input_dir,
        output_dir,
        threads,
        config_file=config,
        skip_preflight=skip_preflight,
        report_resources=report_resources,
    )


@app.command()
def collect(
    read1_file: str = typer.Argument(..., help="Path to the R1 FASTQ file"),
    read2_file: str = typer.Argument(..., help="Path to the R2 FASTQ file"),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
    ),
    threads: int = typer.Option(
        4, "--threads", "-t", help="Number of threads to pass to tools"
    ),
    config: str = typer.Option(
        "bactscout_config.yml", "--config", "-c", help="Path to the configuration file"
    ),
    skip_preflight: bool = typer.Option(
        False, "--skip-preflight", help="Skip the preflight checks"
    ),
    report_resources: bool = typer.Option(
        False, "--report-resources", help="Track and report thread and memory usage for the sample"
    ),
):
    """Process a single sample with paired-end reads"""
    collect_sample(read1_file, read2_file, output_dir, threads, config, skip_preflight, report_resources)


@app.command()
def summary(
    input_dir: str = typer.Argument(
        ..., help="Path to the directory containing sample subdirectories"
    ),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
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
