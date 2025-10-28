# QC Command

The `qc` command performs comprehensive quality control analysis on a batch of bacterial genome samples.

## Overview

The QC command processes all FASTQ pairs in a directory, running:
- **Quality assessment** (via fastp)
- **Taxonomic profiling** (via Sylph)
- **Contamination detection** (via Sylph)
- **MLST typing** (via ARIBA)
- **Quality metrics reporting** (CSV output)

## Basic Usage

```bash
# Analyze all samples in a directory
pixi run bactscout qc /path/to/samples/

# Specify custom output directory
pixi run bactscout qc /path/to/samples/ -o /output/directory/

# Use custom configuration
pixi run bactscout qc /path/to/samples/ -c custom_config.yml
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_dir` | ✅ Yes | Directory containing FASTQ files (R1/R2 pairs) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `bactscout_output` | Output directory for results |
| `--threads` | `-t` | 2 | Number of CPU threads to use |
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
    - Use 2-4 threads per sample
    - More threads = faster analysis but higher memory usage
    - Total = (number of samples) × (threads per sample)

### Skip Preflight Checks

For trusted data, skip validation:

```bash
pixi run bactscout qc data/ --skip-preflight
```

### Different Output Directory

```bash
pixi run bactscout qc data/ -o /results/batch_2024-01/
```

### Custom Configuration

```bash
pixi run bactscout qc data/ -c strict_qc_config.yml
```

## Processing Steps

For each sample, BactScout:

1. **Preflight Checks** - Validates FASTQ format
2. **Quality Assessment** - fastp for read QC metrics
3. **Taxonomic Identification** - Sylph for species ID
4. **Contamination Screening** - Sylph contamination detection
5. **MLST Typing** - ARIBA for strain typing
6. **Result Aggregation** - Generates per-sample and batch CSVs

## Performance

Typical processing time per sample (on 2-thread system):
- Small samples (< 100k reads): ~2-5 minutes
- Medium samples (100k-1M reads): ~5-15 minutes
- Large samples (> 1M reads): ~15-30+ minutes

To significantly speed up analysis:
- Increase `--threads`
- Pre-filter low-quality reads with fastp
- Use SSD storage for input/output

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | ✅ Success |
| 1 | ❌ General error |
| 2 | ❌ Invalid arguments |
| 127 | ❌ Missing dependencies |

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

Databases auto-download on first run. If issues:
```bash
pixi run bactscout qc data/ --skip-preflight
```

See [Troubleshooting Guide](../guide/troubleshooting.md) for more help.
