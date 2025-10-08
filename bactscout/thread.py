import json
import os

from bactscout.software.run_fastp import run_command as run_fastp
from bactscout.software.run_stringmlst import run_command as run_mlst
from bactscout.software.run_sylph import extract_species_from_report
from bactscout.software.run_sylph import run_command as run_sylph
from bactscout.util import print_message


def blank_sample_results(sample_id):
    """
    Generate a blank results dictionary for a given sample.

    This function returns a dictionary containing default values for various sample metrics,
    including read counts, base counts, quality scores, GC content, species identification,
    coverage estimates, and MLST typing. All fields are initialized to indicate that no reads
    have been processed and no analysis has been performed.

    Args:
        sample_id (str or int): Unique identifier for the sample.

    Returns:
        dict: A dictionary with default values for all expected sample result fields.
    """
    return {
        "sample_id": sample_id,
        "total_reads": 0,
        "total_bases": 0,
        "q20_bases": 0,
        "q30_bases": 0,
        "q20_rate": 0.0,
        "q30_rate": 0.0,
        "q30_status": "FAILED",
        "q30_message": "No reads processed. Cannot determine quality metrics.",
        "read1_mean_length": 0,
        "read2_mean_length": 0,
        "read_length_status": "FAILED",
        "read_length_message": "No reads processed. Cannot determine read lengths.",
        "gc_content": 0.0,
        "species": "",
        "species_abundance": "",
        "species_coverage": "",
        "estimated_coverage": 0,
        "expected_genome_size": 0,
        "coverage_status": "FAILED",
        "coverage_message": "No reads processed. Cannot estimate genome size or coverage.",
        "gc_content_lower": 0,
        "gc_content_upper": 0,
        "gc_content_status": "FAILED",
        "gc_content_message": "No reads processed. Cannot determine expected GC content range.",
        "species_status": "FAILED",
        "species_message": "No reads processed. Cannot determine species.",
        "mlst_st": None,
        "mlst_status": "FAILED",
        "mlst_message": "No reads processed. Cannot determine MLST.",
        "contamination_status": "FAILED",
        "contamination_message": "No reads processed. Cannot determine contamination.",
        "estimated_alt_coverage": 0,
        "alt_coverage_message": "No reads processed. Cannot estimate alternative coverage.",
        "alt_coverage_status": "FAILED",
    }


def run_one_sample(
    sample_id, read1_file, read2_file, output_dir, config, message=False
):
    """Run analysis for a single sample."""
    if message:
        print_message(f"Running analysis for {sample_id}", "info")
    # Create output directory if it doesn't exist #
    sample_output_dir = f"{output_dir}/{sample_id}"

    if not os.path.exists(sample_output_dir):
        os.makedirs(sample_output_dir, exist_ok=True)

    # Initialize final results with blank values
    final_results = blank_sample_results(sample_id)
    sylph_result = run_sylph(read1_file, read2_file, sample_output_dir, config)
    species_abundance = extract_species_from_report(sylph_result.get("sylph_report"))

    fastp_result = run_fastp(read1_file, read2_file, sample_output_dir, config)
    fastp_stats = get_fastp_results(fastp_result)
    fastp_stats = handle_fastp_results(fastp_stats, config)
    final_results.update(fastp_stats)

    final_results, species = handle_species_coverage(
        species_abundance, final_results, config
    )
    if species:
        final_results = handle_genome_size(species, fastp_stats, final_results, config)
    # If other species > 10% abundance, skip MLST
    not_contaminated = True
    if len(species) > 1:
        # Sum up abundance of non-top species
        non_top_abundance = sum([s[1] for s in species_abundance[1:]])
        if non_top_abundance > config.get("contamination_threshold", 10):
            final_results["species_status"] = "FAILED"
            final_results["species_message"] = (
                f"Multiple species detected with significant abundance ({non_top_abundance:.2f}%). Skipping MLST."
            )
            not_contaminated = False
    if not_contaminated:
        species = species[0]
        final_results["species_status"] = "PASSED"
        if len(species) == 1:
            final_results["species_message"] = "Single species detected."
        else:
            final_results["species_message"] = (
                "Multiple species detected. Using the top species for MLST."
            )
            final_results["species_status"] = "WARNING"
        final_results = handle_mlst_results(
            final_results=final_results,
            config=config,
            species=species,
            read1_file=read1_file,
            read2_file=read2_file,
            sample_output_dir=sample_output_dir,
            message=message,
        )

    else:
        final_results["species_status"] = "FAILED"
    write_summary_file(final_results, sample_id, sample_output_dir)

    return {
        "status": "success",
        "sample_id": sample_id,
        "results": final_results,
    }


