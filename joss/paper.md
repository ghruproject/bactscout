---
title: 'BactScout: A Python pipeline for quality assessment and taxonomic profiling of bacterial sequencing data'
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
    affiliation: "1, 3" # (Multiple affiliations must be quoted)
  - name: Varun Shamanna
    orcid: 0000-0003-2775-2280
    affiliation: 2
  - name: GHRU Project Contributors
    affiliation: 3
affiliations:
  - index: 1
    name: Centre for Genomic Pathogen Surveillance, University of Oxford, United Kingdom
  - index: 2
    name: KIMS
  - index: 3
    name: Global Healthcare and Research Unit
date: 3 November 2025
bibliography: paper.bib
---

# Summary

BactScout is a Python-based pipeline for rapid, standardized quality assessment and taxonomic profiling of sequencing data from cultured bacterial isolates. It integrates tools like Fastp for read quality control, Sylph for species-level taxonomic profiling, and StringMLST for multi-locus sequence typing into a single, reproducible workflow. BactScout evaluates sequencing data across multiple quality dimensions—read quality, coverage depth, species purity, GC content, and strain typing—producing clear, interpretable quality metrics for downstream applications such as genome assembly, antimicrobial resistance prediction, genotyping, and phylogenetic inference.

The pipeline features a modular and extensible architecture with configurable quality thresholds, parallel sample processing, and detailed per-sample and batch-level reporting. A single command can process hundreds of samples, automatically generating summaries and visual outputs suitable for laboratory or high-performance computing environments.

BactScout emphasizes reproducibility and ease of use through deterministic, containerized environments managed by Pixi, ensuring consistent results across platforms. By combining quality control, taxonomic profiling, and strain typing in a unified, automated framework, BactScout reduces manual effort and improves standardization in bacterial genomics workflows.

# Statement of need

Quality assessment of bacterial sequencing data is a critical and often under-standardized step in genomic analysis pipelines, particularly for applications requiring high-confidence genome assemblies. Common challenges include contamination, low sequencing yield, poor read quality, and variable fragment lengths. While existing tools can report these metrics, interpreting their biological relevance typically requires manual assessment that depends on the species and sequencing context. This leads to inconsistent quality decisions and reduced reproducibility across projects and laboratories.

