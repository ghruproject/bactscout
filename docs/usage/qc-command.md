# QC Command

The `qc` command performs comprehensive quality control analysis on a batch of bacterial genome samples.
**Try this command first.** When you want to run QC on multiple samples in one go, this is the command to use.

If you want to run bactscout at scale on HPC or cloud, consider using the [Scaling up Guide](../guide/scaling.md), where you will separate the process by sample using the `collect` command ([link](collect-command.md)) and then aggregate results with the `summary` command ([link](summary-command.md)).


## Overview

The QC command processes all FASTQ pairs in a directory, running:

- **Quality assessment** (via fastp)
- **Taxonomic profiling** (via Sylph)
- **Contamination detection** (via Sylph)
- **MLST typing** (via StringMLST)
- **Quality metrics reporting** (CSV output)
- **Applying Qualibact criteria** for PASS/FAIL determination

## Basic Usage

```bash
# Analyze all samples in a directory
pixi run bactscout qc /path/to/samples/

# Specify custom output directory
pixi run bactscout qc /path/to/samples/ -o /output/directory/

# Use custom configuration
pixi run bactscout qc /path/to/samples/ -c custom_config.yml

# Skip preflight checks
pixi run bactscout qc data/ --skip-preflight

# Specify number of threads
pixi run bactscout qc /path/to/samples/ -t 8
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_dir` | ✅ Yes | Directory containing FASTQ files (R1/R2 pairs) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `bactscout_output` | Output directory for results |
| `--threads` | `-t` | 4 | Number of CPU threads to use |
| `--config` | `-c` | `bactscout_config.yml` | Configuration file path |
| `--skip-preflight` | - | False | Skip validation checks |
| `--report-resources` | - | False | Track and report thread and memory usage per sample |

## Input Format

Input directory should contain FASTQ files named with paired-end suffixes:

```
samples/
├── sample_001_R1.fastq.gz
├── sample_001_R2.fastq.gz
├── sample_002_R1.fastq.gz
├── sample_002_R2.fastq.gz
└── ...
```

Supported naming patterns:

- `*_R1.fastq.gz` / `*_R2.fastq.gz`
- `*_1.fastq.gz` / `*_2.fastq.gz`
- `*_R1.fq.gz` / `*_R2.fq.gz`

## Output Structure

`final_summary.csv` is the main output file, consolidating results across all samples.

```
bactscout_output/
├── final_summary.csv              # Consolidated results
├── Sample_001/
│   ├── fastp_report.html
│   ├── fastp_report.json
│   ├── reads_QC.json
│   ├── sylph_matches.tsv
│   ├── stringmlst_results.json
│   └── [other analysis files]
├── Sample_002/
│   └── ...
└── ...
```

## Output Columns

See [Output Format](../usage/output-format.md) for detailed descriptions of all CSV columns.

## Advanced Usage

### Parallel Processing

Use multiple threads to speed up analysis:

```bash
pixi run bactscout qc data/ -t 8  # Use 8 threads
```

!!! note "Thread Recommendation"
    - Each thread will be used for processing one sample. i.e. 4 threads = 4 samples processed in parallel.
    - More threads = faster analysis but higher memory usage

## Troubleshooting

### "No FASTQ files found"

Ensure:
- Directory path is correct
- Files have proper naming convention (_R1, _R2, _1, _2)
- Files are uncompressed or `.gz` compressed

### "Out of memory"

Reduce thread count:
```bash
pixi run bactscout qc data/ -t 2
```

### "Database not found"

Databases auto-download on first run. If there are issues (and the databases are indeed available), retry with:
```bash
pixi run bactscout qc data/ --skip-preflight
```

See [Troubleshooting Guide](../guide/troubleshooting.md) for more help.