def write_summary_file(final_results, sample_id, sample_output_dir):
    """
    Writes a summary CSV file containing the results for a given sample.

    The function creates a CSV file named '{sample_id}_summary.csv' in the specified
    output directory. The file contains a single row with headers derived from the
    keys of `final_results` and a corresponding row of values.

    Args:
        final_results (dict): Dictionary containing result data, where keys are column headers
            and values are the corresponding data for the sample.
        sample_id (str): Identifier for the sample, used to name the output file.
        sample_output_dir (str): Directory path where the summary file will be saved.

    Returns:
        None
    """
    final_output_file = os.path.join(sample_output_dir, f"{sample_id}_summary.csv")
    with open(final_output_file, "w", encoding="utf-8") as f:
        # Write header
        headers = list(final_results.keys())
        # Sort: sample_id first, then *_status, then alphabetical
        headers = sorted(
            final_results.keys(),
            key=lambda x: (x != "sample_id", not x.endswith("_status"), x),
            # or: (0 if x == "sample_id" else 1, 0 if x.endswith("_status") else 1, x)
        )
        f.write(",".join(headers) + "\n")
        # Write values
        values = [
            str(final_results[h]) if final_results[h] is not None else ""
            for h in headers
        ]
        f.write(",".join(values) + "\n")


def handle_fastp_results(fastp_results, config):
    """
    Updates fastp_results dictionary with status and messages for Q30 and read length metrics.

    Args:
        fastp_results (dict): Dictionary containing fastp metrics.
        config (dict): Configuration dictionary with thresholds:
            - q30_pass_threshold (int): Minimum Q30 rate (%) to pass.
            - read_length_pass_threshold (int): Minimum mean read length to pass.

    Returns:
        dict: Updated fastp_results with status and message fields.
    """
    q30_threshold = config.get("q30_pass_threshold", 0.80)
    if q30_threshold > 1:
        q30_threshold /= 100
    read_length_threshold = config.get("read_length_pass_threshold", 100)

    # Q30 status and message
    if fastp_results.get("total_reads", 0) == 0:
        fastp_results["q30_status"] = "FAILED"
        fastp_results["q30_message"] = (
            "No reads processed. Cannot determine quality metrics."
        )
    elif fastp_results.get("q30_rate", 0.0) >= q30_threshold:
        fastp_results["q30_status"] = "PASSED"
        fastp_results["q30_message"] = (
            f"Q30 rate {fastp_results['q30_rate']:.2f} meets threshold ({q30_threshold})."
        )
    else:
        fastp_results["q30_status"] = "FAILED"
        fastp_results["q30_message"] = (
            f"Q30 rate {fastp_results['q30_rate']:.2f} below threshold ({q30_threshold})."
        )

    # Read length status and message
    read1_len = fastp_results.get("read1_mean_length", 0)
    read2_len = fastp_results.get("read2_mean_length", 0)
    if fastp_results.get("total_reads", 0) == 0:
        fastp_results["read_length_status"] = "FAILED"
        fastp_results["read_length_message"] = (
            "No reads processed. Cannot determine read lengths."
        )
    elif read1_len >= read_length_threshold and read2_len >= read_length_threshold:
        fastp_results["read_length_status"] = "PASSED"
        fastp_results["read_length_message"] = (
            f"Read1 mean length {read1_len}; Read2 mean length {read2_len} meet threshold (>{read_length_threshold})."
        )
    else:
        fastp_results["read_length_status"] = "FAILED"
        fastp_results["read_length_message"] = (
            f"Read1 mean length {read1_len}; Read2 mean length {read2_len} below threshold (>{read_length_threshold})."
        )

    return fastp_results