BactScout addresses this gap by providing an automated, standardized workflow for assessing sequencing quality of bacterial isolates. It integrates established, fast-performing tools with relatively low memory and CPU requirements to evaluate read quality, taxonomic purity, and strain identity, applying clear pass/fail criteria based on configurable thresholds and species-specific quality benchmarks (as defined in [QualiBact](https://happykhan.github.io/qualibact/)).

The pipeline is designed for typical isolate sequencing tasks encountered in public health surveillance and clinical microbiology, where rapid and reproducible decisions on sample quality are essential before downstream analyses such as genome assembly or resistance prediction. By formalizing interpretation and integrating species-aware thresholds, BactScout reduces subjective decision-making and improves consistency in bacterial genomics quality control. We invision BactScout as an initial rapid screening step to identify high-quality samples suitable for further analysis, working along side more comprehensive pipelines, which would explore the genome assembly quality in greater depth.


# BactScout Development

BactScout is implemented in modern, idiomatic Python (targeting Python >= 3.11) and organised as a compact, modular CLI-first pipeline to make installation, automation, and integration straightforward. The project is intentionally pragmatic: it prioritises reproducibility, stable machine-readable outputs, and predictable resource use so the same checks can be applied on a laptop, an institutional cluster, or in cloud environments.

Architecture and packaging
-------------------------
The codebase separates concerns into small, well-delineated modules. A lightweight CLI (implemented with Typer) exposes a small set of commands (`collect`, `summary`, `qc`), while the core orchestration layer implements the per-sample processing pipeline. Adapter modules encapsulate external tools (Fastp, Sylph and StringMLST), so the pipeline’s logic focuses on metrics aggregation and quality decision-making rather than tool internals. This approach keeps the public contract (CLI flags, CSV/JSON outputs) stable while allowing internal replacements or extensions.

Packaging is designed for reproducibility. The repository provides Pixi manifests and example Docker/Singularity images that bundle system libraries and the third‑party binaries required to run BactScout. Users may run BactScout via containers (recommended for reproducibility) or install it into a site Python environment when container support is not available.

Configuration and thresholds
---------------------------
Runtime behaviour is driven by a single YAML configuration (`bactscout_config.yml`). This file centralises database paths, resource defaults and quality thresholds. The pipeline uses a two-tier threshold model (WARN and FAIL) for most metrics: WARN denotes borderline behaviour that merits inspection, and FAIL denotes a critical condition that prevents automatic acceptance. The explicit two-tier model helps laboratories tune sensitivity for different use-cases—for example, clinical surveillance pipelines can tighten FAIL thresholds while research studies may accept more WARNING results.

Quality decisions are exported as canonical status fields in the per-sample summary (for example, `read_q30_status`, `coverage_status`, `contamination_status` and `mlst_status`). Each status field is accompanied by a human-readable message explaining why the metric passed, warned or failed. This stable results contract makes it straightforward to integrate BactScout outputs into LIMS, dashboards, or downstream analysis scripts.

Outputs and data model
----------------------
Each `collect` invocation produces a self-contained sample directory containing a single-row summary CSV and an optional JSON copy, fastp HTML reports, Sylph outputs, MLST outputs when applicable, and logs. The summary CSV uses canonical, well-documented column names for coverage estimates, status flags, and explanatory messages. A separate `summary` command aggregates per-sample summaries into a batch-level CSV suitable for downstream analysis or archival. Keeping one directory per sample minimises filesystem contention when scaling and simplifies retries and per-sample inspection.

Coverage is reported from two complementary sources: Sylph’s direct coverage estimate and a calculated estimate computed as total_bases_postfilter / expected_genome_size (coverage = total_bases / genome_size). Emitting both estimates allows users to cross-check Sylph’s model-based estimate against the simple reads/genome-size calculation and helps surface discrepancies caused by contamination or misidentified references.

Scalability and orchestration
----------------------------
BactScout treats each sample as an independent unit of work. Horizontal scaling is therefore straightforward: many concurrent `bactscout collect` runs can be dispatched using GNU Parallel, scheduler job-arrays, or workflow engines such as Nextflow. The repository includes a Nextflow example demonstrating production-friendly patterns: node-local staging of inputs, containerised execution, per-sample `publishDir` semantics, and a small final aggregation step that runs `bactscout summary` to assemble a `final_summary.csv`.

For single-node runs, the `--threads` option controls per-sample parallelism and should be set so the sum of threads across concurrent jobs does not exceed the available physical cores. On clusters, we recommend one process per job with tuned `--threads` and memory limits; use job arrays or workflow engines’ native concurrency controls to cap the number of simultaneous tasks. Practical tips: stage compressed FASTQs to node-local scratch, avoid creating millions of tiny files on metadata-limited filesystems, and publish per-sample outputs atomically to reduce contention.

Testing, validation, and CI
--------------------------
The project ships with small mock datasets and unit tests that validate parsing, header parity and the shape of programmatic outputs. Continuous integration runs these tests across supported platforms (Linux and macOS) and focuses on contract stability (column names, JSON schema, status semantics) rather than re-running heavy third-party analyses in CI. This testing strategy keeps CI fast and reliable while ensuring downstream consumers of the pipeline can depend on stable outputs.

Operational observability and tuning
----------------------------------
For production deployments, BactScout can record lightweight resource telemetry (CPU usage, peak and average memory, and elapsed time) when invoked with `--report-resources`. Aggregating these metrics across representative samples helps teams choose conservative defaults for `--threads` and per-job memory and identify whether workloads are CPU- or I/O-bound. The pipeline retains per-sample logs and outputs by default to aid post-mortem debugging and reproducible reruns of failed samples.

Extensibility and contributions
------------------------------
The codebase is intentionally small and modular to lower the barrier to contribution. New analysis modules should implement the same compact results dictionary contract used by existing modules so that outputs remain consistent. The repository includes contribution guidelines, a changelog, and a code of conduct; contributors are asked to include unit tests and documentation for new features.

Documentation and reproducibility
--------------------------------
Extensive documentation is included under `docs/` and covers installation, configuration, the output schema, and recommended run patterns (local parallelism, job arrays, and Nextflow). Example Pixi manifests and the Nextflow example provide production-ready templates. Together, pinned container images, example configs, and clear documentation aim to make analytical runs reproducible across sites and over time.

License and provenance
---------------------
BactScout is released under the GPLv3 license. The repository includes authorship and bibliographic metadata to facilitate citation. The aim is to provide laboratories with a reproducible, auditable screening step that complements downstream assembly, typing, and resistance-detection workflows.

In summary, BactScout is a compact, configurable and reproducible screening tool designed to slot into bacterial genomics pipelines: it delivers clear PASS/WARNING/FAIL decisions, stable machine-readable outputs, and an explicit scaling story so laboratories can apply the same checks to small or large cohorts with minimal operational overhead.

# Tools Utilized in BactScout

BactScout orchestrates three primary external tools to evaluate sequencing quality and taxonomic composition (Table 1).

| Tool | Function | Quality Dimension |
|------|-----------|------------------|
| **Fastp** | Read-level quality control and adapter trimming | Read quality |
| **Sylph** | Taxonomic profiling and species purity estimation | Species identification |
| **StringMLST** | Multi-locus sequence typing (MLST) assignment | Strain typing |

Each module outputs standardized JSON or tabular results that are parsed and evaluated against BactScout’s threshold schema. Quality decisions (PASS/WARNING/FAIL) are derived from metrics such as:
- Mean Q30 score and read length (Fastp)
- Genome coverage and species composition (Sylph)
- MLST type validity and completeness (StringMLST)

Default thresholds are defined in YAML configuration files and can be customized to project or organism-specific standards.

# Quality Assessment and Reporting

BactScout performs quality evaluation in four primary domains:

1. **Read Quality:** Calculates mean read length and percentage of bases \(\geq Q30\) from Fastp outputs.  
2. **Coverage Depth:** Estimates genome coverage both from read counts and Sylph-derived genome size.  
3. **Species Purity:** Quantifies dominant species proportion and flags cross-species contamination.  
4. **Strain Typing:** Runs StringMLST when a single dominant species is detected to validate strain-level assignment.

Each sample is assigned an overall **status**—PASS, WARNING, or FAIL—with explanatory notes for each metric.  
Reports include:
- **Per-sample CSV summaries** with metric breakdowns  
- **Batch-level summaries** aggregating performance across all samples  
- **Optional Fastp HTML reports** for visual inspection  

Outputs are human-readable and machine-parseable, facilitating integration with LIMS systems or downstream pipelines such as **Nextflow**.

# Applications

BactScout is applicable across multiple domains:

- **Genome assembly projects** – Pre-assembly QC to identify high-quality inputs  
- **Epidemiological surveillance** – Rapid strain verification and contamination detection  
- **Sequencing QA/QC** – Standardized acceptance criteria for clinical or public health laboratories  
- **Multi-center research cohorts** – Harmonized quality reporting across institutions  

By producing interpretable, standardized outputs, BactScout helps ensure that only high-quality, biologically relevant sequencing data progress to downstream analysis.

# Source Code and Documentation

Source code for **BactScout** is available at [https://github.com/ghruproject/bactscout](https://github.com/ghruproject/bactscout) under the **GPLv3 License**.  
Comprehensive documentation—covering installation, usage, configuration, and troubleshooting—is hosted on GitHub Pages.  
It includes API references, example datasets, and developer contribution guidelines.

# Acknowledgements

BactScout builds upon three outstanding open-source tools: **Fastp** [@chen2018fastp], **Sylph** [@unckless2023sylph], and **StringMLST** [@datta2016stringmlst].  
We thank contributors from the **Global Health Research Unit (GHRU)** for feedback during design and testing, and the open-source community for providing the foundational libraries and infrastructure enabling this work.

# References