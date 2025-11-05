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

For **cultured bacterial isolates** intended for genome assembly, BactScout evaluates multiple quality metrics with **WARNING** and **FAIL** thresholds to ensure your data is suitable for downstream analysis:

### ✅ **PASS Criteria:**

All thresholds can be adjusted in the `bactscout_config.yml` file.

- **📈 Coverage Depth**: Adequate post-trimming read coverage
  - **FAIL threshold**: < 20x coverage (insufficient for assembly)
  - **WARNING threshold**: < 30x coverage (marginal for high-quality assembly)
  - **PASS**: ≥ 30x coverage
  - Ensures sufficient depth for high-quality genome assembly
  - Reduces assembly gaps and improves base calling accuracy
  - See columns `coverage_status` and `coverage_estimate_qualibact_status`

- **🧬 Species Purity & GC Content**: Single species with expected GC content
  - **Contamination FAIL threshold**: > 10% reads from secondary species
  - **Contamination WARNING threshold**: > 5% reads from secondary species
  - **PASS**: < 5% contamination AND GC within expected range (±5% of species reference)
  - Confirms sample contains only the expected organism
  - Rules out contamination from other bacterial species
  - Critical for accurate genome reconstruction
  - See columns `contamination_status`, `species_status`, and `gc_content_status`

- **📏 Read Quality & Length**: High-quality reads of adequate length
  - **Q30 FAIL threshold**: < 70% bases with Q30+ quality
  - **Q30 WARNING threshold**: < 80% bases with Q30+ quality
  - **Read length FAIL threshold**: < 100bp mean length
  - **Read length WARNING threshold**: < 80bp mean length (deprecated, will use 100bp)
  - **PASS**: ≥ 70% Q30 bases AND ≥ 100bp mean length
  - Indicates proper sequencing run completion
  - Ensures optimal assembly performance
  - See columns `read_length_status` and `read_q30_status`

- **🔬 Additional QC Metrics**:
  - **Duplication Rate**: < 20% (WARNING), < 30% (FAIL) - See `duplication_status`
  - **N-Content**: < 0.1% ambiguous bases (WARNING if exceeded) - See `n_content_status`
  - **Adapter Detection**: ≤ 5 overrepresented sequences (WARNING/FAIL) - See `adapter_detection_status`

- **🎯 MLST Validation**: **Valid ST (Sequence Type) called** for species with available schemes
  - Confirms species identification through multi-locus sequence typing
  - Provides epidemiological context and strain characterization
  - Available for major pathogens (E. coli, Klebsiella, Salmonella, Acinetobacter, Pseudomonas)
  - Novel ST (ST=0) is acceptable and marked as PASSED
  - No ST or invalid ST is a WARNING sign
  - See column `mlst_status`

The same information as a table: 

| Metric | Default Thresholds | Purpose / Rationale | Key Columns |
| :----- | :----------------- | :------------------ | :---------- |
| 📈 **Coverage Depth** | FAIL: < 20x<br>WARNING: < 30x<br>PASS: ≥ 30x | • Ensures sufficient depth for high-quality assembly<br>• Reduces assembly gaps and improves base-calling accuracy<br>• Two-tier system allows marginal samples to proceed with caution | `coverage_status`, `coverage_estimate_qualibact_status` |
| 🧬 **Species Purity** | FAIL: > 10% contamination<br>WARNING: > 5% contamination<br>PASS: < 5% + GC within range | • Confirms sample contains only expected organism<br>• Rules out contamination from other species<br>• Critical for accurate genome reconstruction<br>• GC content validates species identification | `contamination_status`, `species_status`, `gc_content_status` |
| 📏 **Read Quality** | Q30 FAIL: < 70%<br>Q30 WARNING: < 80%<br>Length FAIL: < 100bp<br>PASS: ≥ 70% Q30 + ≥ 100bp | • Indicates proper sequencing run completion<br>• Ensures optimal assembly performance<br>• High Q30 reduces errors in final assembly | `read_length_status`, `read_q30_status` |
| 🔬 **Duplication** | WARNING: > 20%<br>FAIL: > 30% | • Detects PCR bias or library complexity issues<br>• High duplication may indicate poor library quality | `duplication_status` |
| 🧪 **N-Content** | WARNING: > 0.1% | • Detects ambiguous base calls (quality issues)<br>• Excessive N's indicate sequencing problems | `n_content_status` |
| 🧬 **Adapter Contamination** | WARNING: 1-5 sequences<br>FAIL: > 5 sequences | • Detects overrepresented sequences<br>• May indicate adapter contamination or other artifacts | `adapter_detection_status` |
| 🎯 **MLST Validation** | PASS: Valid ST or Novel ST (0)<br>WARNING: No ST / Invalid ST | • Confirms species identification through MLST<br>• Provides epidemiological context<br>• Available for major pathogens (*E. coli*, *Klebsiella*, *Salmonella*, *Acinetobacter*, *Pseudomonas*) | `mlst_status` |


