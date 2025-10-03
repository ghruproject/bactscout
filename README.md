# 🧬 BactScout Pipeline

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

BactScout is a high-performance Python pipeline for rapid quality assessment, taxonomic profiling, and MLST-based quality control of bacterial sequencing data. Built with modern Python tooling and designed for speed, it processes paired-end FASTQ files in parallel with beautiful progress reporting. 


## ✨ Features

- 📊 **Read Quality Control**: Using Fastp

- 🔬 **Taxonomic Profiling**: Ultra-fast metagenomic profiling with Sylph

- 🛡️ **MLST Quality Control**: Multi-locus sequence typing with ARIBA for genome quality assessment. A valid ST is a good sign.

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