def handle_species_coverage(species_abundance, final_results, config):
    coverage_cutoff = config.get("coverage_threshold", 30)
    contamination_cutoff = config.get("contamination_threshold", 10)
    if not species_abundance:
        final_results["coverage_status"] = "FAILED"
        final_results["contamination_status"] = "FAILED"
        final_results["coverage_message"] = (
            "No species detected. Cannot estimate genome size or coverage."
        )
        final_results["gc_content_message"] = (
            "No species detected. Cannot determine expected GC content range."
        )
        final_results["species_status"] = "FAILED"
        final_results["species_message"] = "No species detected."
        return final_results, []
    # species is the first element of the tuple, sorted by abundance
    species = [
        s[0] for s in sorted(species_abundance, key=lambda x: x[1], reverse=True)
    ]
    if len(species) == 1:
        final_results["species_status"] = "PASSED"
        final_results["species_message"] = ""
    elif len(species) > 1:
        final_results["species_status"] = "WARNING"
        final_results["species_message"] = (
            "Multiple species detected. Using the top species for genome size and coverage estimation."
        )
    final_results["species"] = ";".join(species)
    final_results["species_abundance"] = ";".join(
        [str(s[1]) for s in species_abundance]
    )
    final_results["species_coverage"] = ";".join([str(s[2]) for s in species_abundance])
    top_species = species_abundance[0] if species_abundance else None
    if top_species and top_species[2] >= coverage_cutoff:
        final_results["coverage_status"] = "PASSED"
        final_results["coverage_message"] = (
            f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x meets the threshold of {coverage_cutoff}x."
        )
    else:
        final_results["coverage_message"] = (
            f"Top species {top_species[0]} with coverage {top_species[2]:.2f}x falls below the threshold of {coverage_cutoff}x."
        )
        final_results["coverage_status"] = "FAILED"
    if top_species and top_species[1] > (100 - contamination_cutoff):
        final_results["contamination_status"] = "PASSED"
        final_results["contamination_message"] = ""
    else:
        final_results["contamination_message"] = (
            f"Top species {top_species[0]} with contamination {top_species[1]:.2f}x exceeds the threshold of {contamination_cutoff}x."
        )
        final_results["contamination_status"] = "FAILED"
    return final_results, species


def handle_mlst_results(
    final_results,
    config,
    species,
    read1_file,
    read2_file,
    sample_output_dir,
    message,
):
    # Run ARIBA if a single species is identified
    # Need to determine the species_db path
    species_key = None
    # This locates the  correct fodler name for the mlst Db in cases where species exactly matches.
    # e.g klebsiella_pneumoniae: 'Klebsiella pneumoniae'
    for key, value in config["mlst_species"].items():
        if value == species:
            species_key = key
            break
    # In case the species name has a number at the end e.g Escherichia coli#1 or Neisseria spp.
    # In this case species dir will be species.replace(" ", "_").lower()
    if not species_key:
        species_simple = species[0].replace(" ", "_").lower()
        if species_simple in config["mlst_species"]:
            species_key = species_simple

    if species_key:
        species_db_path = os.path.join(
            config["bactscout_dbs_path"], species_key, species_key
        )
        mlst_result = run_mlst(
            read1_file, read2_file, species_db_path, sample_output_dir, config
        )
        # Check MLST results
        if mlst_result.get("stringmlst_results", {}).get("ST"):
            final_results["mlst_st"] = mlst_result["stringmlst_results"]["ST"]
            if int(final_results["mlst_st"]) > 0:
                final_results["mlst_status"] = "PASSED"
                final_results["mlst_message"] = (
                    f"Valid ST found: {mlst_result['stringmlst_results']['ST']}"
                )
            else:
                final_results["mlst_status"] = "FAILED"
                final_results["mlst_message"] = "No valid ST found."
        else:
            final_results["mlst_st"] = None
            final_results["mlst_status"] = "FAILED"
            final_results["mlst_message"] = "No valid ST found."
    else:
        final_results["mlst_message"] = (
            "No MLST database found for species. Install via config.yml."
        )
        if message:
            print_message(
                f"No MLST database found for species: {species}. Skipping MLST.",
                "warning",
            )
    return final_results


def handle_genome_size(species_list, fastp_stats, final_results, config):
    """
    Evaluates genome coverage and GC content for a given sample based on species prediction and sequencing statistics.

    Parameters:
        species_list (list): List of detected species names, with the top species at index 0.
        fastp_stats (dict): Dictionary containing sequencing statistics, including 'total_bases' and 'gc_content'.
        final_results (dict): Dictionary to store the evaluation results and messages.
        config (dict): Configuration dictionary containing thresholds and expected genome size information.

    Returns:
        dict: Updated final_results dictionary with estimated coverage, expected genome size, coverage status/message,
              GC content range, and GC content status/message.

    Notes:
        - If multiple species are detected, only the top species is used for evaluation, and a warning is added.
        - Coverage is calculated as total_bases / expected_genome_size.
        - Coverage and GC content are evaluated against thresholds and expected ranges from config.
    """
    # Get expected genome size,
    coverage_cutoff = config.get("coverage_threshold", 30)
    species = species_list[0]  # Use the top species only
    warning = ""
    if len(species_list) > 1:
        warning = "Warning: Multiple species detected. Using the top species."
    expected_genome_size, gc_lower, gc_upper = get_expected_genome_size(species, config)
    # Get estimated coverage and eval fastp results
    if expected_genome_size > 0 and fastp_stats.get("total_bases", 0) > 0:
        estimated_coverage = fastp_stats["total_bases"] / expected_genome_size
    else:
        estimated_coverage = 0
    final_results["estimated_alt_coverage"] = round(estimated_coverage, 2)
    final_results["expected_genome_size"] = expected_genome_size
    if estimated_coverage >= coverage_cutoff:
        final_results["alt_coverage_status"] = "PASSED"
        final_results["alt_coverage_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x meets the threshold of {coverage_cutoff}x."
            + warning
        )
    else:
        final_results["alt_coverage_status"] = "FAILED"
        final_results["alt_coverage_message"] = (
            f"Estimated coverage {estimated_coverage:.2f}x below the threshold of {coverage_cutoff}x."
            + warning
        )
    final_results["gc_content_lower"] = gc_lower
    final_results["gc_content_upper"] = gc_upper
    if gc_lower > 0 and gc_upper > 0:
        if gc_lower <= fastp_stats.get("gc_content", 0) <= gc_upper:
            final_results["gc_content_status"] = "PASSED"
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% within expected range ({gc_lower}-{gc_upper}%)"
                + warning
            )
        else:
            final_results["gc_content_message"] = (
                f"GC content {fastp_stats.get('gc_content', 0)}% outside expected range ({gc_lower}-{gc_upper}%)"
                + warning
            )
    return final_results


