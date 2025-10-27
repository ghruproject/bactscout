# Welcome to BactScout

BactScout is a high-performance Python pipeline for rapid quality assessment, taxonomic profiling, and MLST-based quality control of bacterial sequencing data.

## ✨ Key Features

- 📊 **Read Quality Control** - Using Fastp for comprehensive quality metrics
- 🔬 **Taxonomic Profiling** - Ultra-fast metagenomic profiling with Sylph
- 🛡️ **MLST Quality Control** - Multi-locus sequence typing with StringMLST for genome quality assessment

## 🚀 Quick Start

Get started in three simple steps:

```bash
# 1. Clone the repository
git clone https://github.com/ghruproject/bactscout.git
cd bactscout

# 2. Install dependencies with Pixi
pixi install

# 3. Run BactScout on your samples
pixi run bactscout qc /path/to/fastq/files -o results
```

## 📚 Documentation

- [Installation Guide](getting-started/installation.md) - Set up BactScout
- [Quality Control Criteria](guide/quality-control.md) - Understand the QC metrics
- [Usage Guide](usage/qc-command.md) - Learn all commands
- [API Reference](reference/api.md) - Python API documentation

## 🔗 Links

- **GitHub**: [ghruproject/bactscout](https://github.com/ghruproject/bactscout)
- **Issues**: [Report bugs](https://github.com/ghruproject/bactscout/issues)
- **Releases**: [Latest version](https://github.com/ghruproject/bactscout/releases)

## 📜 License

BactScout is licensed under the GNU General Public License v3.0. See the [LICENSE](https://github.com/ghruproject/bactscout/blob/main/LICENSE) file for details.
