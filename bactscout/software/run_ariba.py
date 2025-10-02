import shutil
import subprocess
import os
from pathlib import Path

def run_command(r1, r2, species_db, output_dir, config, message=False):
    """
    Run ARIBA on paired-end FASTQ files for antimicrobial resistance gene detection.

    Args:
        r1 (str): Path to the R1 (forward) FASTQ file.
        r2 (str): Path to the R2 (reverse) FASTQ file.
        output_dir (str): Path to the output directory where results will be saved.
        config (dict): Configuration dictionary containing ARIBA settings.
        message (bool): Whether to print success/error messages.
    
    Returns:
        dict: Dictionary containing paths to ARIBA output files.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract sample name from R1 file
    r1_path = Path(r1)
    sample_name = r1_path.stem.replace('_R1', '').replace('.fastq', '').replace('.fq', '')
    
    # Get ARIBA command
    cmd = get_command()
    
    # Get database path from config
    bactscout_dbs_path = config.get("bactscout_dbs_path", "bactscout_dbs")
    
    # ARIBA can handle multiple species databases
    ariba_results = {}

    # Build ARIBA command: ariba run <database> <reads_R1> <reads_R2> <output_dir>
    ariba_cmd = cmd + [
        "run",
        species_db,
        r1,
        r2,
        output_dir
    ]
    
    try:
        # Run ARIBA
        if message:
            print(f"Running ARIBA for {species_db}...")
            print(f"Command: {' '.join(ariba_cmd)}")
            
        subprocess.run(ariba_cmd, check=True, capture_output=not message)
        
        # Store results paths
        ariba_results = {
            'output_dir': output_dir,
            'report': os.path.join(output_dir, "report.tsv"),
            'assembled_genes': os.path.join(output_dir, "assembled_genes.fa.gz"),
            'assembled_seqs': os.path.join(output_dir, "assembled_seqs.fa.gz"),
            'log': os.path.join(output_dir, "log.txt")
        }
        
        if message:
            print(f"ARIBA completed successfully for {species_db}")
            print(f"  - Report: {ariba_results['report']}")
            
    except subprocess.CalledProcessError as e:
        if message:
            print(f"Error running ARIBA for {species_db}: {e}")
        ariba_results[species_db] = {"error": str(e)}

    return {
        'sample_name': sample_name,
        'ariba_results': ariba_results,
        'output_dir': output_dir
    }



def get_command():
    """
    Get the ARIBA command, checking system PATH first, then falling back to pixi/conda.
    
    Returns:
        list: Command as a list of strings for subprocess
    """
    cmd = shutil.which("ariba")
    # If command is not found, shutil.which returns None, try with pixi run
    if cmd is None:
        cmd = ["pixi", "run", "--", "ariba"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd

