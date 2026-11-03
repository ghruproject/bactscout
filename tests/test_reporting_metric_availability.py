"""Missing fastp measurements must not become clean QC results."""

import copy
import json
from pathlib import Path

import pytest

from bactscout.thread import (
    get_fastp_results,
    handle_adapter_detection,
    handle_n_content_results,
)


@pytest.fixture
def report():
    path = (
        Path(__file__).parent / "sample_output_data/sample_001/sample_001_1.fastp.json"
    )
    return json.loads(path.read_text())


def parse_report(tmp_path, report):
    path = tmp_path / "fastp.json"
    path.write_text(json.dumps(report))
    return get_fastp_results({"status": "success", "json_report": str(path)})


def test_normal_report_does_not_invent_measurements(tmp_path, report):
    result = parse_report(tmp_path, report)
    assert (
        result["read_total_reads"]
        == report["summary"]["after_filtering"]["total_reads"]
    )
    assert result["read_q30_rate"] == report["summary"]["after_filtering"]["q30_rate"]
    assert result["n_content_rate"] is None
    result = handle_n_content_results(result, {})
    result = handle_adapter_detection(result, {})
    assert result["n_content_status"] == "WARNING"
    assert result["adapter_detection_status"] == "WARNING"
    assert "unavailable" in result["n_content_message"]
    assert "unavailable" in result["adapter_detection_message"]
    assert not any(key.startswith("_fastp") for key in result)
    assert "read1_before_filtering" not in result


@pytest.mark.parametrize(
    "filtering",
    [
        {"total_reads": 100, "too_many_N": 20},
        {"passed_filter_reads": 80, "too_many_N_reads": 20},
        {},
    ],
)
def test_rejected_read_counts_are_not_n_base_percentage(tmp_path, report, filtering):
    report["filtering_result"] = filtering
    report["read1_before_filtering"]["content_curves"]["N"] = [0.2, 0.0]
    assert parse_report(tmp_path, report)["n_content_rate"] is None


@pytest.mark.parametrize("flag", ["--overrepresentation_analysis", "-p"])
def test_enabled_analysis_can_report_assessed_empty_result(tmp_path, report, flag):
    report["command"] += " " + flag
    result = handle_adapter_detection(parse_report(tmp_path, report), {})
    assert result["adapter_detection_status"] == "PASSED"
    assert "does not establish adapter absence" in result["adapter_detection_message"]


@pytest.mark.parametrize("mate", ["read1_before_filtering", "read2_before_filtering"])
@pytest.mark.parametrize("count, expected", [(2, "WARNING"), (6, "FAILED")])
def test_nonempty_report_results_survive_parser(
    tmp_path, report, mate, count, expected
):
    report[mate]["overrepresented_sequences"] = {
        "A" * (i + 1): 100 for i in range(count)
    }
    result = handle_adapter_detection(parse_report(tmp_path, report), {})
    assert result["adapter_detection_status"] == expected
    assert (
        f"{count} overrepresented sequence entries"
        in result["adapter_detection_message"]
    )
    assert "nonspecific" in result["adapter_detection_message"]


def test_missing_measurements_and_zero_reads():
    for value in (
        {"read_total_reads": 100},
        {"read_total_reads": 100, "n_content_rate": None},
    ):
        assert (
            handle_n_content_results(copy.copy(value), {})["n_content_status"]
            == "WARNING"
        )
        assert (
            handle_adapter_detection(copy.copy(value), {})["adapter_detection_status"]
            == "WARNING"
        )
    for handler, key in (
        (handle_n_content_results, "n_content_status"),
        (handle_adapter_detection, "adapter_detection_status"),
    ):
        assert handler({"read_total_reads": 0}, {})[key] == "FAILED"


@pytest.mark.parametrize(
    "rate, expected", [(0.0, "PASSED"), (0.05, "PASSED"), (0.2, "WARNING")]
)
def test_explicit_measured_n_content_retains_percentage_api(rate, expected):
    result = handle_n_content_results(
        {"read_total_reads": 100, "n_content_rate": rate}, {}
    )
    assert result["n_content_status"] == expected
    assert result["n_content_rate"] == rate


def test_enabled_but_incomplete_paired_report_is_unavailable(tmp_path, report):
    report["command"] += " --overrepresentation_analysis"
    report.pop("read2_before_filtering")
    result = handle_adapter_detection(parse_report(tmp_path, report), {})
    assert result["adapter_detection_status"] == "WARNING"
