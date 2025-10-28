---
title: 'BactScout: A Python pipeline for quality assessment and taxonomic profiling of bacterial sequencing data'
tags:
  - Python
  - bioinformatics
  - quality control
  - bacterial genomics
  - MLST
  - taxonomic profiling
  - genome assembly
authors:
  - name: GHRU Project Contributors
    affiliation: 1
affiliations:
  - index: 1
    name: Global Healthcare and Research Unit
date: 28 October 2025
bibliography: paper.bib
---

# Summary

BactScout is a high-performance Python pipeline designed for rapid quality assessment, taxonomic profiling, and multi-locus sequence typing (MLST) of bacterial sequencing data. The software integrates three complementary bioinformatics tools—Fastp, Sylph, and StringMLST—into a unified workflow that processes paired-end Illumina sequencing data from cultured bacterial isolates. BactScout evaluates sequence data against multiple quality thresholds including sequencing coverage depth, base quality scores, read length, species purity, GC content, and strain typing, providing researchers with comprehensive quality metrics suitable for downstream applications including genome assembly and epidemiological surveillance.

The pipeline implements a modular architecture with configurable quality thresholds, parallel processing capabilities, and detailed result reporting. A single command processes single or multiple samples, generating per-sample quality summaries and batch-level statistical reports. BactScout's design prioritizes ease of use, reproducibility through containerized dependencies via Pixi, and extensibility for integration into genomics workflows.

# Statement of need

Quality assessment of bacterial sequencing data is a critical step in genomic analysis pipelines, particularly for applications requiring high-confidence genome assemblies. Researchers face several challenges:

1. **Fragmented Quality Assessment Landscape**: Existing quality control approaches typically require chaining multiple tools (quality trimming, taxonomic assignment, strain typing) with custom scripting, making reproducibility difficult and increasing implementation barriers.

2. **Inconsistent Thresholds and Documentation**: Different institutions and projects use varied quality criteria without standardized rationale, leading to inconsistent sample acceptance/rejection decisions and difficulties comparing results across studies.

3. **Lack of Integrated Strain Typing**: While taxonomic identification alone is insufficient for strain discrimination and epidemiological tracking, integrating MLST typing requires additional setup and configuration beyond standard QC pipelines.

4. **Scalability for Batch Processing**: Processing large genomic datasets requires efficient parallelization, but most available tools require extensive manual orchestration.

5. **Missing Interpretability for Non-Specialists**: Clinical microbiologists and non-bioinformaticians need clear, actionable quality metrics without requiring deep understanding of sequencing technology or bioinformatics methodology.

BactScout addresses these gaps by providing:

- **Unified Pipeline**: Single entry point orchestrating read QC (Fastp), taxonomic profiling (Sylph), and strain typing (StringMLST) with transparent pass/fail criteria for each metric.

- **Configurable Thresholds**: Easily adjustable quality criteria via YAML configuration, enabling consistency within projects while allowing cross-project customization.

- **Informative Reporting**: Detailed per-sample quality summaries and batch statistics identifying problematic samples and systematic issues.

- **Parallel Processing**: Efficient multi-threaded execution processing hundreds of samples on typical compute infrastructure.

- **Reproducible Environment**: Integration with Pixi ensures deterministic dependency management across platforms.

BactScout is particularly valuable for:

- **Genome Sequencing Projects**: Researchers generating bacterial genome assemblies needing objective quality validation before assembly
- **Epidemiological Surveillance**: Public health labs tracking outbreak strains where ST information supplements species identification
- **Quality Assurance**: Sequencing facilities implementing standardized quality control workflows
- **Clinical Microbiology**: Diagnostic laboratories requiring reproducible, documented sample acceptance criteria

The software follows open-source best practices with comprehensive documentation, 114+ unit tests (76% code coverage), and continuous integration testing across multiple platforms.

# Key Features

## Quality Assessment Dimensions

BactScout evaluates bacterial sequencing data across four primary dimensions:

1. **Read Quality**: Percentage of bases with Phred quality ≥30 (Q30) and mean read length using Fastp post-trimming metrics

2. **Coverage Depth**: Estimated genome coverage calculated from read abundance using both Sylph's direct measurement and calculated estimates (total bases ÷ expected genome size)

