"""Regression tests for short-read QC warning boundaries and rollup."""

from pathlib import Path

import pytest
import yaml

from bactscout.thread import (
    final_status_pass,
    handle_fastp_results,
    handle_genome_size,
    handle_species_coverage,
)


@pytest.fixture
def config():
    return yaml.safe_load(
        (
            Path(__file__).parents[1] / "bactscout/config/bactscout_config.yml"
        ).read_text()
    )


@pytest.mark.parametrize(
    "value,status",
    [(0.699, "FAILED"), (0.7, "WARNING"), (0.799, "WARNING"), (0.8, "PASSED")],
)
def test_q30_packaged_boundaries(config, value, status):
    result = handle_fastp_results(
        {"read_total_reads": 100, "read_q30_rate": value}, config
    )
    assert result["read_q30_status"] == status


@pytest.mark.parametrize(
    "value,status",
    [(19.9, "FAILED"), (20, "WARNING"), (29.9, "WARNING"), (30, "PASSED")],
)
def test_both_coverage_estimators(config, tmp_path, value, status):
    metrics = tmp_path / "metrics.csv"
    metrics.write_text(
        "Escherichia_coli,Genome_Size,900,1100\nEscherichia_coli,GC_Content,50,52\n"
    )
    config["metrics_file"] = str(metrics)
    result, _ = handle_species_coverage([("Escherichia coli", 100, value)], {}, config)
    result = handle_genome_size(
        ["Escherichia coli"],
        {"read_total_bases": value * 1000, "gc_content": 51},
        result,
        config,
    )
    assert result["coverage_status"] == status
    assert result["coverage_estimate_qualibact_status"] == status


@pytest.mark.parametrize(
    "contamination,status",
    [
        (9.9, "PASSED"),
        (10, "PASSED"),
        (10.1, "WARNING"),
        (20, "WARNING"),
        (20.1, "FAILED"),
    ],
)
def test_contamination_boundaries(config, contamination, status):
    result, _ = handle_species_coverage(
        [("Escherichia coli", 100 - contamination, 40)], {}, config
    )
    assert result["contamination_status"] == status


@pytest.mark.parametrize(
    "metric",
    [
        "read_length_status",
        "read_q30_status",
        "contamination_status",
        "gc_content_status",
        "coverage_status",
        "coverage_estimate_qualibact_status",
        "adapter_detection_status",
        "n_content_status",
    ],
)
def test_individual_warnings_propagate(metric):
    assert final_status_pass({metric: "WARNING"}) == "WARNING"


@pytest.mark.parametrize(
    "coverage",
    [
        ("FAILED", "FAILED", "FAILED"),
        ("FAILED", "PASSED", "WARNING"),
        ("WARNING", "PASSED", "WARNING"),
        ("WARNING", "WARNING", "WARNING"),
        ("PASSED", "PASSED", "PASSED"),
    ],
)
def test_coverage_rollup(coverage):
    first, second, expected = coverage
    values = {"coverage_status": first, "coverage_estimate_qualibact_status": second}
    assert final_status_pass(values) == expected
    values["read_q30_status"] = "FAILED"
    assert final_status_pass(values) == "FAILED"


@pytest.mark.parametrize(
    "thresholds",
    [
        {"read_length_warn_threshold": 100, "read_length_fail_threshold": 80},
        {"read_length_warn_threshold": 80, "read_length_fail_threshold": 100},
    ],
)
@pytest.mark.parametrize(
    "value,status", [(79, "FAILED"), (80, "WARNING"), (99, "WARNING"), (100, "PASSED")]
)
def test_read_length_new_and_legacy_threshold_order(thresholds, value, status):
    result = handle_fastp_results(
        {
            "read_total_reads": 100,
            "read1_mean_length": value,
            "read2_mean_length": value,
        },
        thresholds,
    )
    assert result["read_length_status"] == status


def test_outside_gc_clears_previous_pass(config, tmp_path):
    metrics = tmp_path / "metrics.csv"
    metrics.write_text(
        "Escherichia_coli,Genome_Size,900,1100\nEscherichia_coli,GC_Content,50,52\n"
    )
    config["metrics_file"] = str(metrics)
    result = handle_genome_size(
        ["Escherichia coli"],
        {"read_total_bases": 40000, "gc_content": 40},
        {"gc_content_status": "PASSED"},
        config,
    )
    assert result["gc_content_status"] == "FAILED"
