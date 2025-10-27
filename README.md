# 🧬 BactScout

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![codecov](https://codecov.io/github/ghruproject/bactscout/graph/badge.svg?token=NH4TFLH9X4)](https://codecov.io/github/ghruproject/bactscout)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://github.com/ghruproject/bactscout/blob/main/README.md)
[![Release](https://img.shields.io/github/v/release/ghruproject/bactscout?include_prereleases)](https://github.com/ghruproject/bactscout/releases)
[![Pixi](https://img.shields.io/badge/built%20with-pixi-green)](https://pixi.sh)

BactScout is a high-performance Python pipeline for rapid quality assessment, taxonomic profiling, and MLST-based quality control of bacterial sequencing data.


## ✨ Features

- 📊 **Read Quality Control**: Using Fastp

- 🔬 **Taxonomic Profiling**: Ultra-fast metagenomic profiling with Sylph

- 🛡️ **MLST Quality Control**: Multi-locus sequence typing with StringMLST for genome quality assessment. A valid ST is a good sign.

## 🎯 Quality Control Criteria

For **cultured bacterial isolates** intended for genome assembly, BactScout evaluates several key quality metrics to ensure your data is suitable for downstream analysis:

### ✅ **PASS Criteria:**

Most thresholds can be adjusted in the `bactscout_config.yml` file.

- **📈 Coverage Depth**: Good post-trimming read coverage (> 30x default)
  - Ensures sufficient depth for high-quality genome assembly
  - Reduces assembly gaps and improves base calling accuracy
  - See columns `coverage_status` and `coverage_alt_status`.

- **🧬 Species Purity**: There should be no significant of reads assigned to other taxa (< 10% default) and GC content is within expected range for the species. 
  - Confirms sample contains only the expected organism
  - Rules out contamination from other bacterial species
  - Critical for accurate genome reconstruction
  - See columns `contamination_status`, `species_status` and `gc_content_status`.

- **📏 Read Length**: Reads of **good length** (> 100bp; can be changed in `bactscout_config.yml`)
  - Indicates proper sequencing run completion
  - Ensures optimal assembly performance
  - See column `read_length_status` and `read_q30_status`.

- **🎯 MLST Validation**: **Valid ST (Sequence Type) called** for species with available schemes
  - Confirms species identification through multi-locus sequence typing
  - Provides epidemiological context and strain characterization
  - Available for major pathogens (E. coli, Klebsiella, Salmonella, etc.)
  - A novel ST is acceptable, but no ST or multiple STs is a warning sign.
  - See column `mlst_status`.

The same information as a table: 

| Metric                 | Default Threshold                                                        | Purpose / Rationale                                                                                                                                                                               | Key Columns                                                   |
| :--------------------- | :----------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------ |
| 📈 **Coverage Depth**  | > 30×                                                                    | • Ensures sufficient depth for high-quality genome assembly<br>• Reduces assembly gaps and improves base-calling accuracy                                                                         | `coverage_status`, `coverage_alt_status`                      |
| 🧬 **Species Purity**  | < 10 % of reads assigned to other taxa; GC content within expected range | • Confirms sample contains only the expected organism<br>• Rules out contamination from other species<br>• Critical for accurate genome reconstruction                                            | `contamination_status`, `species_status`, `gc_content_status` |
| 📏 **Read Length**     | average len > 100 bp                                                                 | • Indicates proper sequencing run completion<br>• Ensures optimal assembly performance                                                                                                            | `read_length_status`, `read_q30_status`                       |
| 🎯 **MLST Validation** | Valid ST (Sequence Type) for species with available scheme               | • Confirms species identification through MLST<br>• Provides epidemiological context and strain characterization<br>• Available for major pathogens (*E. coli*, *Klebsiella*, *Salmonella*, etc.) | `mlst_status`                                                 |


### ⚠️ **WARNING/FAIL Indicators:**

- **Low coverage** (< 30x): May result in fragmented assemblies. If you are only considering read mapping, you might get away with lower coverage (>5x)
- **Multiple species**: Indicates contamination requiring sample cleanup
- **Truncated reads**: Suggests sequencing quality issues
- **Invalid/Missing ST**: May indicate mixed cultures or novel strains. Some organisms are not well characterized by MLST, so I would not fail a sample just because it has no ST, but I would be cautious.


## 📦 Installation

BactScout uses [pixi](https://pixi.sh) for environment and dependency management. This ensures reproducible builds and easy installation of both Python and bioinformatics tools.

### Prerequisites

First, install pixi if you haven't already:

```bash
# On macOS/Linux
curl -fsSL https://pixi.sh/install.sh | bash

# Or using conda/mamba
conda install -c conda-forge pixi

# Or using Homebrew (macOS)
brew install pixi
```

After installation, restart your terminal or refresh your shell configuration.


### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ghruproject/bactscout.git
   cd bactscout
   ```

2. **Install dependencies using pixi:**
   ```bash
   pixi install
   ```

3. **Run BactScout:**
   ```bash
   pixi run bactscout --help
   ```

   Or use the `qc` command:
   ```bash
   pixi run bactscout qc /path/to/fastq/files
   ```

**Note:** BactScout automatically downloads required databases (Sylph GTDB, MLST schemes) on first run if they don't exist locally.

The pixi environment includes all necessary dependencies:
- **fastp** - Read quality control and trimming
- **sylph** - Ultra-fast taxonomic profiling
- **ariba** - MLST analysis framework
- **Python 3.11+** - Core runtime
- **typer** - CLI framework with Rich formatting
- **rich** - Beautiful terminal output
- **pyaml** - YAML configuration parsing
- **psutil** - System resource monitoring
- **stringmlst** - MLST caller

# 🚀 Usage

BactScout provides three main commands:

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

### `collect` - Collect Results

Collect and organize results from a previous run:

```bash
pixi run bactscout collect /path/to/results [OPTIONS]
```

### `summary` - Generate Summary Report

Generate a consolidated summary of all samples:

```bash
pixi run bactscout summary /path/to/results [OPTIONS]
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

### 📊 **final_summary.csv**

The `final_summary.csv` file is a comprehensive report that consolidates all quality control metrics for every sample in your batch. This single file provides:

**Key Columns Include:**
- **sample_id**: Sample identifier
- **a_final_status**: Overall PASS/FAIL/WARNING based on all criteria
- **total_reads/total_bases**: Sequencing depth metrics
- **read_q20_rate/read_q30_rate**: Base quality scores (Q20/Q30 higher is better)
- **read1_mean_length/read2_mean_length**: Average read length (R1 and R2)
- **gc_content**: Genomic GC percentage
- **species**: Taxonomic identification from Sylph
- **species_status**: PASSED/FAILED/WARNING based on single species detection
- **species_abundance**: Percentage of reads assigned to detected species
- **species_coverage**: Estimated coverage from species identification
- **mlst_st**: Sequence Type from MLST analysis
- **mlst_status**: PASSED/FAILED/WARNING for valid ST assignment
- **coverage_estimate**: Calculated genome coverage depth
- **coverage_alt_estimate**: Alternative coverage calculation
- **coverage_status**: PASSED (≥30x) / FAILED (<30x) / WARNING
- **gc_content_status**: PASSED/FAILED based on expected species range
- **contamination_status**: PASSED/FAILED based on species purity threshold
- **read_length_status**: PASSED/FAILED based on minimum read length (default >100bp)

Use this file to prioritize samples for genome assembly, identify problematic samples requiring attention, and generate summary statistics for your sequencing run quality.