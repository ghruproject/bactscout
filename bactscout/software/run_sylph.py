"""
Sylph wrapper module for ultrafast metagenomic profiling.

This module provides functions to run Sylph on paired-end FASTQ files
for taxonomic profiling and genome-to-genome distance estimation.
Sylph uses k-mer based methods for rapid analysis of metagenomic samples
against reference databases.
"""

import os
import shutil
import subprocess


def run_command(r1, r2, output_dir, config, message=False, threads=1):
    """
    Run Sylph on paired-end FASTQ files for taxonomic profiling.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        output_dir (str): Path to the output directory where results will be saved.
        config (dict): Configuration dictionary containing bactscout_dbs_path and sylph_db.
        message (bool): Whether to print success/error messages. Default is False.
        threads (int): Number of threads to use for processing. Default is 1.

    Returns:
        dict: Dictionary containing sylph_report path and error information if any.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    errors = None
    sylph_report = os.path.join(output_dir, "sylph_report.txt")
    sylph_errors = os.path.join(output_dir, "sylph_errors.log")
    cmd = get_command()
    database_path = os.path.join(
        config.get("bactscout_dbs_path", ""),
        config.get("sylph_db", "gtdb-r226-c1000-dbv1.syldb"),
    )
    cmd = cmd + [
        "profile",
        database_path,
        "-u",
        "-1",
        r1,
        "-2",
        r2,
        "-t",
        str(threads),
    ]

    try:
        with open(sylph_report, "w", encoding="utf-8") as report_file:
            with open(sylph_errors, "w", encoding="utf-8") as error_file:
                subprocess.run(cmd, stdout=report_file, stderr=error_file, check=True)
        if message:
            print(f"Sylph completed successfully. Results are in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error running Sylph: {e}")
        with open(sylph_errors, "r", encoding="utf-8") as error_file:
            errors = error_file.read()
            print(f"Sylph errors:\n{errors}")

    return {"sylph_report": sylph_report, "errors": errors}


def extract_species_from_report(sylph_report):
    """
    Extract species abundance and reference genome information from Sylph report.

    Parses the Sylph output file to extract:
    - Species names (from contig info)
    - Sequence abundance percentages
    - Coverage estimates
    - Genome file paths (from Genome_file column)

    Args:
        sylph_report (str): Path to Sylph report file

    Returns:
        tuple: (species_abundance, genome_file_path)
            - species_abundance (list): List of tuples (species_name, abundance, coverage)
            - genome_file_path (str): Path to reference genome file (top species), or empty string
    """
    species_abundance = []
    genome_file_path = ""

    try:
        with open(sylph_report, encoding="utf-8") as f:
            next(f)  # Skip header
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")

                # Extract genome file path from column 1 (Genome_file)
                # Only store for the first (top) species
                if len(parts) > 1 and not genome_file_path:
                    genome_file_path = parts[1]

                if len(parts) > 14:
                    contig_info = parts[14]
                    words = contig_info.split()
                    if len(words) >= 3:
                        genus_species = f"{words[1]} {words[2]}"
                        try:
                            abundance = float(parts[3])  # Sequence_abundance column
                        except (ValueError, IndexError):
                            abundance = 0.0
                        try:
                            coverage = float(parts[5])  # Coverage column
                        except (ValueError, IndexError):
                            coverage = 0.0
                        species_abundance.append((genus_species, abundance, coverage))
    except FileNotFoundError:
        print(f"Report file {sylph_report} not found.")

    # Sort by abundance descending
    species_abundance.sort(key=lambda x: x[1], reverse=True)
    return species_abundance, genome_file_path


def get_command():
    """
    Get the Sylph command, checking system PATH first, then falling back to pixi.

    Returns:
        list: Command as a list of strings for subprocess
    """
    cmd = shutil.which("sylph")
    # If commands are not found, shutil.which returns None, try with pixi run.
    if cmd is None:
        cmd = ["pixi", "run", "--", "sylph"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd
