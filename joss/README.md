# JOSS Paper Submission

This directory contains the paper submission for the Journal of Open Source Software (JOSS).

## Files

- **`paper.md`**: Main paper manuscript following JOSS format
  - Metadata section with authors, affiliations, and tags
  - Summary and Statement of Need sections
  - Key Features and Implementation details
  - Verification and Testing information
  - Word count: ~1000 words (within JOSS guidelines of 250-1000 words)

- **`paper.bib`**: BibTeX bibliography file with references
  - Citations to core tools (Fastp, Sylph, StringMLST)
  - Dependencies (Typer, Rich, Pixi, pytest, MkDocs)
  - Scientific references (MLST, ANI)

## Submission Checklist

Before submitting to JOSS, verify:

- [x] Paper is 250-1000 words (currently ~1000)
- [x] Authors and affiliations are listed correctly
- [x] YAML metadata is valid
- [x] Bibliography is in BibTeX format
- [x] All in-text citations match bibliography entries
- [x] Software repository has required documentation
- [x] Code has tests (114 tests, 76% coverage)
- [x] License is OSI-approved (GPL v3)
- [x] Software is not just a wrapper around other software

## Repository Requirements Met

- ✅ Open source software (GPL v3 license)
- ✅ GitHub repository: https://github.com/ghruproject/bactscout
- ✅ Comprehensive documentation at GitHub Pages
- ✅ Unit tests with >70% coverage
- ✅ Continuous Integration (GitHub Actions)
- ✅ Clear Statement of Need
- ✅ Unique contributions beyond tool integration

## Building the PDF Locally

Option 1: Using Docker (recommended)
```bash
docker run --rm \
  --volume $PWD/joss:/data \
  --user $(id -u):$(id -g) \
  --env JOURNAL=joss \
  openjournals/inara
```

Option 2: Using GitHub Actions
- Push to GitHub and check Actions tab for generated PDF

## Key Paper Features

### Scope Coverage
- Non-specialist accessible summary of BactScout's purpose
- Detailed Statement of Need highlighting research context
- Concrete applications and use cases
- Clear technical implementation details

### Research Applications
- Genome assembly quality control
- Outbreak investigation and epidemiological surveillance
- Sequencing QA/QC for diagnostic labs
- Multi-center research cohort studies

### Dependencies Documented
- Fastp: Read quality control
- Sylph: Taxonomic profiling (ANI-based)
- StringMLST: Strain typing

### Innovation Points
- Unified workflow integrating three tools
- Configurable quality thresholds with clear rationale
- Comprehensive testing and documentation
- Modular architecture for extensibility
- Batch processing with parallel execution

## JOSS Submission URL

When ready, submit at: https://joss.theoj.org/

## Questions?

Refer to:
- JOSS submission guide: https://joss.readthedocs.io/en/latest/submitting.html
- JOSS paper format: https://joss.readthedocs.io/en/latest/paper.html
- Example paper: https://joss.readthedocs.io/en/latest/example_paper.html
