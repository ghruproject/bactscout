import csv

from bactscout.thread import blank_sample_results, write_summary_file


def test_summary_round_trips_diagnostic_text_and_missing_measurements(tmp_path):
    results = blank_sample_results('sample,"one"')
    message = 'Species A, Species B; "check this"\nSecond diagnostic line'
    results["species_message"] = message
    results["n_content_rate"] = None
    results["duplication_rate"] = 0.0

    write_summary_file(results, results["sample_id"], str(tmp_path))

    with (tmp_path / 'sample,"one"_summary.csv').open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert None not in rows[0]
    assert rows[0]["sample_id"] == results["sample_id"]
    assert rows[0]["species_message"] == message
    assert rows[0]["n_content_rate"] == ""
    assert rows[0]["duplication_rate"] == "0.0"
