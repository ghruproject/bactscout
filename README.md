# GHRU ReadQC Pipeline

A Nextflow pipeline for comprehensive quality control analysis of paired-end FASTQ sequencing data. This pipeline performs trimming, species identification, genome size estimation, MLST typing, depth calculation, and generates comprehensive QC reports.

## Pipeline Overview

The pipeline processes paired FASTQ files through the following steps:

1. **fastp** - Quality trimming and filtering of raw reads
2. **sylph** - Species identification and genome size estimation
3. **Genome Selection** - Automatically picks the smallest genome size from species matches
4. **ARIBA MLST** - Multi-locus sequence typing for strain characterization
5. **Read Depth Calculation** - Estimates sequencing coverage using the selected genome size
6. **MultiQC** - Generates comprehensive quality control reports

## Quick Start

### Prerequisites

- [Nextflow](https://nextflow.io/) (≥23.04.0)
- [Conda](https://docs.conda.io/en/latest/) or [Mamba](https://mamba.readthedocs.io/)
- Paired-end FASTQ files

### Installation

1. Clone the repository:
```bash
git clone https://github.com/cgps-discovery/GHRU-readqc.git
cd GHRU-readqc
```

2. Create the conda environment:
```bash
conda env create -f environment.yml
conda activate ghru-readqc
```

### Basic Usage

```bash
nextflow run main.nf \
    --input /path/to/fastq/directory \
    --outdir /path/to/output/directory \
    -profile conda
```

## Input Requirements

### FASTQ Files
The pipeline expects paired-end FASTQ files in the input directory with standard naming conventions:
- `sample_R1.fastq.gz` and `sample_R2.fastq.gz`
- `sample_1.fastq.gz` and `sample_2.fastq.gz`
- Files can be gzipped (`.gz`) or uncompressed
- Supports both `.fastq` and `.fq` extensions

### Directory Structure
```
input_directory/
├── sample1_R1.fastq.gz
├── sample1_R2.fastq.gz
├── sample2_R1.fastq.gz
├── sample2_R2.fastq.gz
└── ...
```

## Parameters

### Required Parameters
- `--input`: Directory containing paired FASTQ files
- `--outdir`: Output directory for results

### Optional Parameters
- `--help`: Display help message

### Resource Parameters
- `--max_memory`: Maximum memory allocation (default: 128.GB)
- `--max_cpus`: Maximum CPU cores (default: 16)
- `--max_time`: Maximum time per job (default: 240.h)

## Output Structure

```
results/
├── fastp/                    # Quality trimming results
│   ├── sample_fastp.html     # Quality report
│   ├── sample_fastp.json     # Quality metrics
│   └── sample_trimmed_R*.fastq.gz  # Trimmed reads
├── sylph/                    # Species identification
│   └── sample_sylph_profile.tsv    # Species profile
├── genome_selection/         # Genome size selection
│   └── sample_selected_genome.txt  # Selected genome info
├── ariba_mlst/              # MLST typing results
│   └── sample_mlst/         # ARIBA MLST output
├── read_depth/              # Depth calculation
│   └── sample_read_depth.txt # Coverage analysis
└── multiqc/                 # Comprehensive QC report
    ├── multiqc_report.html  # Main QC report
    └── multiqc_data/        # Supporting data
```

## Pipeline Processes

### 1. FASTP - Quality Control and Trimming
- Adapter detection and removal
- Quality trimming (Q15 threshold)
- Length filtering (minimum 36 bp)
- Generates HTML and JSON reports

### 2. SYLPH - Species Identification
- Rapid species identification using k-mer sketching
- Genome size estimation from GTDB database
- ANI (Average Nucleotide Identity) calculation

### 3. Genome Selection
- Filters high-quality species matches (ANI > 80%, containment > 0.1)
- Selects species with smallest estimated genome size
- Provides fallback estimates for common bacterial species

### 4. ARIBA MLST
- Multi-locus sequence typing
- Strain characterization
- Allele identification

### 5. Read Depth Calculation
- Counts total reads and bases
- Calculates average read length
- Estimates sequencing depth using selected genome size
- Provides coverage interpretation

### 6. MultiQC
- Aggregates all QC metrics
- Generates interactive HTML report
- Provides sample comparison views

## Execution Profiles

### Conda Profile (Recommended)
```bash
nextflow run main.nf -profile conda --input data/ --outdir results/
```

### Docker Profile
```bash
nextflow run main.nf -profile docker --input data/ --outdir results/
```

### Singularity Profile
```bash
nextflow run main.nf -profile singularity --input data/ --outdir results/
```

### Test Profile
```bash
nextflow run main.nf -profile test
```

## Resource Requirements

### Minimum Requirements
- 8 GB RAM
- 4 CPU cores
- 50 GB disk space

### Recommended Requirements
- 32 GB RAM
- 8 CPU cores
- 100 GB disk space

### Process-Specific Requirements
- **FASTP**: 4 cores, 8 GB RAM
- **SYLPH**: 8 cores, 16 GB RAM
- **ARIBA**: 4 cores, 12 GB RAM
- **Helper scripts**: 1 core, 2-4 GB RAM

## Troubleshooting

### Common Issues

1. **Memory errors**: Increase `--max_memory` parameter
2. **CPU timeout**: Increase `--max_time` parameter
3. **Database download failures**: Check internet connection and disk space
4. **FASTQ file detection**: Verify file naming conventions

### Log Files
Check the following for debugging:
- `.nextflow.log`: Main Nextflow log
- `work/` directory: Process-specific logs
- Individual process logs in work subdirectories

## Citations

If you use this pipeline, please cite:

- **Nextflow**: Di Tommaso, P. et al. Nextflow enables reproducible computational workflows. Nat Biotechnol 35, 316–319 (2017).
- **fastp**: Chen, S. et al. fastp: an ultra-fast all-in-one FASTQ preprocessor. Bioinformatics 34, i884–i890 (2018).
- **sylph**: Jim Shaw, Yun William Yu. Rapid species-level metagenome profiling with sylph. bioRxiv 2023.
- **ARIBA**: Hunt, M. et al. ARIBA: rapid antimicrobial resistance genotyping directly from sequencing reads. Microbial Genomics 3, e000131 (2017).
- **MultiQC**: Ewels, P. et al. MultiQC: summarize analysis results for multiple tools and samples in a single report. Bioinformatics 32, 3047–3048 (2016).

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For questions and support:
- Open an issue on GitHub
- Check the troubleshooting section
- Review Nextflow documentation

## Version History

- **v1.0.0**: Initial release with complete QC pipeline