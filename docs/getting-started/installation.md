# Installation

## Prerequisites

BactScout uses [Pixi](https://pixi.sh) for reproducible environment and dependency management.

### Install Pixi

=== "macOS/Linux"
    ```bash
    curl -fsSL https://pixi.sh/install.sh | bash
    ```

=== "Conda/Mamba"
    ```bash
    conda install -c conda-forge pixi
    ```

=== "Homebrew (macOS)"
    ```bash
    brew install pixi
    ```

After installation, restart your terminal or refresh your shell configuration.

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/ghruproject/bactscout.git
cd bactscout
```

### 2. Install Dependencies

```bash
pixi install
```

This will install all required dependencies including:

- **fastp** - Read quality control and trimming
- **sylph** - Ultra-fast taxonomic profiling
- **stringMLST** - MLST analysis
- **Python 3.11+** - Core runtime
- **typer** - CLI framework
- **rich** - Beautiful terminal output

### 3. Verify Installation

```bash
pixi run bactscout --help
```

## Docker Installation

BactScout is also available as a Docker image:

```bash
# Build locally
docker build -t bactscout:latest -f docker/Dockerfile .

# Run with Docker
docker run -v /path/to/fastq:/input -v /path/to/output:/output \
  bactscout:latest pixi run bactscout qc /input -o /output
```

If you prefer to run BactScout from a **pre-built container**, pull the image from Docker Hub and run it with your data mounted. The official image is published at: [https://hub.docker.com/repository/docker/happykhan/bactscout/general](https://hub.docker.com/repository/docker/happykhan/bactscout/general)

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

**Supported platforms**: linux/amd64, linux/arm64 (for Apple Silicon)

## Automatic Database Setup

BactScout automatically downloads and configures required databases on first run:

- **Sylph GTDB database** - For taxonomic profiling
- **MLST databases** - For sequence typing (*E. coli, Salmonella, Klebsiella, Pseudomonas, Acinetobacter*)

The sylph database will occupy the most disk space (~4GB). No additional manual setup required! If you want to pre-download databases, run:

```bash
pixi run bactscout preflight
```

This command performs all validation checks and downloads necessary databases without running the full QC pipeline. This is useful for ensuring everything is set up correctly before processing large datasets (on infrastructure with limited internet access, etc.)

## Troubleshooting

!!! tip "Pixi not found after installation?"
    Restart your terminal or run:
    ```bash
    source ~/.bashrc  # or ~/.zshrc for macOS
    ```

!!! warning "Permission denied installing Pixi?"
    Try installing to a different location:
    ```bash
    curl -fsSL https://pixi.sh/install.sh | PIXI_HOME=~/.local/pixi bash
    ```

See [Troubleshooting](../guide/troubleshooting.md) for more help.
