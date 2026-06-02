"""Long-read summary aggregation."""

import csv
from pathlib import Path

from bactscout.util import print_message


def summary_dir_long(data_dir, output_file):
    """Merge long-read per-sample CSV files into a final summary."""
    data_path = Path(data_dir)
    output_path = Path(output_file)
    summary_files = []

    for sample_dir in data_path.iterdir():
        if sample_dir.is_dir():
            summary_files.extend(sample_dir.glob("*_long_summary.csv"))

    summary_files.extend(
        csv_file
        for csv_file in data_path.glob("*_long_summary.csv")
        if csv_file.name != "final_summary_long.csv"
    )

    if not summary_files:
        print_message(f"No long-read summary CSV files found in {data_dir}", "error")
        return

    header = None
    all_rows = []
    for csv_file in sorted(summary_files):
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            continue
        if header is None:
            header = rows[0]
        all_rows.extend(rows[1:])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header:
            writer.writerow(header)
        writer.writerows(all_rows)

    print_message(f"Merged {len(all_rows)} long-read samples into {output_file}", "success")
