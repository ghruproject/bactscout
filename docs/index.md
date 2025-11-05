# Welcome to BactScout

BactScout is a Python-based pipeline for rapid, standardized quality assessment and taxonomic profiling of sequencing data from cultured bacterial isolates. It integrates tools like Fastp for read quality control, Sylph for species-level taxonomic profiling, and StringMLST for multi-locus sequence typing into a single, reproducible workflow. BactScout evaluates sequencing data across multiple quality dimensions—read quality, coverage depth, species purity, GC content, and strain typing—producing clear, interpretable quality metrics for downstream applications such as genome assembly, antimicrobial resistance prediction, genotyping, and phylogenetic inference.

## ✨ Key Features

- 🧭 Command-line interface — a top-level Typer application (entrypoint `bactscout`) provides intuitive subcommands such as `bactscout qc` and `bactscout summarize` for per-sample and batch workflows. The project also exposes a `bactscout` console script for easy execution via `pixi run` or Docker.
- 📊 Fastp integration — read-level QC, adapter trimming, mean read length and Q30 calculations, and optional Fastp HTML reports for visual inspection.
- 🔬 Sylph-based taxonomic profiling — species identification and abundance estimates used to compute species-aware thresholds, contamination percentages, and genome-size-informed coverage estimates.
- 🛡️ StringMLST support — MLST assignment when a single dominant species is detected, producing sequence type (ST) calls and allelic summaries to aid downstream analyses.
- ✅ Automated QC decisions — per-sample PASS/WARNING/FAIL calls derived from configurable thresholds (duplication rate, contamination, N-content, adapter counts, coverage), with CSV summaries and a final batch summary (`final_summary.csv`).
- Containerized, reproducible environments — development and docs environments managed via Pixi (pre-built `dev` and `docs` envs) and an official Docker image on Docker Hub (`happykhan/bactscout`) for zero-install runs.
- ⚡ Parallel processing and robustness — samples are processed in parallel using a thread pool (see `bactscout.thread`), with defensive handling for edge cases (empty species lists, missing metadata) to avoid runtime crashes.

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

!!! note "BactScout on HPC and at scale."

    For tips on running bactscout in an HPC (using nextflow or otherwise), see the [Scaling up Guide](guide/scaling.md).


**Conda install coming soon!**

### Docker quickstart

If you prefer to run BactScout from a pre-built container, pull the image from Docker Hub and run it with your data mounted. The official image is published at: [https://hub.docker.com/repository/docker/happykhan/bactscout/general](https://hub.docker.com/repository/docker/happykhan/bactscout/general)

Example (replace paths with your local data directory):

```bash
# Pull the latest image
docker pull happykhan/bactscout:latest

# Run BactScout to perform QC on FASTQ files mounted from the current directory
docker run --rm \
	--volume "$PWD":/data \
	--user "$(id -u):$(id -g)" \
	happykhan/bactscout:latest \
	bactscout qc /data/fastq -o /data/results

# Show available commands
docker run --rm happykhan/bactscout:latest bactscout --help
```

Notes:

- Mount your input/output directories under `/data` (or change the paths above).
- Use the `--user $(id -u):$(id -g)` option to have output files owned by your user on macOS/Linux.

!!! note "Internet Access Requirement"
    BactScout requires internet access the first time it is run to download necessary databases (Sylph GTDB, MLST schemes). If running in an environment without internet access, consider pre-downloading databases using the `pixi run bactscout preflight` command after installation.

## 📚 Documentation

- [Installation Guide](getting-started/installation.md) - Set up BactScout
- [Configuration Options](getting-started/configuration.md) - Customize your runs
- [Quality Control Criteria](guide/quality-control.md) - Understand the QC metrics
- [Usage Guide](usage/qc-command.md) - Learn all commands
- [API Reference](reference/api.md) - Python API documentation

## 🔗 Links

- **GitHub**: [ghruproject/bactscout](https://github.com/ghruproject/bactscout)
- **Issues**: [Report bugs](https://github.com/ghruproject/bactscout/issues)
- **Releases**: [Latest version](https://github.com/ghruproject/bactscout/releases)

## 📜 License

BactScout is licensed under the GNU General Public License v3.0. See the [LICENSE](https://github.com/ghruproject/bactscout/blob/main/LICENSE) file for details.
