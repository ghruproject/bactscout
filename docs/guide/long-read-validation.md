# Long-read validation

This page documents the reproducible validation workflow for the long-read QC path.

## Scope

The validation matrix for the initial long-read PR is:

- ONT only
- one good single-species dataset
- one bad single-species dataset
- one 90/10 mixed-species dataset
- one 80/20 mixed-species dataset

The committed automation lives under `scripts/long_read_validation/`.

## Reproducibility assets

- `setup_badread_env.sh` creates an isolated Badread environment outside Pixi
- `download_ncbi_genomes.py` downloads reference genomes from NCBI over HTTPS
- `run_long_read_validation.slurm` drives the full simulation and QC workflow on Slurm

## Expected outcomes

- the good ONT sample should pass long-read QC
- the bad ONT sample should fail or warn on read quality and/or N50
- the 90/10 mixed sample should produce a contamination warning
- the 80/20 mixed sample should produce a contamination failure

## Report

The execution report for the cluster run is stored in `LONGREAD_VALIDATION_REPORT.md` at the repository root.