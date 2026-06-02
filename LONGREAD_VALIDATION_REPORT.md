# Long-read validation report

## Status

Validation scripts have been added and exercised on the cluster.

Successful Slurm validation run:

- job id: `20689557`
- script: `scripts/long_read_validation/run_long_read_validation.slurm`
- output directory: `testing/long_read_validation/bactscout_long_output/`

## Validation matrix

- good ONT single-species sample
- bad ONT single-species sample
- ONT 90/10 mixed-species sample
- ONT 80/20 mixed-species sample

## Tooling isolation

Badread is installed in a separate virtual environment created by `scripts/long_read_validation/setup_badread_env.sh` so the shared Pixi environment remains the production runtime for BactScout users.

For validation speed, the final workflow uses:

- a custom two-genome Sylph database built from the downloaded validation references
- 1x Badread seed datasets that are scaled to the desired effective coverage by concatenating gzip streams

This keeps the validation reproducible while avoiding a multi-gigabyte GTDB download and very long Badread runtimes.

## Scripts

- `scripts/long_read_validation/setup_badread_env.sh`
- `scripts/long_read_validation/download_ncbi_genomes.py`
- `scripts/long_read_validation/run_long_read_validation.slurm`

## Cluster execution

Validation references:

- `GCF_000742135.1` for Klebsiella pneumoniae
- `GCF_000005845.2` for Escherichia coli

Validation datasets:

- `kleb_good.fastq.gz`: 35x effective ONT-like good-quality Klebsiella reads
- `kleb_bad.fastq.gz`: 35x effective ONT-like degraded Klebsiella reads
- `kleb_ecoli_90_10.fastq.gz`: 90/10 Klebsiella / E. coli mixed sample
- `kleb_ecoli_80_20.fastq.gz`: 80/20 Klebsiella / E. coli mixed sample

Validation command path:

- build custom Sylph DB from the two downloaded genomes
- run `bactscout.py long preflight` against a validation-specific config
- run `bactscout.py long collect` for each simulated FASTQ
- merge with `bactscout.py long summary`

## Observations

Observed final statuses from `final_summary_long.csv`:

- `kleb_good`: `PASSED`
- `kleb_bad`: `FAILED`
- `kleb_ecoli_90_10`: `WARNING`
- `kleb_ecoli_80_20`: `FAILED`

Observed metric behavior:

- `kleb_good` passed all long-read flags with `median_q=19.22`, `n50=15884`, `coverage_estimate_sylph=35.07`, and `coverage_estimate_calc=34.36`.
- `kleb_ecoli_90_10` produced the expected contamination warning with `contamination_pct=10.68` while keeping both coverage estimates in `PASSED`.
- `kleb_ecoli_80_20` produced the expected contamination failure with `contamination_pct=20.93` while keeping both coverage estimates in `PASSED`.
- `kleb_bad` failed on read quality (`median_q=7.18`) and had a degraded `n50=5208`. Sylph returned no confident profile rows for that dataset, so taxonomy and expected-genome-size fields were empty and the run followed the intended fallback path for missing genome-size information.

Validation conclusion:

- the good sample passed
- the degraded sample failed on poor long-read quality
- the 90/10 mix yielded a contamination warning
- the 80/20 mix yielded a contamination failure

This matches the intended v1 long-read QC behavior for the implemented ONT validation matrix.