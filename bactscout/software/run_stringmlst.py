import os
import shutil
import subprocess
from pathlib import Path


def run_command(r1, r2, species_db, output_dir, config, message=False, threads=1):
    """
    Run StringMLSt on paired-end FASTQ files for antimicrobial resistance gene detection.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        output_dir (str): Path to the output directory where results will be saved.
        config (dict): Configuration dictionary containing ARIBA settings.
        message (bool): Whether to print success/error messages.

    Returns:
        dict: Dictionary containing paths to StringMLST output files.
    """

    # Create output directory and ensure it exists
    output_dir = os.path.abspath(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Extract sample name from R1 file
    r1_path = Path(r1)
    sample_name = (
        r1_path.stem.replace("_R1", "").replace(".fastq", "").replace(".fq", "")
    )

    # Get StringMLST command
    cmd = get_command()
    stringmlst_results = {}
    output_file = os.path.abspath(os.path.join(output_dir, "mlst.tsv"))
    # Remove output file if it exists to avoid appending to old results
    try:
        if os.path.exists(output_file):
            os.remove(output_file)
    except (OSError, FileNotFoundError):
        pass  # File doesn't exist or can't be removed, that's fine
    # Build StringMLST command: stringmlst.py --predict -P <database> -1 <reads_R1> -2 <reads_R2> <output_dir>
    mlst_cmd = cmd + [
        "--predict",
        "-P",
        os.path.abspath(species_db),
        "-1",
        os.path.abspath(r1),
        "-2",
        os.path.abspath(r2),
        "--output",
        output_file,
        "--threads",
        str(threads),
    ]
    try:
        # Run StringMLST
        if message:
            print(f"Running StringMLST for {species_db}...")
            print(f"Command: {' '.join(mlst_cmd)}")

        subprocess.run(mlst_cmd, check=True, capture_output=not message)
        
        # Check if output file was created
        if not os.path.exists(output_file):
            stringmlst_results = {"error": "StringMLST did not create output file."}
            if message:
                print(f"Error: StringMLST did not create output file at {output_file}")
        else:
            # Open mlst.tsv add to results
            with open(output_file) as f:
                lines = f.readlines()
                if len(lines) > 1:
                    header = lines[0].strip().split("\t")
                    values = lines[1].strip().split("\t")
                    mlst_data = dict(zip(header, values, strict=False))
                    stringmlst_results = mlst_data
                else:
                    stringmlst_results = {"error": "No MLST results found in output file."}

            if message:
                print(f"StringMLST completed successfully for {species_db}")
    except subprocess.CalledProcessError as e:
        stringmlst_results = {"error": f"StringMLST command failed: {e}"}
        if message:
            print(f"Error running MLST for {species_db}: {e}")
    except Exception as e:
        stringmlst_results = {"error": f"Unexpected error: {e}"}
        if message:
            print(f"Unexpected error in MLST processing: {e}")

    return {
        "sample_name": sample_name,
        "stringmlst_results": stringmlst_results,
        "output_dir": output_dir,
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
