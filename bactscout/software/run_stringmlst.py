"""
StringMLST wrapper module for Multi-Locus Sequence Typing (MLST).

This module provides functions to run StringMLST on paired-end FASTQ files
to determine sequence types based on allelic profiles. StringMLST performs
k-mer based MLST typing directly from raw sequencing reads.
"""

import os
import shutil
import subprocess

from bactscout.util import extract_sample_name, print_message


def run_command(r1, r2, species_db, output_dir, message=False):
    """
    Run StringMLST on paired-end FASTQ files for MLST typing.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        species_db (str): Path to the species-specific MLST database directory.
        output_dir (str): Path to the output directory where results will be saved.
        message (bool): Whether to print success/error messages. Default is False.

    Returns:
        dict: Dictionary containing sample_name, stringmlst_results, and output_dir.
    """

    # Create output directory and ensure it exists
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Extract sample name from R1 file
    sample_name = extract_sample_name(r1)

    # Get StringMLST command
    cmd = get_command()
    cmd = list(cmd) if isinstance(cmd, str) else cmd  # Ensure cmd is a list
    stringmlst_results = {}
    output_file = os.path.abspath(os.path.join(output_dir, "mlst.tsv"))
    # Remove output file if it exists to avoid appending to old results
    try:
        if os.path.exists(output_file):
            os.remove(output_file)
    except (OSError, FileNotFoundError):
        pass  # File doesn't exist or can't be removed, that's fine
    # Build StringMLST command: stringmlst.py --predict -P <database> -1 <reads_R1> -2 <reads_R2> <output_dir>
    # You need the prefix for the db as well,
    # Check if species_db is a directory or file
    if os.path.isdir(species_db):
        db_prefix = os.path.join(
            os.path.abspath(species_db),
            os.path.splitext(os.path.basename(species_db))[0],
        )
    else:
        db_prefix = species_db
    mlst_cmd = cmd + [
        "--predict",
        "-P",
        db_prefix,
        "-1",
        os.path.abspath(r1),
        "-2",
        os.path.abspath(r2),
        "--output",
        output_file,
    ]
    try:
        # Run StringMLST
        if message:
            print_message(f"Running StringMLST for {species_db}...")
            print_message(f"Command: {' '.join(mlst_cmd)}")

        subprocess.run(mlst_cmd, check=True, capture_output=not message)

        # Check if output file was created
        if not os.path.exists(output_file):
            stringmlst_results = {"error": "StringMLST did not create output file."}
            if message:
                print_message(
                    f"Error: StringMLST did not create output file at {output_file}"
                )
        else:
            # Open mlst.tsv add to results (explicitly specify encoding to avoid warnings)
            with open(output_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
                if len(lines) > 1:
                    header = lines[0].strip().split("\t")
                    values = lines[1].strip().split("\t")
                    mlst_data = dict(zip(header, values, strict=False))
                    stringmlst_results = mlst_data
                else:
                    stringmlst_results = {
                        "error": "No MLST results found in output file."
                    }

        if message:
            print_message(f"StringMLST completed successfully for {species_db}")
    except subprocess.CalledProcessError as e:
        stringmlst_results = {"error": f"StringMLST command failed: {e}"}
        if message:
            print_message(f"Error running MLST for {species_db}: {e}")
    except Exception as e:
        stringmlst_results = {"error": f"Unexpected error: {e}"}
        if message:
            print_message(f"Unexpected error in MLST processing: {e}")

    return {
        "sample_name": sample_name,
        "stringmlst_results": stringmlst_results,
        "output_dir": output_dir,
        "error": None,
    }


def get_command():
    """
    Get the StringMLST command, checking system PATH first, then falling back to pixi/conda.

    Returns:
        list: Command as a list of strings for subprocess
    """
    cmd = shutil.which("stringMLST.py")
    # If command is not found, shutil.which returns None, try with pixi run
    if cmd is None:
        cmd = ["pixi", "run", "--", "stringMLST.py"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd
