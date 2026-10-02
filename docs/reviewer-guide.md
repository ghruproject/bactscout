# Reviewer guide

This guide separates deterministic checks of BactScout's decision logic from end-to-end runs that invoke external bioinformatics tools.

## Install and prepare databases

From a clone of the repository:

```bash
pixi install -e dev
pixi run bactscout --help
```

The small FASTQ examples are checked into `sample_data/` (about 23 MB total). The first real QC run also needs the configured reference databases. Preflight downloads the default Sylph GTDB database (approximately 4 GB) and the configured StringMLST schemes if they are absent. This requires network access and additional disk space. To put databases in a chosen location, pass the same `--database` path to preflight and to each run:

```bash
pixi run bactscout preflight --database reviewer-databases
```

If these databases are already available, use their directory instead. The long-read command uses the Sylph database; the short-read command also checks the configured MLST databases.

## Short-read workflow

Run the checked-in paired-end example:

```bash
pixi run bactscout qc sample_data \
  --output reviewer-output/short \
  --threads 2 \
  --database reviewer-databases
```

Check that `reviewer-output/short/final_summary.csv` exists and includes the sample row, overall status, read-QC metrics, species, and coverage fields. Per-sample directories should contain the tool outputs and summary CSV. The final QC status depends on the database version and the configured thresholds; this guide does not prescribe a particular result for the real FASTQ run.

## Long-read workflow

Run the checked-in single-file long-read example:

```bash
pixi run bactscout long collect sample_data/long.fastq.gz \
  --platform ont_r10 \
  --output reviewer-output/long \
  --threads 2 \
  --database reviewer-databases
pixi run bactscout long summary reviewer-output/long \
  --output reviewer-output/long
```

Check that `reviewer-output/long/long/long_long_summary.csv` and `reviewer-output/long/final_summary_long.csv` exist. The summary should include read-quality, N50, Sylph coverage, calculated-coverage and final-status fields. As with short reads, the real-run status depends on the selected Sylph database and thresholds.

## Missing-coverage regression

This small test passes controlled `None` coverage values directly to the long-read evaluator. It checks the decision logic without FASTQ processing, Sylph, or a reference database:

```bash
pixi run -e dev pytest tests/test_long_evaluate.py \
  -k no_coverage_can_be_estimated -q
```

Expected checks: the evaluator returns `FAILED`, the combined and Sylph coverage flags are `FAILED`, and the reasons include `No coverage estimate available`. This unit test is not an end-to-end test of Sylph or the long-read command. The real long-read run above exercises external tools and database-backed coverage estimation.

## Additional checks

```bash
pixi run -e dev pytest tests/test_long_evaluate.py tests/test_long_collect.py
pixi run docs-build
```

The first command covers long-read decision and collection tests; some collection tests use controlled tool results rather than real sequencing data. The documentation build checks the MkDocs site. Run these commands from the repository root. Record the software revision and environment with any results reported in a review.
