# Changelog

All notable changes to the GHRU ReadQC pipeline will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-09-26

### Added
- Initial release of GHRU ReadQC pipeline
- Complete Nextflow DSL2 pipeline for paired-end FASTQ quality control
- fastp integration for quality trimming and filtering
- sylph integration for species identification and genome size estimation
- Automated genome size selection (picks smallest genome)
- ARIBA MLST integration for strain typing
- Read depth calculation using estimated genome sizes
- MultiQC integration for comprehensive reporting
- Conda environment specification with all dependencies
- Helper scripts for genome selection and depth calculation
- Pipeline runner script with error checking
- Test data generation utilities
- Comprehensive documentation and usage examples
- Pipeline validation and testing framework
- Support for multiple execution profiles (conda, docker, singularity)
- Configurable resource requirements
- Resume capability for failed runs

### Features
- **Input**: Paired-end FASTQ files (compressed or uncompressed)
- **Quality Control**: fastp for adapter trimming and quality filtering
- **Species ID**: sylph for rapid species identification using GTDB database
- **Genome Selection**: Automatic selection of smallest genome size from matches
- **Strain Typing**: ARIBA MLST for multi-locus sequence typing
- **Coverage Analysis**: Read depth calculation with interpretation
- **Reporting**: MultiQC for interactive quality control reports
- **Testing**: Synthetic test data generation and validation tools
- **Documentation**: Comprehensive README, usage examples, and troubleshooting

### Technical Details
- Nextflow DSL2 compatible
- Supports conda, docker, and singularity containers
- Configurable resource limits and retry strategies
- Process isolation and error handling
- Comprehensive logging and monitoring
- HPC system compatibility
- Resume functionality for interrupted runs

### Dependencies
- Nextflow ≥23.04.0
- fastp 0.23.4
- sylph 0.6.1
- ARIBA 2.14.6
- MultiQC 1.19
- Python 3.11 with pandas, numpy, biopython
- Conda or compatible package manager

### Performance
- Optimized for bacterial genomics data
- Scales from single samples to large batches
- Typical runtime: 30-60 minutes per sample
- Memory requirements: 8-32GB depending on data size
- CPU requirements: 4-16 cores recommended