def get_fastp_results(fastp_results):
    """
    Extracts quality metrics from a fastp JSON report after filtering.

    Parameters:
        fastp_results (dict): Dictionary containing fastp run information.
            Expected keys:
                - "status": Should be "success" if fastp ran successfully.
                - "json_report": Path to the fastp JSON report file.

    Returns:
        dict: Dictionary of metrics from the 'after_filtering' section of the fastp report, including:
            - total_reads (int): Number of reads after filtering.
            - total_bases (int): Number of bases after filtering.
            - q20_bases (int): Number of bases with quality >= Q20.
            - q30_bases (int): Number of bases with quality >= Q30.
            - q20_rate (float): Percentage of bases with quality >= Q20.
            - q30_rate (float): Percentage of bases with quality >= Q30.
            - read1_mean_length (int): Mean length of read 1 after filtering.
            - read2_mean_length (int): Mean length of read 2 after filtering.
            - gc_content (float): GC content percentage after filtering (rounded to 4 decimals).

    If the fastp run was unsuccessful or the report file is missing, returns a dictionary with zeroed/default values for all metrics.
    """
    failed = {
        "total_reads": 0,
        "total_bases": 0,
        "q20_bases": 0,
        "q30_bases": 0,
        "q20_rate": 0.0,
        "q30_rate": 0.0,
        "read1_mean_length": 0,
        "read2_mean_length": 0,
        "gc_content": 0.0,
    }
    if fastp_results.get("status") != "success":
        return failed
    fastp_json = fastp_results.get("json_report")
    if not fastp_json or not os.path.exists(fastp_json):
        return failed

    with open(fastp_json, encoding="utf-8") as f:
        data = json.load(f)

    after_filtering = data.get("summary").get("after_filtering", failed)
    after_filtering["gc_content"] = round(float(after_filtering["gc_content"] * 100), 4)
    return after_filtering


def get_expected_genome_size(species, config):
    """
    Retrieves the expected genome size and GC content range for a given species from a metrics CSV file.

    Args:
        species (str): The scientific name of the species (e.g., "Streptococcus agalactiae").
        config (dict): Configuration dictionary containing the path to the metrics file under the key "metrics_file".

    Returns:
        tuple:
            genome_size (float): The expected genome size (average of lower and upper bounds) for the species.
            gc_lower (int): The lower bound of GC content percentage for the species.
            gc_upper (int): The upper bound of GC content percentage for the species.

    Notes:
        - The metrics file is expected to contain lines in the format:
            <species_name>,Genome_Size,<lower>,<upper>
            <species_name>,GC_Content,<lower>,<upper>
        - Species names in the file should use underscores instead of spaces or periods.
        - If no matching entry is found, returns zeros for all values.
    """
    metrics_file = config.get("metrics_file")
    safe_species_name = species.replace(" ", "_").replace(".", "_")
    genome_size = 0
    gc_lower = 0
    gc_upper = 0
    with open(metrics_file, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(",")
            # Line should be line Streptococcus_agalactiae,Genome_Size,<lower>,<upper>
            if line.startswith(safe_species_name) and "Genome_Size" in line:
                genome_size = (int(parts[2]) + int(parts[3])) / 2
            # Also return GC Content, from Streptococcus_agalactiae,GC_Content,35,37
            if line.startswith(safe_species_name) and "GC_Content" in line:
                gc_lower = int(parts[2])
                gc_upper = int(parts[3])
    return genome_size, gc_lower, gc_upper
