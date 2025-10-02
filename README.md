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

3. **Activate the environment:**
   ```bash
   pixi shell
   ```

4. **Run BactScout:**
   ```bash
   pixi run bactscout --help
   ```

### Alternative: Direct execution

You can also run BactScout directly without activating the shell:

```bash
pixi run bactscout [your-arguments]
```

The pixi environment includes all necessary dependencies:
- **fastp** - for read quality control
- **sylph** - for taxonomic profiling  
- **ariba** - for MLST analysis
- **Python packages** - typer, rich, pyaml, psutil 
