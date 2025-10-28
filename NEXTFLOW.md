# BactScout Nextflow Workflow

A production-ready Nextflow workflow for processing paired-end bacterial genomic samples through BactScout on HPC systems or local machines.

## Overview

This workflow:
1. **Discovers** paired-end FASTQ files (supports `_R1/_R2` or `_1/_2` naming conventions)
2. **Processes** each sample independently with BactScout collect (fully parallelizable)
3. **Aggregates** results into a single comprehensive summary CSV

## Prerequisites

- **Nextflow** (v20.0+): [Installation guide](https://www.nextflow.io/docs/latest/getstarted.html)
- **BactScout**: Installed and available in PATH
- **Python 3.9+**
- **Paired-end FASTQ files**: Properly named with `_R1/_R2` or `_1/_2` suffixes (gzipped or uncompressed)

## Quick Start

### Basic Usage

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --output_dir ./results
```

### With Custom Configuration

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --output_dir ./results \
  --config /path/to/bactscout_config.yml \
  --threads 8 \
  --kat_enabled true \
  --k_mer_size 25
```

### Display Help

```bash
nextflow run nextflow.nf --help
```

## Parameters

### Required

| Parameter | Description |
|-----------|-------------|
| `--input_dir` | Directory containing paired-end FASTQ files |

### Optional

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--output_dir` | `./bactscout_output` | Output directory for results |
| `--config` | `./bactscout_config.yml` | Path to BactScout config file |
| `--threads` | `4` | Number of threads per sample |
| `--kat_enabled` | `null` | Override KAT setting (true/false, null uses config) |
| `--k_mer_size` | `null` | Override K-mer size (null uses config) |
| `--skip_preflight` | `false` | Skip preflight checks (not recommended) |
| `--help` | `false` | Display help message |

## File Organization

### Input Structure

```
reads/
├── Sample_001_R1.fastq.gz
├── Sample_001_R2.fastq.gz
├── Sample_002_R1.fastq.gz
├── Sample_002_R2.fastq.gz
└── ...
```

Or with alternative naming:

```
reads/
├── Sample_001_1.fastq.gz
├── Sample_001_2.fastq.gz
├── Sample_002_1.fastq.gz
├── Sample_002_2.fastq.gz
└── ...
```

### Output Structure

```
results/
├── Sample_001/
│   ├── Sample_001_summary.csv
│   ├── Sample_001_qc_report.html
│   └── [other sample outputs]
├── Sample_002/
│   ├── Sample_002_summary.csv
│   ├── Sample_002_qc_report.html
│   └── [other sample outputs]
└── final_summary.csv    # Aggregated results
```

## Workflow Steps

### 1. Input Discovery
The workflow scans the input directory for paired-end FASTQ files matching:
- `*_R1.fastq.gz` paired with `*_R2.fastq.gz`
- `*_1.fastq.gz` paired with `*_2.fastq.gz`

Each pair is logged at startup.

### 2. Sample Processing
Each sample is processed independently through:
- **BactScout Collect**: Quality control, taxonomic profiling, MLST analysis
- **Per-sample Results**: Individual summary and optional QC report
- **Parallel Execution**: All samples processed concurrently (configurable)

### 3. Result Aggregation
All individual sample summaries are merged into a single `final_summary.csv` containing:
- Per-sample metrics
- QC status for each sample
- Aggregated statistics

## Running on HPC

### SLURM

```bash
#!/bin/bash
#SBATCH --job-name=bactscout
#SBATCH --cpus-per-task=32
#SBATCH --mem=128G
#SBATCH --time=24:00:00

module load java/11        # or appropriate version
module load nextflow

nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --output_dir ./results \
  --threads 8 \
  -profile cluster
```

### With Conda/Mamba

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --output_dir ./results \
  -profile conda
```

### With Singularity

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --output_dir ./results \
  -profile singularity
```

## Common Scenarios

### Enable KAT for all samples

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --kat_enabled true \
  --k_mer_size 25
```

### Process many samples with distributed resources

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --threads 16 \
  -profile cluster \
  -with-trace execution_trace.txt \
  -with-report execution_report.html
```

### Use custom configuration file

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --config /path/to/custom/config.yml \
  --skip_preflight
```

## Monitoring Progress

### Real-time Monitoring

```bash
# In another terminal, monitor the work directory
watch ls -lh work/
```

### Execution Reports

Generate automatic reports:

```bash
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  -with-trace trace.txt \
  -with-timeline timeline.html \
  -with-report report.html
```

Then view the HTML reports in a browser.

### Resuming Failed Runs

```bash
# Continue from the last successful task
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  -resume
```

## Performance Tuning

### Adjust Parallelization

```bash
# Process 4 samples in parallel (default)
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  -qs 4
```

### Resource Allocation

```bash
# Increase memory and threads per sample
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --threads 16 \
  -with-docker ubuntu:latest
```

## Troubleshooting

### No samples found

**Problem**: "No samples found in input directory"

**Solution**: 
- Verify file names match `_R1/_R2` or `_1/_2` pattern
- Ensure files are gzipped (`.fastq.gz`)
- Check that the input directory path is correct

### BactScout command not found

**Problem**: "BactScout not found in PATH"

**Solution**:
```bash
# Verify BactScout installation
which bactscout

# Or use full path in nextflow config
```

### Out of memory

**Problem**: Jobs killed due to memory limits

**Solution**:
```bash
# Reduce threads per sample or increase memory allocation
nextflow run nextflow.nf \
  --input_dir /path/to/reads \
  --threads 4
```

## Output Files

### Per-Sample Outputs

Each sample directory contains:
- `{sample_name}_summary.csv` - QC and analysis results
- `{sample_name}_qc_report.html` - Interactive QC report (if enabled)
- Additional analysis files (MLST, taxonomic assignments, etc.)

### Final Summary

`final_summary.csv` contains:
- All per-sample metrics in a single table
- Convenient for downstream analysis or reporting
- Compatible with standard data analysis tools

## Configuration

Use a custom BactScout configuration file to control:
- Quality thresholds
- Taxonomic databases
- MLST settings
- KAT analysis parameters
- Resource usage

See `bactscout_config.yml` for available options.

## Support

For issues or questions:
1. Check BactScout documentation: [GitHub](https://github.com/ghruproject/bactscout)
2. Consult Nextflow documentation: [Official Docs](https://www.nextflow.io/docs/latest/)
3. Review workflow logs in `.nextflow.log`

## License

Same as BactScout (see main repository)
