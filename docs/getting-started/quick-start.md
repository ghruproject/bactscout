# Quick Start

Get up and running with BactScout in 5 minutes.

## 1. Install BactScout

```bash
git clone https://github.com/ghruproject/bactscout.git
cd bactscout
pixi install
```

## 2. Prepare Your Input

Organize your FASTQ files in a directory with standard naming:

```
data/
├── sample_001_R1.fastq.gz
├── sample_001_R2.fastq.gz
├── sample_002_R1.fastq.gz
├── sample_002_R2.fastq.gz
└── ...
```

!!! note "Naming Formats Supported"
    - `sample_001_R1.fastq.gz` ✅
    - `sample_001_1.fastq.gz` ✅
    - `sample_001.fastq` ✅
    - `sample.001_R1.fq.gz` ✅

## 3. Run Quality Control

=== "Batch Processing (Multiple Samples)"
    ```bash
    pixi run bactscout qc data/ -o results/
    ```

=== "Single Sample"
    ```bash
    pixi run bactscout collect data/sample_001_R1.fastq.gz data/sample_001_R2.fastq.gz -o results/
    ```

## 4. Generate Summary Report

```bash
pixi run bactscout summary results/
```

This creates `results/final_summary.csv` with all samples merged.

## 5. Analyze Results

Check `results/final_summary.csv`:

```
sample_id,a_final_status,coverage_status,mlst_status,species,...
sample_001,PASSED,PASSED,PASSED,Escherichia coli,...
sample_002,WARNING,PASSED,WARNING,Salmonella enterica,...
```

## Common Options

```bash
# Use custom configuration
pixi run bactscout qc data/ -c custom_config.yml

# Specify number of threads
pixi run bactscout qc data/ -t 8

# Skip preflight checks (not recommended)
pixi run bactscout qc data/ --skip-preflight
```

## What's Next?

- 📖 Read about [Quality Control Criteria](../guide/quality-control.md)
- ⚙️ Learn [Configuration Options](configuration.md)
- 🔍 Understand [Output Format](../usage/output-format.md)
