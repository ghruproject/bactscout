import csv

from bactscout.long.collect import extract_long_sample_name, run_one_long_sample


def test_extract_long_sample_name_strips_extension_only():
    assert extract_long_sample_name("sample_1.fastq.gz") == "sample_1"
    assert extract_long_sample_name("sample_R1.fq") == "sample_R1"


def test_run_one_long_sample_writes_summary(monkeypatch, tmp_path):
    reads = tmp_path / "sample_1.fastq.gz"
    reads.write_text("@r1\nACGT\n+\nIIII\n")
    output_dir = tmp_path / "output"
    metrics = tmp_path / "metrics.csv"
    metrics.write_text(
        "Klebsiella_pneumoniae,Genome_Size,5000000,6000000\n"
        "Klebsiella_pneumoniae,GC_Content,56,59\n"
    )
    config = {
        "metrics_file": str(metrics),
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
        "bactscout_dbs_path": "bactscout_dbs",
        "sylph_db": "db.syldb",
    }

    monkeypatch.setattr(
        "bactscout.long.collect.run_nanoq",
        lambda *a, **k: {
            "read_count": 1000,
            "total_bases": 275000000,
            "n50": 15000,
            "mean_len": 12000,
            "median_len": 11000,
            "mean_q": 16.4,
            "median_q": 16.0,
        },
    )
    monkeypatch.setattr(
        "bactscout.long.collect.run_sylph_single",
        lambda *a, **k: {"sylph_report": str(tmp_path / "sylph_report.txt")},
    )
    monkeypatch.setattr(
        "bactscout.long.collect.extract_species_from_report",
        lambda *a, **k: ([('Klebsiella pneumoniae', 95.0, 42.0)], "ref"),
    )

    result = run_one_long_sample(
        "sample_1",
        str(reads),
        str(output_dir),
        config,
        "ont_r10",
        threads=1,
        message=False,
        report_resources=False,
    )

    summary_file = output_dir / "sample_1" / "sample_1_long_summary.csv"
    assert result["status"] == "success"
    assert summary_file.exists()
    with open(summary_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["status"] == "PASSED"
    assert rows[0]["top_taxon"] == "Klebsiella pneumoniae"


def test_run_one_long_sample_warns_when_genome_size_missing(monkeypatch, tmp_path):
    reads = tmp_path / "mystery.fastq.gz"
    reads.write_text("@r1\nACGT\n+\nIIII\n")
    output_dir = tmp_path / "output"
    metrics = tmp_path / "metrics.csv"
    metrics.write_text("species,metric,lower_bounds,upper_bounds\n")
    config = {
        "metrics_file": str(metrics),
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
        "bactscout_dbs_path": "bactscout_dbs",
        "sylph_db": "db.syldb",
    }

    monkeypatch.setattr(
        "bactscout.long.collect.run_nanoq",
        lambda *a, **k: {
            "read_count": 1000,
            "total_bases": 275000000,
            "n50": 15000,
            "mean_len": 12000,
            "median_len": 11000,
            "mean_q": 16.4,
            "median_q": 16.0,
        },
    )
    monkeypatch.setattr(
        "bactscout.long.collect.run_sylph_single",
        lambda *a, **k: {"sylph_report": str(tmp_path / "sylph_report.txt")},
    )
    monkeypatch.setattr(
        "bactscout.long.collect.extract_species_from_report",
        lambda *a, **k: ([('Uncatalogued bacterium', 95.0, 42.0)], "ref"),
    )

    result = run_one_long_sample(
        "mystery",
        str(reads),
        str(output_dir),
        config,
        "ont_r10",
        threads=1,
        message=False,
        report_resources=False,
    )

    assert result["results"]["status"] == "WARNING"
    assert result["results"]["flag_coverage_calc"] == "WARNING"