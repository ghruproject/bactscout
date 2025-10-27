# Collect Command

The `collect` command processes a single bacterial genome sample (one pair of FASTQ files).

## Overview

Perfect for:
- Processing individual samples received at different times
- Integration with other pipelines
- Testing and validation
- Low-throughput studies

Uses the same QC pipeline as the `qc` command but operates on a single sample.

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
| `--output` | `-o` | `bactscout_output` | Output directory for results |
| `--threads` | `-t` | 2 | Number of CPU threads to use |
| `--config` | `-c` | `bactscout_config.yml` | Configuration file path |
| `--skip-preflight` | - | False | Skip validation checks |

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
    ├── fastp_report.html           # Interactive QC report
    ├── fastp_report.json           # QC data (JSON)
    ├── reads_QC.json               # Quality metrics summary
    ├── sylph_matches.tsv           # Taxonomic profiles
    ├── sylph_matches.csv           # CSV version
    ├── stringmlst_results.json     # MLST typing
    ├── stringmlst_report.txt       # MLST summary
    ├── sample_results.csv          # Per-sample metrics (key output)
    └── [other intermediate files]
```

## Key Output Files

### `sample_results.csv`

Per-sample analysis results with columns:
- `sample_id` - Sample identifier
- `species` - Identified species
- `coverage` - Mean coverage depth
- `quality_pass` - Pass/Fail based on thresholds
- `contamination_pct` - % contamination from other species
- `mlst_type` - MLST typing result
- And more (see [Output Format](./output-format.md))

### `fastp_report.html`

Interactive HTML report showing:
- Per-base quality scores
- Per-read quality distribution
- Adapter trimming results
- Read length distribution
- GC content analysis

Open in a web browser for detailed visualization.

## Usage Examples

### Single Local Sample

```bash
pixi run bactscout collect \
  ./data/isolate_123_R1.fastq.gz \
  ./data/isolate_123_R2.fastq.gz
```

Output: `bactscout_output/Sample_isolate_123/`

### Batch Processing Individual Samples

Process multiple samples sequentially:

```bash
for sample in sample_*_R1.fastq.gz; do
  r2="${sample/_R1/_R2}"
  pixi run bactscout collect "$sample" "$r2"
done
```

### High-Performance Processing

Use more threads:

```bash
pixi run bactscout collect data/sample_R1.gz data/sample_R2.gz -t 8
```

### Custom Output Location

```bash
pixi run bactscout collect \
  input/sample_R1.fastq.gz \
  input/sample_R2.fastq.gz \
  -o /analysis/results/2024-01/
```

### With Strict QC Configuration

```bash
pixi run bactscout collect \
  sample_R1.fastq.gz \
  sample_R2.fastq.gz \
  -c strict_qc_config.yml
```

## Comparison: `collect` vs `qc`

| Feature | `collect` | `qc` |
|---------|-----------|-----|
| **Input** | Two FASTQ files (R1, R2) | Directory with many pairs |
| **Samples per run** | 1 | Multiple |
| **Use case** | Single sample | Batch processing |
| **Output location** | `Sample_ID/` | Many `Sample_*` dirs |
| **Recommended for** | Individual samples, integration | High-throughput screening |

Use `collect` when you have one or a few samples. Use `qc` when you have many samples to process together.

## Performance Tips

### Reduce Memory Usage

If your system has limited RAM:
```bash
pixi run bactscout collect sample_R1.gz sample_R2.gz -t 2
```

### Optimize for Speed

On systems with ample resources:
```bash
pixi run bactscout collect sample_R1.gz sample_R2.gz -t 16
```

### Pre-filter Reads

For very large files, pre-filter with fastp:
```bash
fastp -i sample_R1.fastq.gz -I sample_R2.fastq.gz \
      -o filtered_R1.fastq.gz -O filtered_R2.fastq.gz \
      --low_complexity_filter --length_required 50

pixi run bactscout collect filtered_R1.fastq.gz filtered_R2.fastq.gz
```

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
