# JOSS preparation validation

Executed 2 October 2026 against the preparation changes based on commit `2d389b4f9dfac0b636c91cec04d1c95a278e06f6`. This record describes checks, not benchmark results or final author approval.

## Automated checks

- Python 3.11.14, pytest 8.4.2: `pytest -m 'not slow and not integration'` passed **77 tests**, with 10 integration/slow tests deselected and no skips in the selected suite.
- Ruff 0.6.9: `ruff check .` passed. Format checks passed for the Q30 implementation and regression-test file.
- `mkdocs build --strict` passed with MkDocs 1.6 and Material 9.x.
- `git diff --check` passed.

The local verification environment used `uv` to install the package and test/documentation dependencies because the native host is Apple silicon. The repository Pixi environment was used inside the Linux container. Native Pixi installation across every declared platform was not tested.

Three tests that can download FASTQs are now marked `integration` and `slow`; they no longer enter the selected fast suite merely because their filenames contain “integration”. The repository's existing broader CI selection is unchanged.

## Q30 regression

New tests were run before changing the implementation. They produced three failures: a legacy percentage configuration at 65% Q30 and decimal values 0.70 and 0.79 were incorrectly PASSED. The corrected decision is:

| Configuration | Q30 fraction | Expected status |
| --- | ---: | --- |
| Fail 0.70, warn 0.80 | 0.69 | FAILED |
| Fail 0.70, warn 0.80 | 0.70 | WARNING |
| Fail 0.70, warn 0.80 | 0.79 | WARNING |
| Fail 0.70, warn 0.80 | 0.80 | PASSED |
| Legacy fail 60, warn 70 | 0.65 | WARNING |

All 13 tests in `tests/test_faspt_handling.py` pass, including zero-read handling. The change is recorded under Unreleased and is not included in the published 1.4.2 image.

## Real-tool checks

The published `happykhan/bactscout:1.4.2` image was pulled with manifest digest `sha256:43dcac261615c834e19ad92c682a6ba75ba326fa449dc7746879167af2ee7ff8`. Its source metadata reports 1.4.2. The image includes Sylph's GTDB r226 index and configured MLST databases. Commands ran with Docker networking disabled, using fastp 1.0.1, Sylph 0.8.1 and the packaged long-read runtime.

The checked-in paired FASTQs and `sample_data/long.fastq.gz` were processed using the commands in the [reviewer guide](../docs/reviewer-guide.md), with explicit container paths and `/app/bactscout_dbs` as the database directory. Each workflow generated its expected per-sample report and one-row batch summary.

Both workflows were then repeated with the revised `bactscout/` source directory mounted read-only at `/app/bactscout` in the same image. They again completed and produced the same principal metrics/statuses; the short-read report contained the corrected Q30 message. This verifies the revised source with the existing environment without claiming that the published image contains the source changes.

| Input | Observed result in released image | Interpretation |
| --- | --- | --- |
| `GCA_000292405.1_R1/R2.fastq.gz` | 115,980 reads; *Mycoplasmoides genitalium*; Sylph coverage 29.36; overall FAILED | The example runs successfully but fails QC, including missing species genome-size/GC criteria. It is not a passing-control dataset. |
| `long.fastq.gz` | 836 reads; same taxon; Sylph coverage 18.65; overall FAILED | Coverage is below the configured minimum; the expected genome size is unavailable. |
| First 38 reads derived from the long-read fixture | 38 reads; Sylph coverage 4.18; overall FAILED | Confirms low-yield failure with real tools. These are not the original reported 38 reads and still produce a Sylph estimate. |

The exact missing-both-estimates condition is covered separately by `tests/test_long_evaluate.py`, using the reported read metrics. Do not describe the derived 38-read run as a reproduction of missing coverage.

The real workflow run emits a warning that optional resource-monitoring columns are absent when resource reporting is not enabled. Reports are still written. MLST calling on a supported species, every supported platform and the Nextflow example were not independently exercised by these smoke runs.

## Paper

The paper is within the 750–1,750-word range and was compiled with the installed official `openjournals/inara` image. All four pages of the final draft were rendered and visually inspected for clipping, author/affiliation layout, citations and references. JOSS's draft template inserts placeholder publication metadata, including the submission date; this is not a claim of submission.

Final PDF SHA-256: `d9fc672de6d88c338eb101334988917efe778b1cfc59265bad9b501d8b47c2dd`.

The paper deliberately retains a visibly provisional AI disclosure. Funding-role and research-use queries remain in source comments and in the submission checklist. The submitting author confirmed no competing interests. Human review and author consent remain necessary before submission.
