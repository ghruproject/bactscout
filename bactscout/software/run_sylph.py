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
    cmd = cmd + ["profile", database_path, "-1", r1, "-2", r2]

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
    species_list = []
    try:
        with open(sylph_report, encoding="utf-8") as f:
            header = next(f)
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split("\t")
                if len(parts) > 14:
                    contig_info = parts[14]
                    # Extract genus and species (first two words)
                    words = contig_info.split()
                    if len(words) >= 3:
                        genus_species = f"{words[1]} {words[2]}"
                        species_list.append(genus_species)
    except FileNotFoundError:
        print(f"Report file {sylph_report} not found.")
    return list(set(species_list))


def get_command():
    cmd = shutil.which("sylph")
    # If commands are not found, shutil.which returns None, try with pixi run.
    if cmd is None:
        cmd = ["pixi", "run", "--", "sylph"]
    else:
        # Convert string path to list for consistent handling
        cmd = [cmd]
    return cmd
