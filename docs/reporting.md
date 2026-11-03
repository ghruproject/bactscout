# HTML reports

BactScout can generate an offline HTML report containing the recorded QC statuses,
measurements and diagnostic messages for short-read or long-read samples. CSV
output remains the default. HTML generation does not rerun fastp, nanoq, Sylph or
stringMLST, and does not recalculate QC decisions.

## Report existing results

Pass a BactScout output directory or a single summary CSV:

```bash
bactscout report results/ -o results/report.html
bactscout report results/final_summary.csv -o results/report.html
bactscout report long_results/final_summary_long.csv -o long_results/report.html
```

When a directory contains a consolidated summary, the report uses it instead of
counting its individual sample CSVs again. Otherwise, it reads the per-sample
summaries. Duplicate samples and malformed CSV rows produce an error rather than
being silently combined or misaligned.

## Generate HTML with an analysis command

Add `--html-report PATH` to `qc`, `collect` or `summary`, including their `long`
variants:

```bash
bactscout qc reads/ -o results --html-report results/report.html
bactscout collect sample_R1.fastq.gz sample_R2.fastq.gz -o results \
  --html-report results/sample-report.html
bactscout summary results/ -o results --html-report results/report.html
bactscout long qc long_reads/ --platform ont_r10 -o long_results \
  --html-report long_results/report.html
```

These commands generate HTML only after successfully writing their CSV output.
A sample with a QC status of `FAILED` can still be reported: this status describes
read quality, not a failed software run. If processing or preflight fails, no new
HTML report is generated from old results. Existing files are retained.

## Read and share the report

Open the HTML file in a browser. Its styles and table controls work
offline. Search and filter the sample table, then open a sample to inspect its
measurements and warning or failure messages. Missing measurements appear as
unavailable; zero values remain zero. Short-read Q30 fractions are displayed as
percentages, while GC and taxonomic abundance are already percentages in CSV.

Links to individual fastp reports work when the corresponding HTML files remain
at their relative locations. Share the result directory alongside the combined
report to preserve these links. This combined report complements the original
fastp HTML reports and retains BactScout's recorded decisions.

The report styling is adapted from [SpecCheck](https://gitlab.com/cgps/tools/speccheck).
