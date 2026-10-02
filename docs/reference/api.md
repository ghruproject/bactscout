# API reference

BactScout's documented interface is its command-line application, installed as the `bactscout` console command. The project does not currently promise a stable Python library API; modules under `bactscout.*` implement the CLI and may change between releases.

## Command-line interface

Use `--help` for the options available in the installed version:

```bash
pixi run bactscout --help
pixi run bactscout qc --help
pixi run bactscout long --help
```

The principal commands are:

| Command | Purpose |
|---|---|
| `bactscout qc INPUT_DIR` | Run short-read QC over paired FASTQs in a directory |
| `bactscout collect READ1 READ2` | Run short-read QC for one pair |
| `bactscout summary INPUT_DIR` | Combine existing per-sample short-read CSV summaries |
| `bactscout long qc INPUT_DIR --platform PLATFORM` | Run long-read QC over FASTQs in a directory |
| `bactscout long collect FASTQ --platform PLATFORM` | Run long-read QC on one FASTQ |
| `bactscout long summary INPUT_DIR` | Combine existing per-sample long-read CSV summaries |
| `bactscout preflight` | Check prerequisites and set up configured short-read databases |
| `bactscout long preflight` | Check prerequisites and set up the long-read database |

For input naming, database prerequisites, and a reproducible reviewer workflow, see the [reviewer guide](../reviewer-guide.md). For thresholds and configuration keys, see the [configuration reference](configuration.md).

## Summary CSV fields

Short-read QC writes one per-sample summary and a batch-level `final_summary.csv`. The `a_final_status` column contains `PASSED`, `WARNING`, or `FAILED`. Component results are exposed in fields such as `read_q30_status`, `read_length_status`, `coverage_status`, `coverage_estimate_qualibact_status`, `contamination_status`, and `mlst_status`.

Coverage estimates are represented by `coverage_estimate_sylph` and `coverage_estimate_qualibact`; the latter is calculated from read bases and the expected genome size where available. Long-read per-sample summaries and `final_summary_long.csv` use a separate schema with `status`, `flag_quality`, `flag_n50`, `flag_coverage`, and `flag_contam` fields. The [output-format reference](../usage/output-format.md) documents the columns in both schemas.

The `summary` commands combine the per-sample CSV files already present in the input directory. They do not rerun QC or apply a different configuration to existing results.

## Reading a summary from Python

The summary CSV is the stable way to consume results from Python or another analysis tool. This example uses only the Python standard library:

```python
import csv

with open("results/final_summary.csv", newline="", encoding="utf-8") as handle:
    rows = csv.DictReader(handle)
    failed_samples = [
        row["sample_id"]
        for row in rows
        if row["a_final_status"] == "FAILED"
    ]

print(f"Failed samples: {len(failed_samples)}")
```
