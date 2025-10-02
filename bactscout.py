#!/usr/bin/env python3
import typer
from rich.console import Console
from bactscout.main import main

app = typer.Typer(rich_markup_mode="rich")
console = Console()

@app.command()
def qc(
    input_dir: str = typer.Argument(..., help="Path to the input directory containing FASTQ files"),
    output_dir: str = typer.Option("bactscout_output", "--output", "-o", help="Path to the output directory"),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    config: str = typer.Option("bactscout_config.yml", "--config", "-c", help="Path to the configuration file"),
):
    """Main QC command"""
    main(input_dir, output_dir, threads, config_file=config)

@app.command()
def collect(
    input_dir: str = typer.Argument(..., help="Path to the input directory containing FASTQ files"),
    output_dir: str = typer.Option("bactscout_output", "--output", "-o", help="Path to the output directory"),
    threads: int = typer.Option(4, "--threads", "-t", help="Number of threads to use"),
    config: str = typer.Option("bactscout_config.yml", "--config", "-c", help="Path to the configuration file"),
):
    """Run on a single sample"""
    main(input_dir, output_dir, threads, config_file=config)

@app.command()
def summary(
    input_dir: str = typer.Argument(..., help="Path to the directory containing sample subdirectories"),
    output_dir: str = typer.Option("bactscout_output", "--output", "-o", help="Path to the output directory"),
    config: str = typer.Option("bactscout_config.yml", "--config", "-c", help="Path to the configuration file"),
):
    """Run on a single sample"""
    print('hello')   

if __name__ == "__main__":
    app()