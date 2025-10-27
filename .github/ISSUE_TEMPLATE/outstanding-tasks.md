---
name: Outstanding Tasks & Development Roadmap
about: Track development priorities and improvements for BactScout
title: "Outstanding Tasks & Development Roadmap"
labels: documentation, enhancement, maintenance
assignees: ghruproject
---

# BactScout Development Roadmap

This issue tracks outstanding tasks and improvements needed for the BactScout project. Please comment or create sub-issues for any additional work required.

## Documentation

- [ ] Expand troubleshooting guide with more edge cases
- [ ] Add API documentation for programmatic usage
- [ ] Create video tutorials for common workflows
- [ ] Document database update procedures
- [ ] Add architecture diagram to design documentation
- [ ] Create developer contribution guidelines
- [ ] Document performance tuning options

## Test Coverage

- [ ] Increase coverage for `bactscout/collect.py` (currently 65%)
- [ ] Increase coverage for `bactscout/software/run_fastp.py` (currently 58%)
- [ ] Add integration tests for end-to-end workflows
- [ ] Add performance/benchmarking tests
- [ ] Test error handling paths more thoroughly
- [ ] Add tests for edge cases (empty files, malformed input, etc.)
- [ ] Mock external tool calls for faster unit tests

## Features & Enhancements

- [ ] Add support for long-read sequencing data (PacBio, Nanopore)
- [ ] Implement multi-species contamination reporting
- [ ] Add real-time progress reporting for large batch runs
- [ ] Support for custom database creation
- [ ] Batch processing with automatic retries
- [ ] Web UI/Dashboard for results visualization
- [ ] Integration with common bioinformatics platforms (Galaxy, Nextflow)
- [ ] Add phylogenetic tree generation for multiple samples
- [ ] Customizable quality thresholds per species

## Code Quality & Refactoring

- [ ] Extract `qc` command logic to separate `bactscout/qc.py` module (like `collect.py`)
- [ ] Extract `summary` command logic to separate `bactscout/summary.py` module
- [ ] Refactor `thread.py` - currently 210 statements, split into smaller functions
- [ ] Add comprehensive type hints throughout codebase
- [ ] Implement dependency injection for better testability
- [ ] Consider using dataclasses for result objects
- [ ] Review and refactor error handling for consistency
- [ ] Add structured logging instead of print statements

## Performance Optimization

- [ ] Profile and optimize critical paths in `thread.py`
- [ ] Implement streaming for large FASTQ file processing
- [ ] Cache species lookup results
- [ ] Optimize database queries
- [ ] Consider using NumPy/Pandas for statistical operations
- [ ] Implement lazy loading for heavy dependencies
- [ ] Benchmark against similar tools

## Security & Maintenance

- [ ] Security audit of dependency tree
- [ ] Add code signing for releases
- [ ] Implement SBOM (Software Bill of Materials)
- [ ] Review and update dependencies quarterly
- [ ] Add pre-commit hooks for local development
- [ ] Implement automated security scanning
- [ ] Document security policy for reporting vulnerabilities
- [ ] Add input validation hardening

## Bug Fixes & Known Issues

- [ ] ⚠️ Sylph parameter handling in main.py (fixed: `threads=False` → `threads=1`)
- [ ] ⚠️ Coverage estimation calculation (fixed: `coverage_alt_estimate` was 0)
- [ ] ⚠️ Species detection message (fixed: showing "Multiple" for single species)
- [ ] Fix pre-existing lint errors in `handle_species_coverage()`
- [ ] Improve `extract_species_from_report()` error handling for empty files
- [ ] Add graceful handling for missing Sylph database

## User Experience

- [ ] Add `--dry-run` flag to preview operations without running
- [ ] Implement better error messages with suggested fixes
- [ ] Add `--resume` flag to continue interrupted batch jobs
- [ ] Create sample datasets for testing and tutorials
- [ ] Add configuration file validation with helpful error messages
- [ ] Implement progress bar for preflight checks
- [ ] Add `--quiet` and `--verbose` output modes

## DevOps & CI/CD

- [ ] Set up automated dependency updates (Dependabot)
- [ ] Add container image builds for Docker Hub
- [ ] Create Conda package for bioconda-channel
- [ ] Set up automatic releases to PyPI
- [ ] Add performance regression testing
- [ ] Implement code coverage reporting trends
- [ ] Add linting to pull request checks (already implemented ✅)
- [ ] Create deployment guides for different environments

## Dependencies & Versions

- [ ] Evaluate and document minimum Python version requirements
- [ ] Test compatibility with Python 3.12+
- [ ] Review and pin compatible versions for all dependencies
- [ ] Create separate dev/test/runtime dependency groups
- [ ] Document optional dependencies for advanced features
- [ ] Set up automated testing across Python versions

## Community & Contribution

- [ ] Create CONTRIBUTING.md with contribution guidelines
- [ ] Set up discussion forums for user support
- [ ] Create issue templates for bug reports and feature requests
- [ ] Establish code review standards and process
- [ ] Create development environment setup guide
- [ ] Set up community chat (Discord/Slack)

## Documentation Quality Improvements

- [ ] Add cross-references between documentation pages
- [ ] Create quick-start guide for common scenarios
- [ ] Add FAQ section with real user questions
- [ ] Create comparison with similar tools
- [ ] Document output format specifications
- [ ] Add data format specifications for inputs

## Monitoring & Analytics

- [ ] Add usage analytics (opt-in)
- [ ] Track error rates and common failures
- [ ] Monitor database performance metrics
- [ ] Create dashboard for tool usage patterns
- [ ] Add telemetry for improvement feedback

---

## How to Contribute

1. **Pick a task** - Choose an item that interests you
2. **Create a sub-issue** - If the task needs more detail
3. **Submit a PR** - Link your PR to this issue
4. **Request review** - Tag maintainers for feedback

## Current Status

- **Last Updated**: 2025-10-27
- **Total Tasks**: 75+
- **Completed**: ✅ Multiple bug fixes, CI/CD improvements, test optimizations
- **In Progress**: Code refactoring, performance optimization
- **Priority**: High (3), Medium (3), Low (3)

---

**Feel free to comment with suggestions or volunteer for tasks!**
