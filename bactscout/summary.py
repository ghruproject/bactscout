import csv
import os
from pathlib import Path

from bactscout.util import print_message


def summary_dir(data_dir, output_file):
    """
    Read the data/output dir, each folder inside is a sample, each folder has a summary.csv file.
    Merge these into a single summary.csv file.

    Args:
        data_dir (str): Path to directory containing sample subdirectories
        output_file (str): Path to output merged CSV file
    """

    # Convert to Path objects for easier manipulation
    data_path = Path(data_dir)
    output_path = Path(output_file)
    if os.getenv("NXF_TASK_WORKDIR"):
        output_path = Path(
            os.getenv("NXF_TASK_WORKDIR", ""), os.path.basename(output_file)
        )
        print_message(f"Using Nextflow path for output: {output_path}", "info")
        data_path = Path(os.getenv("NXF_TASK_WORKDIR", ""), os.path.basename(data_dir))
        print_message(f"Using Nextflow path for input: {data_path}", "info")
    # Find all CSV files that match the pattern *_summary.csv
    summary_files = []

    # Look for summary CSV files in each subdirectory
    for sample_dir in data_path.iterdir():
        if sample_dir.is_dir():
            # Look for CSV files in this sample directory
            for csv_file in sample_dir.glob("*_summary.csv"):
                summary_files.append(csv_file)
    # OR there could be summary files directly in data_dir (don't include final_summary.csv)
    for csv_file in data_path.glob("*_summary.csv"):
        if csv_file.name != "final_summary.csv":
            summary_files.append(csv_file)

    if not summary_files:
        print_message(f"No summary CSV files found in {data_dir}", "error")
        return

    print_message(f"Found {len(summary_files)} summary files to merge", "info")

    # Read the first file to get the header
    header = None
    all_rows = []

    for csv_file in sorted(summary_files):
        try:
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

                if not rows:
                    print(f"Warning: Empty file {csv_file}")
                    continue

                # Use the first file's header as the master header
                if header is None:
                    header = rows[0]
                    print(f"Using header from {csv_file}")

                # Add data rows (skip header)
                if len(rows) > 1:
                    all_rows.extend(rows[1:])
                else:
                    print(f"Warning: No data rows in {csv_file}")

        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading {csv_file}: {e}")
            continue

    # Write the merged file
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            if header:
                writer.writerow(header)

            # Write all data rows
            writer.writerows(all_rows)

        print(f"Successfully merged {len(all_rows)} rows into {output_file}")
        print(f"Total samples processed: {len(all_rows)}")

    except OSError as e:
        print(f"Error writing merged file {output_file}: {e}")
        raise
