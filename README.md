# 🧬 BactScout

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Tests](https://github.com/ghruproject/bactscout/workflows/CI/badge.svg)](https://github.com/ghruproject/bactscout/actions)
[![Coverage](https://img.shields.io/badge/coverage-67%25-yellow.svg)](https://github.com/ghruproject/bactscout)
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

- **📈 Coverage Depth**: Post-trimming read coverage **> Some number (default 30x)**
  - Ensures sufficient depth for high-quality genome assembly
  - Reduces assembly gaps and improves base calling accuracy

- **🧬 Species Purity**: **Single species detected** by taxonomic profiling
  - Confirms sample contains only the expected organism
  - Rules out contamination from other bacterial species
  - Critical for accurate genome reconstruction

- **📏 Read Length**: Reads of **expected length** (typically 150bp for Illumina)
  - Indicates proper sequencing run completion
  - Ensures optimal assembly performance

- **🎯 MLST Validation**: **Valid ST (Sequence Type) called** for species with available schemes
  - Confirms species identification through multi-locus sequence typing
  - Provides epidemiological context and strain characterization
  - Available for major pathogens (E. coli, Klebsiella, Salmonella, etc.)

### ⚠️ **WARNING/FAIL Indicators:**

- **Low coverage** (< 30x): May result in fragmented assemblies. If you are only consider read mapping, you might get away with lower coverage (>5x)
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

** I am working on a better way to do this **

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ghruproject/bactscout.git
   cd bactscout
   ```

2. **Install dependencies using pixi:**
   ```bash
   pixi install
   ```

4. **Run BactScout:**
   ```bash
   pixi run bactscout --help
   ```

The pixi environment includes all necessary dependencies:
- **fastp** - for read quality control
- **sylph** - for taxonomic profiling  
- **ariba** - for MLST analysis
- **Python packages** - typer, rich, pyaml, psutil 

# 🚀 Usage

```                                                                                                                                                                                                                                                           
 Usage: bactscout.py qc [OPTIONS] INPUT_DIR                                                                                                                                                                                                                
                                                                                                                                                                                                                                                           
 Main QC command                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                           
╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    input_dir      TEXT  Path to the input directory containing FASTQ files [required]                                                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --output   -o      TEXT     Path to the output directory [default: bactscout_output]                                                                                                                                                                    │
│ --threads  -t      INTEGER  Number of threads to use [default: 4]                                                                                                                                                                                       │
│ --config   -c      TEXT     Path to the configuration file [default: bactscout_config.yml]                                                                                                                                                              │
│ --help                      Show this message and exit.                                                                                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

# Outputs

Using the regular `qc` command will generate an output directory with the following structure:

```
bactscout_output/
├── sample1/
│   ├── sylph_report.txt
│   ├── mlst.tsv
│   ├── sample1_summary.csv
│   └── sample1.fastp.json
├── sample2/ ...
└── final_summary.csv
```

### 📊 **final_summary.csv**

The `final_summary.csv` file is a comprehensive report that consolidates all quality control metrics for every sample in your batch. This single file provides:

**Key Columns Include:**
- **sample_id**: Sample identifier
- **total_reads/total_bases**: Sequencing depth metrics
- **q20_rate/q30_rate**: Base quality scores (higher is better)
- **gc_content**: Genomic GC percentage
- **species**: Taxonomic identification from Sylph
- **species_status**: PASSED/FAILED based on single species detection
- **mlst_st**: Sequence Type from MLST analysis
- **mlst_status**: PASSED/FAILED for valid ST assignment
- **estimated_coverage**: Calculated genome coverage depth
- **coverage_status**: PASSED (≥30x) / FAILED (<30x)
- **gc_content_status**: PASSED/FAILED based on expected species range

**Overall Assessment:**
Each sample receives individual PASS/FAIL status for each quality metric, allowing you to quickly identify:
- ✅ **Assembly-ready samples** (all metrics PASSED)
- ⚠️ **Marginal samples** (some metrics FAILED) 
- ❌ **Poor quality samples** (multiple failures requiring re-sequencing)

Use this file to prioritize samples for genome assembly, identify problematic samples requiring attention, and generate summary statistics for your sequencing run quality.