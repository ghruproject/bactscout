---
title: 'BactScout: A Python pipeline for quality assessment of bacterial sequencing reads'
tags:
  - Python
  - bioinformatics
  - quality control
  - bacterial genomics
  - taxonomic profiling
  - genome sequencing
authors:
  - name: Nabil-Fareed Alikhan
    orcid: 0000-0002-1243-0767
    affiliation: "1,2,4" # (Multiple affiliations must be quoted)
  - name: Varun Shamanna
    orcid: 0000-0003-2775-2280
    affiliation: "3,4"
  - name: Natacha Couto
    orcid: 0000-0002-9152-5464
    affiliation: "5,6"
  - name: June Gayeta
    orcid: 0000-0001-6339-2476
    affiliation: "4,7"
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
  - index: 5
    name: Instituto de Microbiologia, Faculdade de Medicina, Universidade de Lisboa, Lisbon, PT
  - index: 6
    name: Cardiff Metropolitan University, Cardiff, UK
  - index: 7
    name: Research Institute for Tropical Medicine, Department of Health, Muntinlupa City, Philippines
date: 2 October 2026
bibliography: paper.bib
---

# Summary

BactScout assesses raw sequencing reads from cultured bacterial isolates before assembly or other downstream analysis. Its short-read workflow combines read-quality metrics from fastp, species-level profiling and coverage estimates from Sylph, and sequence typing with stringMLST when a scheme is configured. Its long-read workflow combines read statistics from Nanoq with Sylph taxonomic and coverage estimates. For both workflows, configurable thresholds classify samples as PASSED, WARNING, or FAILED and report the measurements and reasons behind each result. Users can run one sample or process a directory and aggregate sample summaries as CSV files. BactScout is intended for bacterial genomics and public-health surveillance teams that need a repeatable way to review read quality, taxonomic composition, coverage, and typing results before deciding which samples to analyse further.

# Statement of need

Read quality control for cultured bacterial isolates includes both technical measurements, such as read length and quality, and biological checks, such as taxonomic composition and expected sequencing depth. A read-level quality report can show whether a file has unusual quality scores or base composition, but it does not by itself combine those observations with an isolate's taxon, expected genome size, or typing result. Laboratories often need to interpret reports from several tools and apply local criteria before deciding whether to proceed with assembly or surveillance analysis.

BactScout provides that sample-level step. It runs established analysis tools, applies configurable thresholds to their results and produces per-sample and batch summaries with status fields and diagnostic reasons. The target users are researchers and public-health laboratories processing short- or long-read bacterial isolate data. A sample-level warning is intended to prompt review; it does not replace laboratory judgement or downstream assessment of assemblies and genomic analyses.

# State of the field

FastQC reports technical read-quality checks, while fastp supplies read-level metrics and preprocessing functions. Kraken 2 and Sylph provide taxonomic classification or profiling from sequence reads. QualiBact provides species-specific quality criteria for genome assemblies; BactScout uses selected species metrics when assessing reads before assembly. Integrated workflows such as Bactopia and TORMES span read QC, assembly, and downstream bacterial genome analysis [@petit2020bactopia; @quijada2019tormes]. BactScout has a narrower role: it combines read metrics, taxonomic results, coverage estimates, and optional sequence typing into a sample-level result before downstream analysis. It uses established tools for these analyses and can serve as a separate read-review stage alongside broader workflows. [@andrews2010fastqc; @chen2018fastp; @wood2019kraken2; @shaw2025sylph; @steinig2022nanoq; @gupta2017stringmlst; @qualibact]

The contribution is an integration and decision layer for cultured-isolate workflows. Keeping read assessment in a separate package allows laboratories to apply the same criteria while retaining their own assembly and downstream analysis workflows. An implementation confined to one end-to-end pipeline would couple that assessment to a particular workflow environment. BactScout instead exposes commands and CSV summaries that can be used independently, at the cost of maintaining its own tool adapters and configuration. Users can adjust thresholds and inspect the reported metrics and reasons. QualiBact supplies species-aware QC guidance used by the project [@qualibact].

# Software design

BactScout separates tool execution and output parsing from metric aggregation and QC evaluation. This lets the pipeline reuse established tools while applying its own configurable decision rules. The code exposes separate short-read and long-read command paths because the platforms provide different measurements: the short-read path reports fastp metrics and may report MLST, whereas the long-read path reports Nanoq read statistics and platform-specific quality and N50 checks. The paths therefore write distinct summary schemas rather than forcing unlike measurements into the same fields.

Coverage can be estimated from Sylph or calculated from total read bases and an expected genome size when that value is available. The QC logic records estimates and flags before deriving the overall status. In long-read runs, the absence of both coverage estimates is a failure; if expected genome size is unavailable but Sylph reports coverage, the calculated estimate is flagged as unavailable and the result is a warning unless another metric fails. Configuration files keep threshold choices and database locations outside the evaluation code. Per-sample CSV records can be combined into a short-read or long-read batch summary, while tool reports and logs remain available for inspection. The repository includes a Pixi lockfile and container recipe for setting up the software environment. These choices make the criteria and reported reasons inspectable, while requiring downstream users to account for the two output schemas when combining short- and long-read results.

# Research impact statement

Within the NIHR Global Health Research Unit, BactScout is used in sentinel surveillance to screen raw reads before assembly QC and downstream Kleborate analysis [@lam2021kleborate]. During a user-reported long-read QC run, a sample with 38 reads had no coverage estimate but was not classified as FAILED. This use exposed a gap in the decision logic; release 1.4.2 changed the long-read evaluation so that absence of both Sylph and calculated coverage estimates yields FAILED [@bactscout]. This case records a specific example of use informing a software change.

QualiBact recommends BactScout as a complementary read-level QC tool [@qualibact]. A Galaxy CollaborationFest team reported work to wrap and extend BactScout as a QC subworkflow for public-health pathogen genomics [@galaxy2026]. The CoFest report describes this as activity in progress. <!-- Author query: add the GHRU workflow period and any further verifiable adoption details that can be shared. -->

# Availability

Source code and documentation are available at [https://github.com/ghruproject/bactscout](https://github.com/ghruproject/bactscout) under GPL-3.0. The cited release is v1.4.2 [@bactscout]. <!-- Add the version-specific archive DOI after the reviewed release is archived. -->

# Acknowledgements

This work was supported by the National Institute for Health Research (NIHR133307). We thank contributors from the NIHR Global Health Research Unit on Genomics and enabling data for the Surveillance of AMR for feedback during design and testing. <!-- Author query: state whether the funder had a role in the work or manuscript preparation. -->

# Competing interests

The authors declare no competing interests.

# AI usage disclosure

**Draft, pending author confirmation:** During this JOSS preparation, Codex using GPT-6 and delegated agents using GPT-6 Luna assisted with repository review, manuscript and documentation drafting, reference checks, a Q30 threshold correction and regression tests. GitHub Copilot and Codex were also used during earlier development; the historical model versions and scope remain to be confirmed. Automated checks were run during preparation. Before submission, the authors must complete the tool-use inventory and confirm their own review, editing and validation of AI-assisted outputs and responsibility for the core design decisions. The authors remain responsible for the final paper and software.

# References
