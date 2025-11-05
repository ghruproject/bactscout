# Summary Command

The `summary` command generates a consolidated quality control report from multiple samples analyzed with the `collect` command. `qc` does this step for you. If you want to run bactscout at scale on HPC or cloud, consider using the [Scaling up Guide](../guide/scaling.md)

## Overview

After processing multiple samples individually or in batches, the `summary` command:

- Reads individual sample result CSVs
- Merges them into a single `final_summary.csv`
- Provides a unified view of all samples
- Enables easy comparison and filtering

## Basic Usage

```bash
# Generate summary from QC output directory
pixi run bactscout summary bactscout_output/

# Specify custom output location
pixi run bactscout summary bactscout_output/ -o final_results/

# Use different configuration
pixi run bactscout summary bactscout_output/ -c config.yml
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_dir` | ✅ Yes | Directory containing sample subdirectories (output from `collect`) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `bactscout_output` | Location to write `final_summary.csv` |
| `--config` | `-c` | `bactscout_config.yml` | Configuration file path |

## Input Format

The `summary` command expects the standard output directory structure from `collect`:

```
bactscout_output/
├── Sample_001/
│   ├── sample_results.csv          # Per-sample results
│   ├── fastp_report.json
│   ├── sylph_matches.csv
│   └── [other files]
├── Sample_002/
│   ├── sample_results.csv
│   └── ...
├── Sample_003/
│   ├── sample_results.csv
│   └── ...
└── final_summary.csv               # Output file (created by summary command)
```

## Output

### `final_summary.csv`

A consolidated CSV file with one row per sample, containing:

- `sample_id` — Sample identifier
- `a_final_status` — Overall QC status (PASSED / WARNING / FAILED)
- `species` — Detected species name(s) (top species or semicolon-separated list)
- `species_coverage` — Sylph-derived coverage values for reported species
- `contamination_status` — Contamination QC status (PASSED/WARNING/FAILED)
- `coverage_status` — Coverage QC status (PASSED/WARNING/FAILED)
- `mlst_status` — MLST QC status (PASSED/WARNING)
- `read_q30_rate` — Fraction (0-1) of bases with Q≥30
- `duplication_rate` — Read duplication rate (0-1)
- `gc_content` — GC content percentage

See [Output Format](./output-format.md) for detailed column descriptions.

## Usage Scenarios

### Workflow: Individual Processing + Summary

Process all samples, then generate report:

```bash
# 1. Run QC on all samples
pixi run bactscout collect samples/ -o batch_results/ -t 4

# 2. Generate summary
pixi run bactscout summary batch_results/ -o batch_results/
```

Result: `batch_results/final_summary.csv` with all results


## Troubleshooting

### "No results found"

Ensure:
- Directory contains sample subdirectories
- Each subdirectory has `sample_results.csv`
- Path is correct and accessible

### "File permission denied"

Check permissions:
```bash
ls -l bactscout_output/
```

### Empty Summary

Verify sample directories exist and contain results:
```bash
find bactscout_output/ -name "sample_results.csv"
```

See [Troubleshooting Guide](../guide/troubleshooting.md) for more help.
