---
title: 'BactScout: A reproducible Python pipeline for bacterial genome sequencing quality control'
tags:
  - Python
  - bioinformatics
  - quality control
  - bacterial genomics
  - taxonomic profiling
  - genome assembly
authors:
  - name: Nabil-Fareed Alikhan
    orcid: 0000-0002-1243-0767
    affiliation: "1,2,4" # (Multiple affiliations must be quoted)
  - name: Varun Shamanna
    orcid: 0000-0003-2775-2280
    affiliation: "3,4"
  - name: Natacha Couto
    orcid: 0000-0002-9152-5464
    affiliation: "1,2,4"
  - name: GHRU2 Project Contributors
    affiliation: 4
  - name: David M Aanensen
    orcid: 0000-0001-6688-0854
    affiliation: "1,2,4"
affiliations:
  - index: 1
    name: Centre for Genomic Pathogen Surveillance, University of Oxford, United Kingdom
  - index: 2
    name: WHO Collaborating Centre on Genomic Surveillance of AMR, University of Oxford, United Kingdom
  - index: 3
    name: Central Research Laboratory, KIMS, Bengaluru, India
  - index: 4
    name: NIHR Global Health Research Unit on Genomics and enabling data for the Surveillance of AMR
date: 3 November 2025
bibliography: paper.bib
---

# Summary

BactScout is a Python-based pipeline for rapid, standardized quality assessment and taxonomic profiling of raw read data from sequencing cultured bacterial isolates. It integrates tools like Fastp for read quality control, Sylph for species-level taxonomic profiling, and StringMLST for multi-locus sequence typing into a single, reproducible workflow.  Designed for scientists working with large-scale bacterial genome data, BactScout provides interpretable quality metrics across read quality, species purity, GC content, and strain typing. These outputs support downstream applications such as genome assembly, resistance prediction, mapping, variant calling, and phylogenetic analysis. The pipeline features a modular and extensible architecture with configurable quality thresholds, parallel sample processing, and detailed per-sample and batch-level reporting.

BactScout emphasizes reproducibility and ease of use through deterministic, containerized environments managed by Pixi, ensuring consistent results across platforms. By combining quality control, taxonomic profiling, and strain typing in a unified, automated framework, BactScout reduces manual effort and improves standardization in bacterial genomics workflows.

# Statement of need

Quality assessment of bacterial sequencing data is a critical and often under-standardized step in genomic analysis pipelines, particularly for applications requiring high-confidence downstream analysis. Common challenges include contamination, low sequencing yield, poor read quality, and variable fragment lengths. While existing tools can report these metrics, interpreting their biological relevance typically requires manual assessment that depends on the species and sequencing context. This leads to inconsistent quality decisions and reduced reproducibility across projects and laboratories.

Existing tools such as *FastQC* [@andrews2010fastqc] provide detailed summaries of read-level sequencing quality but do not assess biological metrics like species purity or strain identity. Similarly, taxonomic profilers such as Kraken2 [@lu2022kraken] require additional integration and interpretation to be useful in a quality control context, with species-specific decisions often left to the discretion of the operator. BactScout bridges this gap by combining technical and biological quality metrics within a single, reproducible workflow, automatically generating pass/fail assessments informed by species-aware benchmarks defined in [QualiBact](https://happykhan.github.io/qualibact/).

The pipeline is designed for routine isolate sequencing tasks commonly encountered in public health surveillance and clinical microbiology, where rapid and reproducible assessment of sequencing quality is essential prior to downstream analyses such as genome assembly or antimicrobial resistance prediction. By formalizing quality interpretation and applying species-aware thresholds, BactScout minimizes subjective decision-making and enhances consistency across bacterial genomics workflows. It serves as a rapid, automated screening step to identify high-quality samples suitable for deeper analyses, complementing more comprehensive assembly evaluation pipelines. BactScout was developed to meet the practical needs of scientists and has been successfully deployed within the Global Health Research Unit (GHRU) on Genomic Surveillance of Antimicrobial Resistance, demonstrating its robustness and scalability in high-throughput laboratory environments.

# Implementation
BactScout automates post-sequencing quality control by integrating *Fastp* [@chen2018fastp], *Sylph* [@unckless2023sylph], and *StringMLST* [@datta2016stringmlst] to identify problematic samples rapidly. It applies a configurable two-tier threshold system (WARN/FAIL) to classify samples as PASS, WARNING, or FAIL, summarizing results per sample and across batches. By combining standardized thresholds with species-aware criteria, BactScout streamlines decision-making and enhances reproducibility in bacterial WGS analysis.

BactScout is implemented in modern Python (3.11+) as a compact, modular pipeline designed for reproducibility and scalability across environments. It follows a CLI-first design (via *Typer*) with distinct modules for tool wrappers, metrics aggregation, and QC decision logic. External tool adapters (for *Fastp*, *Sylph*, *StringMLST*) isolate dependencies, ensuring a stable command-line and output schema. BactScout is packaged with Pixi and container images for reproducible deployment. It supports standalone use or integration within workflow managers such as Nextflow, job arrays, or GNU Parallel, ensuring consistent execution from laptops to HPC environments. The repository includes manifests and container recipes to facilitate reproducible builds.

Runtime behavior is configured through a single YAML file defining database paths, defaults, and quality thresholds. A consistent two-tier WARN/FAIL model allows users to adjust sensitivity to their context (e.g., stricter for clinical pipelines, relaxed for research). Each run generates per-sample directories containing structured CSV and JSON summaries, tool logs, and reports. The summaries include stable, well-documented field names for easy integration into LIMS or dashboards. A `summary` command aggregates all per-sample outputs into a batch-level report (`final_summary.csv`). The typical runtime for a 2 million read sample is 30-60 seconds with less than 8 GB RAM on one thread, scaling linearly with sample number.

The codebase follows a modular structure with distinct submodules for I/O, quality assessment, and result aggregation. Automated tests (~75% code coverage) validate parsing, schema stability, and cross-platform compatibility via GitHub Actions. The project includes contribution guidelines, changelog, and code of conduct. New modules follow a simple results-dictionary contract to maintain compatibility.

# Availability
Source code and documentation are available at [https://github.com/ghruproject/bactscout](https://github.com/ghruproject/bactscout) under the GPLv3 license. Installation instructions, usage examples, and container images are provided via the project’s documentation site. Example datasets and expected outputs are included for testing and demonstration purposes in the documentation. 

# Acknowledgements

This work was supported by National Institute for Health Research (NIHR133307). BactScout builds upon three outstanding open-source tools: **Fastp** [@chen2018fastp], **Sylph** [@unckless2023sylph], and **StringMLST** [@datta2016stringmlst].  
We thank contributors from the **NIHR Global Health Research Unit on Genomics and enabling data for the Surveillance of AMR** for feedback during design and testing, and the open-source community for providing the foundational libraries and infrastructure enabling this work.

# References