# Collect Command

The `collect` command processes a single bacterial genome sample (one pair of FASTQ files).

## Overview

Perfect for:

- Processing individual samples received at different times
- Integration with other pipelines
- Testing and validation
- Low-throughput studies

Uses the same QC pipeline as the `qc` command but operates on a single sample. Results are stored in a sample-specific directory, ready for aggregation with the `summary` command. If you want to run bactscout at scale on HPC or cloud, consider using the [Scaling up Guide](../guide/scaling.md)

## Basic Usage

```bash
# Process single sample
pixi run bactscout collect sample_R1.fastq.gz sample_R2.fastq.gz

# Specify output directory
pixi run bactscout collect sample_R1.fastq.gz sample_R2.fastq.gz -o /output/path/

# Use custom configuration
pixi run bactscout collect sample_R1.fastq.gz sample_R2.fastq.gz -c config.yml
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `read1_file` | ✅ Yes | Path to R1 (forward) FASTQ file |
| `read2_file` | ✅ Yes | Path to R2 (reverse) FASTQ file |

!!! note "Argument Order"
    R1 must be first, R2 must be second. Order matters!

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `bactscout_output` | Output directory for results. Results csv will be in `bactscout_output/<sample_name>/` |
| `--threads` | `-t` | 4 | Number of CPU threads to use |
| `--config` | `-c` | `bactscout_config.yml` | Configuration file path |
| `--skip-preflight` | - | True | Skip validation checks (default for `collect`)
| `--report-resources` | - | False | Track and report thread and memory usage for the sample |
| `--write-json` | - | False | Write results to JSON file as well |

## Input Format

### File Requirements

- **R1 (forward)**: Forward read file, typically ending in `_R1` or `_1`
- **R2 (reverse)**: Reverse read file, typically ending in `_R2` or `_2`
- **Compression**: Can be gzipped (`.fastq.gz`) or uncompressed (`.fastq`)

### Sample Name Detection

BactScout automatically extracts the sample name from the R1 filename:

```
Input:  sample_ABC123_R1.fastq.gz
        ↓
Output: Sample_ABC123/
        
Input:  2024-01_isolate_1.fq.gz
        ↓
Output: Sample_2024-01_isolate_1/
```

The following suffixes are removed:
- `_R1`, `_R2`, `_1`, `_2`
- `.fastq`, `.fq`
- `.gz`

## Output Structure

Results are organized in a sample-specific directory:

```
bactscout_output/
└── Sample_ABC123/
    ├── Sample_ABC123_fastp.json    # fastp QC data (JSON)
    ├── sylph_report.txt           # Taxonomic profiles
    ├── mlst.tsv                    # MLST typing
    ├── Sample_ABC123_summary.csv   # Per-sample summary CSV (`{sample_id}_summary.csv`)
    └── [other intermediate files]
```

## Output Table - `{sample_id}_summary.csv`

Most important columns (these are the actual CSV keys produced by BactScout):

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

See [Output Format](./output-format.md) for the full, canonical field list and descriptions.

## Troubleshooting

### "File not found"

Verify file paths:
```bash
ls -lh sample_R1.fastq.gz sample_R2.fastq.gz
```

### "Files are in wrong order"

Ensure R1 is first, R2 is second:
```bash
# ✅ Correct
pixi run bactscout collect sample_R1.gz sample_R2.gz

# ❌ Wrong
pixi run bactscout collect sample_R2.gz sample_R1.gz
```

### "Sample name not detected correctly"

Check the R1 filename. It should contain a sample identifier before `_R1`:
```
Good names:  isolate_001_R1.fastq.gz
             ecoli_batch2_R1.fastq.gz
             2024-01-sample_R1.fq.gz

Bad names:   R1.fastq.gz           (no sample identifier)
             _R1.fastq.gz          (no identifier)
```

See [Troubleshooting Guide](../guide/troubleshooting.md) for more help.
