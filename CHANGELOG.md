# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