### ⚠️ **WARNING/FAIL Indicators:**

BactScout uses a **two-tier system** (WARNING/FAIL) for most metrics:

- **FAILED samples**: Critical issues that typically prevent successful genome assembly
  - Coverage < 20x: Severely insufficient depth
  - Contamination > 10%: High levels of mixed species
  - Q30 < 70%: Very poor base quality
  - Read length < 100bp: Truncated reads
  - Duplication > 30%: Severe PCR bias
  - Adapter contamination > 5 overrepresented sequences

- **WARNING samples**: Marginal quality that may work but requires attention
  - Coverage 20-30x: May result in fragmented assemblies
  - Contamination 5-10%: Moderate contamination
  - Q30 70-80%: Acceptable but not optimal quality
  - Duplication 20-30%: Moderate PCR bias
  - Invalid/Missing ST: May indicate mixed cultures, novel strains, or species without MLST schemes
  - Adapter contamination 1-5 overrepresented sequences: Minor contamination

**Note**: Some organisms are not well characterized by MLST. A sample shouldn't automatically fail due to missing ST, but it should be reviewed carefully for contamination or mixed cultures.


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
- **stringmlst** - MLST caller for sequence typing
- **Python 3.11+** - Core runtime
- **typer** - CLI framework with Rich formatting
- **rich** - Beautiful terminal output
- **pyyaml** - YAML configuration parsing
- **psutil** - System resource monitoring

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

- **Key Status Columns:**
- **a_final_status**: Overall PASS/WARNING/FAIL based on all criteria
 - **coverage_status** / **coverage_estimate_qualibact_status**: Coverage depth evaluation (PASS ≥30x, WARNING ≥20x)
- **contamination_status**: Species purity (PASS <5%, WARNING <10%)
- **species_status**: Single species detection
- **gc_content_status**: GC content within expected range
- **read_q30_status**: Base quality (PASS ≥70%, WARNING ≥80%)
- **read_length_status**: Read length evaluation (PASS ≥100bp)
- **duplication_status**: PCR duplication rate (PASS ≤20%, WARNING ≤30%)
- **n_content_status**: Ambiguous base content (WARNING >0.1%)
- **adapter_detection_status**: Adapter contamination check
- **mlst_status**: MLST sequence typing validation

**Key Metric Columns:**
- **sample_id**: Sample identifier
- **read_total_reads** / **read_total_bases**: Sequencing depth metrics
- **read_q20_rate** / **read_q30_rate**: Base quality scores (higher is better)
- **read1_mean_length** / **read2_mean_length**: Average read length (R1 and R2)
- **duplication_rate**: Fraction of duplicate reads (0.0-1.0)
- **n_content_rate**: Percentage of ambiguous (N) bases
- **gc_content**: Genomic GC percentage
- **species**: Taxonomic identification from Sylph
- **species_abundance**: Percentage of reads assigned to detected species
- **species_coverage**: Estimated coverage from Sylph
 - **coverage_estimate_sylph**: Sylph-based genome coverage depth
 - **coverage_estimate_qualibact**: Alternative coverage calculation (total_bases / expected_genome_size)
- **mlst_st**: Sequence Type from MLST analysis (0 = novel ST)
- **gc_content_lower** / **gc_content_upper**: Expected GC range for species
- **genome_size_expected**: Expected genome size for coverage calculation

**Message Columns** (ending in `_message`):
Each status field has a corresponding message column providing detailed explanations of PASS/WARNING/FAIL reasons and threshold values.

Use this file to:
- Prioritize samples for genome assembly
- Identify problematic samples requiring attention
- Generate summary statistics for your sequencing run quality
- Filter samples by specific QC criteria