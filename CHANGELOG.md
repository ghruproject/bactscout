# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Corrected short-read Q30 classification so values between the fail and warning cutoffs yield `WARNING`, with boundary and legacy-percentage regression tests.
- Updated the JOSS manuscript, references and author metadata, and added reviewer instructions and a submission checklist.
- Reconciled documentation with the current CLI, configuration and summary fields, and marked download-dependent cache checks as integration tests.

## [1.4.2] - 2026-09-24
- Fixed long-read QC so samples fail when neither Sylph nor the expected-genome-size calculation can produce a coverage estimate.
- Added explicit diagnostic messages when taxon, contamination, or coverage results are unavailable.

## [1.4.1] - 2026-09-05
- Fixed false contamination failures for clean single-species samples by using Sylph's taxonomic abundance rather than treating unclassified sequence as another species.
- Collapsed multiple Sylph reference rows for the same species before calculating species purity.
- Fixed the Docker image build by making BactScout's package metadata available before running preflight checks.

## [1.3.0] - 2026-06-02
- Added a new `bactscout long` command group with `qc`, `collect`, `summary`, and `preflight` subcommands.
- Added long-read QC using `nanoq` for ONT and PacBio HiFi reads.
- Added single-end Sylph execution support for long-read taxonomic profiling and coverage estimation.
- Added `bactscout_long_config.yml` and a separate `final_summary_long.csv` output path for long-read runs.
- Added targeted tests for long-read evaluation, batch discovery, collection, summary generation, and Sylph single-end execution.
- Added long-read documentation, output format reference updates, JOSS paper updates, and a Slurm validation report.

## [1.2.0]
- Renamed coverage-related output fields to canonical keys, including `coverage_estimate_sylph` and `coverage_estimate_qualibact`.

## [1.1.2]
- Initial public release.
- Added the core QC pipeline built around Fastp, Sylph, and StringMLST.
- Added summary and reporting features.
- Added Pixi environment support.