3. **Species Purity and Identification**: Species detection via Sylph ANI-based profiling with contamination assessment (% reads assigned to non-dominant species)

4. **Strain Typing**: Multi-locus sequence typing (MLST) assignment via StringMLST when single-species samples identified

Each dimension produces PASS/WARNING/FAILED status with configurable thresholds and detailed explanatory messages.

## Modular Architecture

The codebase is organized as separate modules:

- `main.py`: Batch processing orchestrator for multiple samples
- `thread.py`: Individual sample processing coordination and QC result aggregation
- `collect.py`: Single-sample processing interface
- `software/`: External tool integrations (Fastp, Sylph, StringMLST)
- `summary.py`: Cross-sample result consolidation and statistics
- `util.py`: Formatting and output utilities

## Advanced Capabilities

- **Parallel Execution**: Thread pool-based sample processing with configurable concurrency
- **Flexible Input**: Support for multiple FASTQ naming conventions (\_R1/\_R2, \_1/\_2, both gzipped and uncompressed)
- **Batch Statistics**: Aggregated summary CSV with species distribution, coverage statistics, and failure analysis
- **MLST Integration**: Seamless species database mapping and automated ST assignment with novel ST detection

# Implementation

BactScout is implemented in Python 3.11+ using:

- **Typer**: Command-line interface framework with auto-generated help text
- **Rich**: Formatted terminal output with progress tracking
- **Pixi**: Cross-platform dependency management (Python 3.11+, Fastp v0.23.4, Sylph v0.13.2, StringMLST)

The pipeline processes each sample through these steps:

1. Extract paired-end FASTQ file locations from input directory
2. Run Fastp for read quality control and adapter trimming
3. Run Sylph for species identification and abundance profiling
4. Extract and evaluate Fastp and Sylph results against quality thresholds
5. Assign expected genome size and GC content from metrics database
6. Calculate coverage estimates (Sylph-based and read-count-based)
7. Run StringMLST for strain typing if single species detected
8. Evaluate all metrics to assign final PASS/WARNING/FAILED status
9. Write per-sample summary CSV and append to batch results

Results are written as:
- Per-sample directory: `{sample_id}/{sample_id}_summary.csv`
- Batch results: `final_summary.csv`
- Optional: Fastp HTML reports for individual read quality inspection

# Verification and Testing

BactScout includes 114 unit tests covering:

- CLI command parsing and validation
- FASTQ pair detection for various naming schemes
- Fastp result extraction and quality metric calculations
- Sylph output parsing and species abundance handling
- StringMLST invocation and ST assignment validation
- QC threshold evaluation and pass/fail logic
- Batch result aggregation and consistency

Tests achieve 76% code coverage with continuous integration via GitHub Actions (Ubuntu 22.04 and macOS latest), ensuring cross-platform compatibility. Parallel test execution via pytest-xdist reduces CI time by >50%.

# Performance

BactScout processes samples efficiently:

- Single sample (~1M reads): 5-15 minutes
- Batch (100 samples): 8-25 hours depending on read depth and thread count
- Typical resource usage: 2-8GB RAM, minimal disk I/O

The software scales to hundreds of samples when distributed across computing infrastructure.

# Applications

BactScout has been designed for several research contexts:

1. **Genome Assembly Projects**: Pre-assembly quality filtering to identify candidates suitable for de novo assembly
2. **Outbreak Investigation**: Rapid strain discrimination via ST assignment for epidemiological surveillance
3. **Sequencing QA/QC**: Standardized acceptance criteria for diagnostic laboratory workflows
4. **Research Cohorts**: Consistent sample quality documentation for multi-center studies

# Documentation and Community

Comprehensive documentation is available at GitHub Pages including:

- Installation guide with platform-specific instructions
- Usage guide for batch and single-sample processing
- Quality control interpretation guide
- API reference and troubleshooting guide
- Contributing guidelines for community development

# Acknowledgements

BactScout integrates three excellent open-source bioinformatics tools: Fastp [@chen2018fastp], Sylph [@unckless2023sylph], and StringMLST [@datta2016stringmlst]. Development was supported by automated testing and documentation frameworks including pytest, pytest-xdist, MkDocs Material, and GitHub Actions.

# References
