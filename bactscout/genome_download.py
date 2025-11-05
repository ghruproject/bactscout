"""
Reference genome download and caching module for BactScout.

This module provides utilities for downloading reference genomes from NCBI
based on accession IDs extracted from Sylph output, with local caching to
avoid redundant downloads.

Key Functions:
    - extract_accession_from_path(): Extract GCF/GCA accession from genome file path
    - download_genome(): Download a genome from NCBI
    - cache_genome(): Cache downloaded genome locally
    - get_cached_genome(): Retrieve cached genome
    - ensure_genome_downloaded(): Download if not cached

Workflow:
    1. Extract accession from Sylph genome file path (e.g., GCF_000742135.1)
    2. Check if genome already cached locally
    3. If not cached: Download from NCBI and store
    4. Return local path to genome file

Dependencies:
    - requests: HTTP requests for downloading
    - bactscout.util: Utility functions

Example:
    >>> from bactscout.genome_download import extract_accession_from_path
    >>> path = "gtdb_genomes_reps_r226/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz"
    >>> accession = extract_accession_from_path(path)
    >>> print(accession)
    GCF_000742135.1
"""

import os
import re
from pathlib import Path

import requests

from bactscout.util import print_message


def extract_accession_from_path(genome_file_path: str) -> str:
    """
    Extract the NCBI accession ID from a genome file path.

    Parses paths like:
    - gtdb_genomes_reps_r226/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz
    - GCF_000742135.1_genomic.fna.gz
    - /path/to/GCA_000005845.2_genomic.fna.gz

    Extracts the accession pattern: GCF_XXXXXXXXX.X or GCA_XXXXXXXXX.X

    Args:
        genome_file_path (str): Full or partial path to genome file

    Returns:
        str: NCBI accession ID (e.g., "GCF_000742135.1") or empty string if not found
    """
    # Match pattern GCF_XXXXXXXXX.X or GCA_XXXXXXXXX.X
    match = re.search(r"(GC[FA]_\d{9}\.\d)", genome_file_path)
    if match:
        return match.group(1)
    return ""


def build_ncbi_url(accession: str) -> str:
    """
    Build NCBI FTP URL for genome download.

    Args:
        accession (str): NCBI accession ID (e.g., "GCF_000742135.1")

    Returns:
        str: NCBI FTP URL for genomic FASTA file

    Example:
        >>> build_ncbi_url("GCF_000742135.1")
        'ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/742/135/GCF_000742135.1/GCF_000742135.1_genomic.fna.gz'
    """
    # Parse accession: GCF_000742135.1 -> GCF/000/742/135
    if not accession or len(accession) < 13:
        return ""

    type_prefix = accession[:3]  # GCF or GCA
    numeric_part = accession[4:13]  # 000742135 from GCF_000742135.1

    # Build directory structure
    dir1 = numeric_part[0:3]  # 000
    dir2 = numeric_part[3:6]  # 742
    dir3 = numeric_part[6:9]  # 135

    filename = f"{accession}_genomic.fna.gz"
    url = f"ftp://ftp.ncbi.nlm.nih.gov/genomes/all/{type_prefix}/{dir1}/{dir2}/{dir3}/{accession}/{filename}"

    return url


def download_genome_from_ncbi(accession: str, destination: str) -> bool:
    """
    Download a genome from NCBI.

    Args:
        accession (str): NCBI accession ID (e.g., "GCF_000742135.1")
        destination (str): Local file path where genome will be saved

    Returns:
        bool: True if successful, False otherwise
    """
    url = build_ncbi_url(accession)

    if not url:
        print_message(f"Could not build URL for accession {accession}", "error")
        return False

    try:
        print_message(f"Downloading {accession} from NCBI...", "info")
        response = requests.get(url, timeout=300, stream=True)
        response.raise_for_status()

        # Ensure destination directory exists
        Path(destination).parent.mkdir(parents=True, exist_ok=True)

        # Write file
        with open(destination, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        print_message(
            f"Successfully downloaded {accession} to {destination}", "success"
        )
        return True

    except requests.exceptions.RequestException as e:
        print_message(f"Failed to download {accession} from NCBI: {e}", "error")
        return False
    except OSError as e:
        print_message(f"Failed to write {destination}: {e}", "error")
        return False


def get_cached_genome_path(accession: str, cache_dir: str) -> str:
    """
    Get the local cache path for a genome.

    Args:
        accession (str): NCBI accession ID
        cache_dir (str): Base cache directory

    Returns:
        str: Full path to cached genome file
    """
    filename = f"{accession}_genomic.fna.gz"
    return os.path.join(cache_dir, filename)


def ensure_genome_downloaded(
    accession: str, cache_dir: str, force_download: bool = False
) -> str:
    """
    Ensure a genome is available locally, downloading if necessary.

    Checks if genome is already cached. If not (or if force_download=True),
    downloads from NCBI and caches locally. Subsequent calls for the same
    accession will use the cached copy.

    Args:
        accession (str): NCBI accession ID (e.g., "GCF_000742135.1")
        cache_dir (str): Directory to cache genomes
        force_download (bool): Force re-download even if cached

    Returns:
        str: Local path to genome file (or empty string if download failed)
    """
    cache_path = get_cached_genome_path(accession, cache_dir)

    # Check if already cached
    if os.path.exists(cache_path) and not force_download:
        print_message(f"Using cached genome: {cache_path}", "info")
        return cache_path

    # Download if not cached
    if download_genome_from_ncbi(accession, cache_path):
        return cache_path

    return ""


def download_reference_genomes(sample_results_list: list, output_dir: str) -> list:
    """
    Download reference genomes for all samples in results list.

    Extracts accessions from sample results and downloads genomes to a cache
    directory within the output folder. Caches genomes to avoid re-downloading
    duplicates. Updates sample results with path to downloaded genome.

    Args:
        sample_results_list (list): List of sample result dictionaries
            Each dict should have 'results' key containing sample data
        output_dir (str): Base output directory

    Returns:
        list: Updated sample results list with 'ref_genome' field added
    """
    cache_dir = os.path.join(output_dir, "reference_genomes")

    for sample_result in sample_results_list:
        if "results" not in sample_result:
            continue

        results = sample_result["results"]

        # Extract genome path from results (if present)
        genome_path = results.get("genome_file_path", "")
        if not genome_path:
            # No genome path -> ensure ref_genome empty for consistency
            results["ref_genome"] = ""
            continue

        # Extract accession
        accession = extract_accession_from_path(genome_path)
        if not accession:
            print_message(f"Could not extract accession from {genome_path}", "warning")
            results["ref_genome"] = ""
            continue

        # Ensure genome is downloaded
        local_genome = ensure_genome_downloaded(accession, cache_dir)
        if local_genome:
            # Store accession for downstream use
            results["ref_genome"] = accession
        else:
            results["ref_genome"] = ""

    return sample_results_list
