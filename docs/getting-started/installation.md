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
- **ariba** - MLST analysis framework
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

**Supported platforms**: linux/amd64, linux/arm64 (for Apple Silicon)

## Automatic Database Setup

BactScout automatically downloads and configures required databases on first run:
- **Sylph GTDB database** - For taxonomic profiling
- **MLST databases** - For sequence typing (E. coli, Salmonella, Klebsiella, Pseudomonas, Acinetobacter)

No additional manual setup required!

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
