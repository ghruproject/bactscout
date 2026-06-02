import csv

from bactscout.long.summary import summary_dir_long


def test_summary_dir_long_merges_only_long_summaries(tmp_path):
    sample_a = tmp_path / "sample_a"
    sample_b = tmp_path / "sample_b"
    sample_a.mkdir()
    sample_b.mkdir()

    header = ["sample_id", "status"]
    for sample_dir, sample_id in ((sample_a, "sample_a"), (sample_b, "sample_b")):
        with open(sample_dir / f"{sample_id}_long_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow([sample_id, "PASSED"])
        with open(sample_dir / f"{sample_id}_summary.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerow([sample_id, "FAILED"])

    output_file = tmp_path / "final_summary_long.csv"
    summary_dir_long(str(tmp_path), str(output_file))

    with open(output_file, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert all(row["status"] == "PASSED" for row in rows)