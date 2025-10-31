import pytest

from bactscout.thread import (
    handle_adapter_detection,
    handle_duplication_results,
    handle_fastp_results,
    handle_n_content_results,
)


def test_handle_fastp_results_q30_and_length_thresholds():
    # Zero reads => FAILED statuses
    fr = {"read_total_reads": 0}
    res = handle_fastp_results(fr.copy(), {})
    assert res["read_q30_status"] == "FAILED"
    assert res["read_length_status"] == "FAILED"

    # Q30 as decimal above fail threshold -> PASSED
    fr = {
        "read_total_reads": 1000,
        "read_q30_rate": 0.8,
        "read1_mean_length": 150,
        "read2_mean_length": 150,
    }
    res = handle_fastp_results(fr.copy(), {})
    assert res["read_q30_status"] == "PASSED"
    assert res["read_length_status"] == "PASSED"

    # Q30 given as percentage thresholds (legacy >1 values) should be handled
    cfg = {"q30_fail_threshold": 60, "q30_warn_threshold": 70}
    fr = {"read_total_reads": 100, "read_q30_rate": 0.65}
    res = handle_fastp_results(fr.copy(), cfg)
    # Note: implementation marks PASSED when >= fail threshold (after conversion)
    assert res["read_q30_status"] == "PASSED"

    # Read lengths borderline: warn vs fail
    cfg = {"read_length_fail_threshold": 150, "read_length_warn_threshold": 120}
    fr = {"read_total_reads": 100, "read1_mean_length": 130, "read2_mean_length": 130}
    res = handle_fastp_results(fr.copy(), cfg)
    # with both at 130, which is >= warn(120) but < fail(150) => WARNING
    assert res["read_length_status"] == "WARNING"


@pytest.mark.parametrize(
    "dup_rate, total_reads, expected",
    [
        (0.05, 100, "PASSED"),
        (0.25, 100, "WARNING"),
        (0.5, 100, "FAILED"),
        (0.0, 0, "FAILED"),
    ],
)
def test_handle_duplication_results(dup_rate, total_reads, expected):
    fr = {"duplication_rate": dup_rate, "read_total_reads": total_reads}
    res = handle_duplication_results(fr.copy(), {})
    assert res["duplication_status"] == expected


@pytest.mark.parametrize(
    "n_rate, total_reads, expected",
    [
        (0.05, 100, "PASSED"),  # 0.05% <= 0.1% threshold => PASSED
        (0.2, 100, "WARNING"),  # 0.2% > 0.1% => WARNING
        (0.0, 0, "FAILED"),
    ],
)
def test_handle_n_content_results(n_rate, total_reads, expected):
    fr = {"n_content_rate": n_rate, "read_total_reads": total_reads}
    res = handle_n_content_results(fr.copy(), {})
    assert res["n_content_status"] == expected


def test_handle_adapter_detection():
    # No reads -> FAILED
    fr = {"read_total_reads": 0}
    res = handle_adapter_detection(fr.copy(), {})
    assert res["adapter_detection_status"] == "FAILED"

    # No overrep sequences -> PASSED
    fr = {
        "read_total_reads": 100,
        "read1_before_filtering": {"overrepresented_sequences": []},
    }
    res = handle_adapter_detection(fr.copy(), {})
    assert res["adapter_detection_status"] == "PASSED"

    # Few overrep sequences -> WARNING (<= threshold)
    fr = {
        "read_total_reads": 100,
        "read1_before_filtering": {"overrepresented_sequences": ["a", "b"]},
    }
    res = handle_adapter_detection(fr.copy(), {"adapter_overrep_threshold": 5})
    assert res["adapter_detection_status"] == "WARNING"

    # Many overrep -> FAILED
    fr = {
        "read_total_reads": 100,
        "read1_before_filtering": {"overrepresented_sequences": list(range(10))},
    }
    res = handle_adapter_detection(fr.copy(), {"adapter_overrep_threshold": 5})
    assert res["adapter_detection_status"] == "FAILED"
