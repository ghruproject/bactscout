#!/usr/bin/env python3
from pathlib import Path

import typer

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
    input_dir: str = typer.Argument(
        ..., help="Path to the input directory containing FASTQ files"
    ),
    output_dir: str = typer.Option(
        "bactscout_output", "--output", "-o", help="Path to the output directory"
    ),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    config: str = typer.Option(
        "bactscout_config.yml", "--config", "-c", help="Path to the configuration file"
    ),
    skip_preflight: bool = typer.Option(
        False, "--skip-preflight", help="Skip the preflight checks"
    ),
):
    """Run on a single sample"""
    main(input_dir, output_dir, threads, config_file=config)


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
