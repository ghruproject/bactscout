import os
import shutil
import subprocess


def run_command(r1, r2, output_dir, config, message=False):
    """
    Run Sylph on the input directory and save results to the output directory.

    Args:
        input_dir (str): Path to the input directory containing FASTQ files.
        output_dir (str): Path to the output directory where results will be saved.
        threads (int): Number of threads to use for processing.
    """

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    sylph_report = os.path.join(output_dir, "sylph_report.txt")
    cmd = get_command()
    database_path = os.path.join(
        config.get("bactscout_dbs_path", ""),
        config.get("sylph_db", "gtdb-r226-c1000-dbv1.syldb"),
    )
    cmd = cmd + ["profile", database_path, "-u", "-1", r1, "-2", r2]

    try:
        with open(sylph_report, "w", encoding="utf-8") as report_file:
            subprocess.run(
                cmd, stdout=report_file, stderr=subprocess.DEVNULL, check=True
            )
        if message:
            print(f"Sylph completed successfully. Results are in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error running Sylph: {e}")
    return {"sylph_report": sylph_report}


def extract_species_from_report(sylph_report):
    species_abundance = []
    try:
        with open(sylph_report, encoding="utf-8") as f:
            next(f)  # Skip header
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")
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
    return species_abundance


def get_command():
    cmd = shutil.which("sylph")
    # If commands are not found, shutil.which returns None, try with pixi run.
    if cmd is None:
        cmd = ["pixi", "run", "--", "sylph"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd
