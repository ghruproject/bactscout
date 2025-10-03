import shutil
import subprocess
import os
from pathlib import Path

def run_command(r1, r2, species_db, output_dir, config, message=False):
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
    sample_name = r1_path.stem.replace('_R1', '').replace('.fastq', '').replace('.fq', '')
    
    # Get StringMLST command
    cmd = get_command()
    stringmlst_results = {}
    output_file = os.path.abspath(os.path.join(output_dir, "mlst.tsv"))
    # Remove output file if it exists to avoid appending to old results
    if os.path.exists(output_file):
        os.remove(output_file)
    # Build StringMLST command: stringmlst.py --predict -P <database> -1 <reads_R1> -2 <reads_R2> <output_dir>
    mlst_cmd = cmd + [
        "--predict",
        "-P",
        os.path.abspath(species_db),
        '-1',
        os.path.abspath(r1),
        '-2',
        os.path.abspath(r2),
        '--output',
        output_file
    ]
    
    try:
        # Run StringMLST
        if message:
            print(f"Running StringMLST for {species_db}...")
            print(f"Command: {' '.join(mlst_cmd)}")
            
        subprocess.run(mlst_cmd, check=True, capture_output=not message)
        
        # Store results paths
        stringmlst_results = {
            'output_dir': output_dir,
            'report': os.path.join(output_dir, "report.tsv"),
            'assembled_genes': os.path.join(output_dir, "assembled_genes.fa.gz"),
            'assembled_seqs': os.path.join(output_dir, "assembled_seqs.fa.gz"),
            'log': os.path.join(output_dir, "log.txt")
        }
        
        if message:
            print(f"ARIBA completed successfully for {species_db}")
            print(f"  - Report: {stringmlst_results['report']}")
            
    except subprocess.CalledProcessError as e:
        if message:
            print(f"Error running ARIBA for {species_db}: {e}")
        stringmlst_results[species_db] = {"error": str(e)}

    return {
        'sample_name': sample_name,
        'stringmlst_results': stringmlst_results,
        'output_dir': output_dir
    }


def get_command():
    """
    Get the StringMLST command, checking system PATH first, then falling back to pixi/conda.
    
    Returns:
        list: Command as a list of strings for subprocess
    """
    cmd = shutil.which("stringmlst.py")
    # If command is not found, shutil.which returns None, try with pixi run
    if cmd is None:
        cmd = ["pixi", "run", "--", "stringmlst.py"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd

