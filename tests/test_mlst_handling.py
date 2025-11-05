import pytest

from bactscout.thread import blank_sample_results, handle_mlst_results


@pytest.mark.parametrize(
    "mock_result",
    [
        {"stringmlst_results": {"error": "runtime error"}},
        {"stringmlst_results": {"ST": "5"}},
        {"stringmlst_results": {"ST": "0"}},
        {"stringmlst_results": {"ST": "-1"}},
        {"stringmlst_results": {"ST": ""}},
        {"stringmlst_results": {"ST": "N/A"}},
        {"stringmlst_results": {}},
    ],
)
def test_handle_mlst_results_various_outputs(monkeypatch, mock_result):
    """Ensure handle_mlst_results yields either PASSED or WARNING for MLST status.

    This test patches the underlying `run_mlst` function used by `handle_mlst_results`
    to return a variety of realistic outputs from stringMLST and asserts that the
    resulting `mlst_status` is either "PASSED" or "WARNING" as required by the
    QC logic.
    """
    # Prepare inputs
    final_results = blank_sample_results("sample1")
    config = {
        "mlst_species": {"escherichia_coli": "Escherichia coli"},
        "bactscout_dbs_path": "/nonexistent/path",
    }

    # Patch run_mlst in the module where handle_mlst_results looks it up
    monkeypatch.setattr("bactscout.thread.run_mlst", lambda *a, **k: mock_result)

    # Call with a species that exists in the mapping so run_mlst is invoked
    out = handle_mlst_results(
        final_results=final_results,
        config=config,
        species="Escherichia coli",
        read1_file="/dev/null",
        read2_file="/dev/null",
        sample_output_dir="/tmp",
        message=False,
    )

    assert out["mlst_status"] in {"PASSED", "WARNING"}


def test_handle_mlst_results_no_database():
    """If no MLST database is found for the species, mlst_status should be WARNING."""
    final_results = blank_sample_results("sample2")
    config = {
        "mlst_species": {"escherichia_coli": "Escherichia coli"},
        "bactscout_dbs_path": "/nonexistent/path",
    }

    # Do not patch run_mlst; it should not be called because species won't match
    out = handle_mlst_results(
        final_results=final_results,
        config=config,
        species="Some Unknown Bacterium",
        read1_file="/dev/null",
        read2_file="/dev/null",
        sample_output_dir="/tmp",
        message=False,
    )

    assert out["mlst_status"] == "WARNING"


def test_handle_mlst_results_top_level_error(monkeypatch):
    """If run_mlst returns a top-level error key, function should return early with WARNING."""
    final_results = blank_sample_results("sample3")
    config = {
        "mlst_species": {"escherichia_coli": "Escherichia coli"},
        "bactscout_dbs_path": "/nonexistent/path",
    }

    # Patch run_mlst to return a top-level error (not inside stringmlst_results)
    monkeypatch.setattr("bactscout.thread.run_mlst", lambda *a, **k: {"error": "boom"})

    out = handle_mlst_results(
        final_results=final_results,
        config=config,
        species="Escherichia coli",
        read1_file="/dev/null",
        read2_file="/dev/null",
        sample_output_dir="/tmp",
        message=False,
    )

    assert out["mlst_status"] == "WARNING"
    assert out["mlst_message"] == "MLST analysis failed: boom"
