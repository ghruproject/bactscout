
# 🧬 BactScout

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://ghruproject.github.io/bactscout/)
[![Release](https://img.shields.io/github/v/release/ghruproject/bactscout?include_prereleases)](https://github.com/ghruproject/bactscout/releases)
[![codecov](https://codecov.io/github/ghruproject/bactscout/graph/badge.svg?token=NH4TFLH9X4)](https://codecov.io/github/ghruproject/bactscout)
[![Pixi](https://img.shields.io/badge/built%20with-pixi-green)](https://pixi.sh)

BactScout performs fast post-sequencing checks on bacterial WGS data: read QC (fastp), taxonomic profiling (Sylph) and MLST-based (stringMLST) checks to help decide whether samples are ready for assembly or downstream analysis.

Full user documentation, configuration reference, and examples are available at:

https://ghruproject.github.io/bactscout/

Important: this repository now contains a breaking change in v1.2.0 — coverage-related output fields were renamed to canonical keys (for example `coverage_estimate_sylph` and `coverage_estimate_qualibact`). 

## ✨ Features

- What BactScout’s QC does
  - Rapid post‑sequencing checks for bacterial WGS (fit for assembly, typing, AMR and phylogeny)
  - Combines read‑level metrics from fastp (Q30, mean read length, duplication, N‑content, adapter over‑representation)
  - Adds Sylph taxonomic profiling and a reads/expected‑genome‑size coverage estimate (you get both Sylph‑derived and calculated coverage)
  - Two‑tier thresholds (WARN / FAIL) are configurable so borderline samples are flagged for review rather than auto‑rejected
  - Full list of reported fields and per‑sample outputs: https://ghruproject.github.io/bactscout/usage/output-format/

- PASS / WARNING / FAIL logic
  - Any critical metric FAILED (Q30, read length, contamination, or GC deviation) → overall FAIL
  - Both coverage estimates FAILED → overall FAIL; one coverage FAILED → overall WARNING
  - Non‑critical issues (duplication, adapters, missing MLST) generally produce WARNINGs rather than immediate FAILs
  - All thresholds are configurable in `bactscout_config.yml`; remediation and examples: https://ghruproject.github.io/bactscout/getting-started/configuration
  - See Quality Control Guide for full details: https://ghruproject.github.io/bactscout/guide/quality-control/


## 🚀 Quick Start
### `qc` - Quality Control (Main Command)

Run quality control analysis on FASTQ files:

```bash
pixi run bactscout qc /path/to/fastq/files [OPTIONS]
```

**Options:**
- `--output, -o` - Output directory (default: `bactscout_output`)
- `--threads, -t` - Number of threads (default: 4)
- `--config, -c` - Config file path (default: `bactscout_config.yml`)
- `--skip-preflight` - Skip preflight checks (not recommended)

**Example:**
```bash
pixi run bactscout qc ./test_data -o results -t 8
```

### `collect` - Process a single sample

Process a single paired-end sample (R1 and R2 FASTQ files):

```bash
pixi run bactscout collect <read1.fastq.gz> <read2.fastq.gz> [OPTIONS]
```

### `summary` - Generate Summary Report

Generate a consolidated summary of all samples:

```bash
pixi run bactscout summary /path/to/results [OPTIONS]
```

### `version` - Print version

Print the installed BactScout version string:

```bash
pixi run bactscout version
```

**Nextflow and HPC users should reads the Scaling Up Guide:** https://ghruproject.github.io/bactscout/guide/scaling/


## ⚙️ Installation

The recommended way to install BactScout and its tool dependencies is via Pixi (the project provides a reproducible environment). See the full installation guide: https://ghruproject.github.io/bactscout/getting-started/installation/

Quick steps:

```bash
# install pixi (macOS/Linux)
curl -fsSL https://pixi.sh/install.sh | bash

# clone repo and install dependencies
git clone https://github.com/ghruproject/bactscout.git
cd bactscout
pixi install

# verify
pixi run bactscout --help
```

### Docker

A ready-to-run Docker image is available for zero-install use. See the installation guide for details and alternative tags: https://ghruproject.github.io/bactscout/getting-started/installation/

Example:

```bash
docker pull happykhan/bactscout:latest
docker run --rm -v "$PWD":/data --user "$(id -u):$(id -g)" happykhan/bactscout:latest \
  bactscout qc /data/fastq -o /data/results
```


# Outputs

Using the `qc` command will generate an output directory with the following structure:

```
bactscout_output/
├── sample1/
│   ├── sylph_report.txt          # Species identification results
│   ├── mlst.tsv                  # MLST sequence typing results
│   ├── sample1_summary.csv       # Per-sample quality summary
│   └── sample1_1.fastp.json      # Fastp quality control metrics (R1)
├── sample2/ ...
└── final_summary.csv             # Merged summary of all samples
```

A full list of output fields is available in the [Output Format documentation](https://ghruproject.github.io/bactscout/usage/output-format/).