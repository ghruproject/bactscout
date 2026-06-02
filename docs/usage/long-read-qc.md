# Long-read QC

BactScout provides a parallel long-read QC path under `bactscout long`.

The long-read workflow is additive: it does not change the existing Illumina commands or outputs.

## Commands

Run batch QC on a directory of long-read FASTQ files:

```bash
pixi run python bactscout.py long qc /path/to/fastqs --platform ont_r10
```

Process a single long-read sample:

```bash
pixi run python bactscout.py long collect /path/to/sample.fastq.gz --platform ont_r10
```

Run long-read preflight checks:

```bash
pixi run python bactscout.py long preflight
```

Merge per-sample long-read summaries:

```bash
pixi run python bactscout.py long summary bactscout_long_output
```

## Inputs

- One FASTQ per sample in batch mode.
- Sample names are derived by stripping only FASTQ extensions.
- Supported platforms are `ont_r9`, `ont_r10`, and `pacbio_hifi`.
- `--platform` is required so the QC thresholds are explicit.

## Outputs

The long-read workflow writes to `bactscout_long_output/` by default.

Each sample directory contains:

- `nanoq_stats.json`
- `sylph_report.txt`
- `<sample_id>_long_summary.csv`

The merged batch output is `final_summary_long.csv`.

## QC logic

The long-read workflow uses:

- `nanoq` for read count, total bases, N50, read lengths, and quality summaries
- Sylph for taxonomy and direct coverage estimates
- expected genome size from `filtered_metrics.csv` when available

If the expected genome size is missing for the top taxon, BactScout keeps the Sylph coverage estimate, marks the calculated coverage flag as `WARNING`, and records the reason in the summary.