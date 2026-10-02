import csv
import gzip
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from bactscout.config import DEFAULT_CONFIG
from bactscout.software.run_sylph import get_command


@pytest.mark.integration
@pytest.mark.slow
def test_sample_data_qc(tmp_path):
    project_root = Path(__file__).resolve().parent.parent
    sample_dir = project_root / "sample_data"
    assert sample_dir.exists(), f"sample_data directory missing at {sample_dir}"

    output_dir = tmp_path / "qc_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # A small index derived from the input tests real tool plumbing, not taxonomic
    # accuracy. Avoid downloading GTDB and MLST databases in parallel CI workers.
    reference = tmp_path / "smoke_reference.fasta"
    sequences = []
    with gzip.open(sample_dir / "GCA_000292405.1_R1.fastq.gz", "rt") as reads:
        for _ in range(1000):
            if not reads.readline():
                break
            sequences.append(reads.readline().strip())
            reads.readline()
            reads.readline()
    assert sequences, "The checked-in FASTQ fixture contains no reads"
    reference.write_text(
        ">smoke_reference\n" + ("N" * 31).join(sequences) + "\n", encoding="utf-8"
    )
    database_prefix = tmp_path / "smoke"
    sketch = subprocess.run(
        get_command() + ["sketch", "-g", str(reference), "-o", str(database_prefix)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert sketch.returncode == 0, (
        f"Sylph sketch failed:\nSTDOUT: {sketch.stdout}\nSTDERR: {sketch.stderr}"
    )
    assert database_prefix.with_suffix(".syldb").is_file()
    with open(DEFAULT_CONFIG, encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    config.update(
        sylph_db="smoke.syldb",
        mlst_species={},
        system_resources={"cpus": 1, "memory": "1.GB"},
    )
    config_path = tmp_path / "smoke.yml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "bactscout.cli",
        "qc",
        str(sample_dir),
        "--output",
        str(output_dir),
        "--threads",
        "1",
        "--config",
        str(config_path),
        "--database",
        str(tmp_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)

    assert (
        result.returncode == 0
    ), f"Command failed with:\nSTDERR: {result.stderr}\nSTDOUT: {result.stdout}"

    generated_files = list(output_dir.rglob("*.csv"))
    assert generated_files, (
        f"QC run produced no output files in {output_dir}\n"
        f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    )
    with (output_dir / "final_summary.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["sample_id"] == "GCA_000292405.1"
    assert int(rows[0]["read_total_reads"]) > 0
    sample_output = output_dir / "GCA_000292405.1"
    report = (sample_output / "sylph_report.txt").read_text(encoding="utf-8")
    assert "Taxonomic_abundance" in report.splitlines()[0]
