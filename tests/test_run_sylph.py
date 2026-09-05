import subprocess
from unittest.mock import MagicMock, mock_open, patch

from bactscout.software.run_sylph import (
    extract_species_from_report,
    get_command,
    run_command_single,
)
from bactscout.thread import handle_species_coverage


SYLPH_HEADER = "\t".join(
    [
        "Sample_file",
        "Genome_file",
        "Taxonomic_abundance",
        "Sequence_abundance",
        "Adjusted_ANI",
        "True_cov",
        "ANI_5-95_percentile",
        "Eff_lambda",
        "Lambda_5-95_percentile",
        "Median_cov",
        "Mean_cov_geq1",
        "Containment_ind",
        "Naive_ANI",
        "kmers_reassigned",
        "Contig_name",
    ]
)


def sylph_row(genome, taxonomic_abundance, sequence_abundance, coverage, contig_name):
    return "\t".join(
        [
            "sample",
            genome,
            str(taxonomic_abundance),
            str(sequence_abundance),
            "99",
            str(coverage),
            "NA-NA",
            "HIGH",
            "NA-NA",
            "0",
            "0",
            "0/0",
            "99",
            "0",
            contig_name,
        ]
    )


def test_get_command_sylph_in_path():
    """Test get_command when sylph is found in PATH."""
    with patch("shutil.which") as mock_which:
        # Mock sylph found in PATH
        mock_which.return_value = "/usr/bin/sylph"

        result = get_command()

        assert result == ["/usr/bin/sylph"]
        mock_which.assert_called_once_with("sylph")


def test_get_command_sylph_not_in_path():
    """Test get_command when sylph not in PATH - falls back to pixi."""
    with patch("shutil.which") as mock_which:
        # Mock sylph not found
        mock_which.return_value = None

        result = get_command()

        assert result == ["pixi", "run", "--", "sylph"]
        mock_which.assert_called_once_with("sylph")


def test_get_command_returns_list():
    """Test that get_command always returns a list."""
    result = get_command()
    assert isinstance(result, list)
    assert len(result) > 0


def test_extract_species_collapses_duplicate_reference_rows(tmp_path):
    report = tmp_path / "sylph_report.txt"
    report.write_text(
        "\n".join(
            [
                SYLPH_HEADER,
                sylph_row(
                    "GCF_001.fna.gz",
                    39.0,
                    30.0,
                    18.0,
                    "contig1 Escherichia coli strain A",
                ),
                sylph_row(
                    "GCF_002.fna.gz",
                    58.5,
                    45.0,
                    24.0,
                    "contig2 Escherichia coli strain B",
                ),
                sylph_row(
                    "GCF_003.fna.gz",
                    2.5,
                    2.0,
                    1.0,
                    "contig3 Klebsiella pneumoniae strain C",
                ),
            ]
        ),
        encoding="utf-8",
    )

    species_abundance, genome_file_path = extract_species_from_report(report)

    assert species_abundance == [
        ("Escherichia coli", 97.5, 24.0),
        ("Klebsiella pneumoniae", 2.5, 1.0),
    ]
    assert genome_file_path == "GCF_001.fna.gz"

    results, species = handle_species_coverage(species_abundance, {}, {})

    assert species == ["Escherichia coli", "Klebsiella pneumoniae"]
    assert results["contamination_status"] == "PASSED"


def test_single_species_uses_taxonomic_abundance_for_contamination(tmp_path):
    report = tmp_path / "sylph_report.txt"
    report.write_text(
        "\n".join(
            [
                SYLPH_HEADER,
                sylph_row(
                    "GCF_004.fna.gz",
                    100.0,
                    80.0,
                    35.0,
                    "contig4 Escherichia coli strain D",
                ),
            ]
        ),
        encoding="utf-8",
    )

    species_abundance, _genome_file_path = extract_species_from_report(report)
    results, species = handle_species_coverage(species_abundance, {}, {})

    assert species_abundance == [("Escherichia coli", 100.0, 35.0)]
    assert species == ["Escherichia coli"]
    assert results["contamination_status"] == "PASSED"


def test_run_command_single_success(tmp_path):
    reads = tmp_path / "sample.fastq.gz"
    reads.touch()
    output_dir = tmp_path / "output"
    config = {"bactscout_dbs_path": "/db", "sylph_db": "db.syldb"}

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_sylph.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open()):
        mock_get_cmd.return_value = ["sylph"]
        mock_run.return_value = MagicMock(returncode=0)

        result = run_command_single(str(reads), str(output_dir), config, threads=3)

        assert result["errors"] is None
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        assert command[:3] == ["sylph", "profile", "/db/db.syldb"]
        assert str(reads) in command
        assert "-t" in command
        assert "3" in command


def test_run_command_single_failure(tmp_path):
    reads = tmp_path / "sample.fastq.gz"
    reads.touch()
    output_dir = tmp_path / "output"
    config = {"bactscout_dbs_path": "/db", "sylph_db": "db.syldb"}

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_sylph.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open(read_data="boom")):
        mock_get_cmd.return_value = ["sylph"]
        mock_run.side_effect = subprocess.CalledProcessError(1, ["sylph"])

        result = run_command_single(str(reads), str(output_dir), config, threads=1)

        assert result["errors"] == "boom"
