#!/usr/bin/env python3
"""Download reference genomes from the NCBI Datasets API for long-read validation."""

import argparse
import pathlib
import urllib.request
import zipfile


def accession_to_url(accession: str) -> str:
    return (
        "https://api.ncbi.nlm.nih.gov/datasets/v2/genome/accession/"
        f"{accession}/download?include_annotation_type=GENOME_FASTA"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir")
    parser.add_argument("accessions", nargs="+")
    args = parser.parse_args()

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for accession in args.accessions:
        destination = output_dir / f"{accession}.fna"
        if destination.exists():
            print(f"Using cached genome: {destination}")
            continue
        url = accession_to_url(accession)
        print(f"Downloading {accession} from {url}")
        zip_path = output_dir / f"{accession}.zip"
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            genome_members = [
                name for name in zf.namelist() if name.endswith("_genomic.fna")
            ]
            if not genome_members:
                raise FileNotFoundError(f"No genomic FASTA found for {accession}")
            member = genome_members[0]
            with zf.open(member) as src, open(destination, "wb") as dst:
                dst.write(src.read())
        zip_path.unlink()


if __name__ == "__main__":
    main()