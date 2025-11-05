# Quality Control Guide

!!! note
    This guide explains how to interpret BactScout's quality control metrics and what they mean for your samples.

Quality control (QC) in bacterial whole-genome sequencing (WGS) serves as the foundation for all downstream bioinformatics and biological interpretation.   It ensures that sequencing data are **complete, accurate, and biologically representative** of the isolate being studied.  Without proper QC, subsequent analyses—such as assembly, typing, antimicrobial resistance prediction, or phylogenetic inference—can produce misleading results.

QC can be conceptualized as a **multi-layered process**:

- **Pre-sequencing quality** – Determined by biological and technical inputs:
    - Sample purity and culture viability  
    - DNA integrity, concentration, and contamination from other organisms  
    - Library preparation success (fragment size, adapter ligation, and index balance)

- **Sequencing quality** – Reflecting the instrument’s performance:
    - Base-calling accuracy (Q30 scores)  
    - Read length and distribution  
    - Cluster density and sequencing depth  
    - Instrument- or chemistry-related artefacts (e.g., barcode cross-talk, GC bias)

- **Post-sequencing quality** – Evaluated through computational QC:
    - Correct species identification  
    - Detection of contamination or mixed cultures  
    - Adequate coverage for confident variant detection and assembly  
    - Reasonable GC content and read duplication profiles  
    - Consistent strain typing or MLST results  

In practice, these QC layers are interdependent. For example, **low coverage** might reflect insufficient DNA input, degraded DNA, or instrument under-performance.  Similarly, **mixed-species contamination** could arise from culture cross-contamination or index mis-assignment during multiplexing.

**BactScout’s QC module** focuses on this post-sequencing stage, using read-level metrics and taxonomic profiling to rapidly “scout out” problematic samples before downstream analysis.  
Its goal is not only to identify failures but also to highlight **borderline (“warning”) samples**, allowing laboratories to make informed decisions about resequencing or accepting data with caveats.

The following sections describe how these quality metrics are calculated, the thresholds that define pass/fail states, and how to interpret results within the broader sequencing workflow.

## Quality Control Metrics

BactScout evaluates samples with a two-tier threshold system and several derived metrics. The code uses separate WARN and FAIL thresholds for most metrics (see `bactscout_config.yml`). Where legacy single-threshold keys are present, the code falls back to them for backward compatibility.

Summary of primary metrics and the configuration keys used by the code:

- **Coverage (two sources):**
    - Sylph-based coverage estimate (direct from Sylph): stored as `coverage_estimate_sylph` and its status in `coverage_status`.
    - Calculated coverage (reads / expected genome size): stored as `coverage_estimate_qualibact` and its status in `coverage_estimate_qualibact_status`.
    - Config keys: `coverage_warn_threshold` and `coverage_fail_threshold` (fallback: legacy `coverage_threshold`). These are x-fold values (e.g. 20, 30).

- **Base quality (Q30):**
    - Metric key: `read_q30_rate` (fraction 0.0–1.0).
    - Status stored in `read_q30_status`.
    - Config keys: `q30_warn_threshold` and `q30_fail_threshold`.

- **Read length:**
    - Metrics keys: `read1_mean_length` and `read2_mean_length` (bp); combined status in `read_length_status`.
    - Config keys: `read_length_warn_threshold` and `read_length_fail_threshold` (bp).

- **Contamination (species purity):**
    - Computed as 100 - (top species abundance). The code stores species abundances and evaluates purity.
    - Status stored in `contamination_status` and messages in `contamination_message`.
    - Config keys: `contamination_warn_threshold` and `contamination_fail_threshold` (percent secondary species tolerated). The code treats these as percentages of non-top-species allowed; e.g. `contamination_fail_threshold: 10` means top species purity must be >90% to PASS.
    - The proportion of unassigned reads is included, this means that a sample with 75% Escherichia coli, 15% other species, and 10% unassigned would have 25% contamination.

- **Duplication, N-content, Adapter detection (fastp-derived):**
    - Keys and statuses: `duplication_rate` → `duplication_status`, `n_content_rate` → `n_content_status`, adapter over-representation → `adapter_detection_status`.
    - Config keys: `duplication_warn_threshold` / `duplication_fail_threshold`, `n_content_threshold` (fraction; compared as percentage in the code), `adapter_overrep_threshold`.

Notes about the two-tier logic:

- The code uses WARN and FAIL thresholds. FAIL thresholds represent the minimum/maximum required for a PASSED metric (e.g. `q30_fail_threshold` is the value at or above which Q30 is considered PASSED). WARN thresholds define a borderline region that yields `WARNING` rather than `PASSED` or `FAILED`.
- Many configuration values accept either percent (e.g. 80) or fraction (0.80); the code attempts to normalize values where necessary.

!!! note "What does x-fold coverage mean?"
    "x-fold" (or "30x") coverage refers to the average genome coverage. Practically this is computed as the total number of sequenced bases (after filtering) divided by the expected genome size — e.g. 30x means, on average, each genomic position is covered by ~30 bases. BactScout reports both a Sylph-derived coverage estimate (`coverage_estimate_sylph`) and a calculated estimate based on reads/genome size (`coverage_estimate_qualibact`). **This is different to coverage across the genome - i.e some measure of the proportion of the genome covered at a certain depth - which is not directly assessed by BactScout.**


## PASS/FAIL Determination

The actual PASS/WARNING/FAIL logic is implemented in `bactscout/thread.py` (function `final_status_pass`). The code evaluates individual metric status fields (all keys that end with `_status`) and then derives an overall `PASSED` / `WARNING` / `FAILED` outcome. Below is the precise behaviour used by the code so you can reason about results and tune thresholds accordingly.

Key points of the algorithm (exact behavior in code):

- Critical failures cause immediate FAIL:
    - The following metric statuses are treated as critical: `read_length_status`, `read_q30_status`, `contamination_status`, `gc_content_status`.
    - If any of these is `FAILED`, the final status becomes `FAILED`.

- Coverage handling (both Sylph and qualibact coverage are considered):
    - The pipeline computes two coverage estimates: `coverage_status` (Sylph) and `coverage_estimate_qualibact_status` (calculated from read bases and expected genome size).
    - If both coverage statuses are `FAILED`, final status is `FAILED`.
    - If exactly one of the two coverage statuses is `FAILED` (the other is `PASSED` or `WARNING`), final status becomes `WARNING` (unless already `FAILED` due to a critical metric).

- Non-critical metrics turn PASS → WARNING but do not alone cause FAIL:
    - Non-critical status fields include: `species_status` (species identification), `adapter_detection_status`, `duplication_status`, `n_content_status`. If any of these are `FAILED` or `WARNING` they will push the overall result to `WARNING` unless a critical `FAILED` is already present.
    - `mlst_status` is informational only and never forces a `FAILED` final status; a `WARNING` here can contribute to an overall `WARNING`.

In short:

- Any critical `FAILED` → overall `FAILED`.
- Both coverage methods `FAILED` → overall `FAILED`.
- One coverage `FAILED` (but not critical failures) → overall `WARNING`.
- Any non-critical `WARNING`/`FAILED` (and no critical `FAILED`) → overall `WARNING`.
- Otherwise no problems → overall `PASSED`.

Examples (illustrative):

| Coverage (Sylph / Qualibact) | Q30 | Read length | Contam | Result |
|--------------------------------|-----:|------------:|-------:|--------|
| 50x / 48x                      | PASS | PASS (150bp) | PASS   | ✅ PASSED |
| 20x / 18x                      | PASS | PASS (150bp) | PASS   | ❌ FAILED (both coverage methods FAILED) |
| 50x / 18x                      | PASS | PASS (150bp) | PASS   | ⚠️ WARNING (one coverage metric FAILED) |
| 50x / 48x                      | FAIL | PASS         | PASS   | ❌ FAILED (Q30 is critical and FAILED) |
| 50x / 48x                      | PASS | PASS         | WARNING| ⚠️ WARNING (contamination raised WARNING) |

## Adjusting Thresholds

BactScout supports explicit WARN and FAIL thresholds for most metrics. Edit `bactscout_config.yml` to tune behavior. The code reads keys such as:

- `coverage_warn_threshold` and `coverage_fail_threshold` (x-fold coverage)
- `q30_warn_threshold` and `q30_fail_threshold` (fractions, e.g. 0.80 or 80 are both accepted)
- `read_length_warn_threshold` and `read_length_fail_threshold` (bp)
- `contamination_warn_threshold` and `contamination_fail_threshold` (percent secondary species tolerated)
- `duplication_warn_threshold` / `duplication_fail_threshold` (fraction)
- `n_content_threshold` (fraction; code multiplies by 100 when comparing to percent values produced by fastp)
- `adapter_overrep_threshold` (integer count)

Suggested example sets:

Lenient (more samples will PASS/WARNING rather than FAIL):

```yaml
coverage_fail_threshold: 20
coverage_warn_threshold: 13
q30_fail_threshold: 0.70
q30_warn_threshold: 0.60
read_length_fail_threshold: 80
read_length_warn_threshold: 60
contamination_fail_threshold: 15
contamination_warn_threshold: 8
```

Strict (fewer samples PASS):

```yaml
coverage_fail_threshold: 50
coverage_warn_threshold: 33
q30_fail_threshold: 0.90
q30_warn_threshold: 0.85
read_length_fail_threshold: 120
read_length_warn_threshold: 100
contamination_fail_threshold: 5
contamination_warn_threshold: 2
```

Run BactScout with a custom config file:

```bash
pixi run bactscout qc data/ -c strict_config.yml
```

## Interpreting Individual Failures

### Low Coverage

BactScout computes coverage in two ways: the Sylph-provided estimate (`coverage_estimate_sylph`) and a calculated estimate derived from total read bases divided by an expected genome size (`coverage_estimate_qualibact`). Either or both can indicate low coverage.

**Symptoms**:

- `coverage_estimate_sylph` or `coverage_estimate_qualibact` below the configured WARN/FAIL thresholds (see `coverage_warn_threshold` and `coverage_fail_threshold`).
- Low `read_total_bases` relative to expected genome size.

**Causes**:

- Insufficient input material
- Poor DNA extraction
- Low sequencing depth
- Library preparation issues

**Solutions**:

1. Re-sequence with higher depth
2. Verify DNA quality/quantity before sequencing
3. If appropriate for your study, relax coverage thresholds in `bactscout_config.yml`

### Low Q30 (base quality)

**Symptoms**:

- `read_q30_rate` (fraction) falls below the configured `q30_warn_threshold` / `q30_fail_threshold`.

**Causes**:

- Sequencing toward end of flowcell (quality degradation)
- Poor cluster quality
- Contaminating sequences
- Sequencing chemistry issues

**Solutions**:

1. Review raw FASTQ quality scores (fastp json/html report)
2. Consider adapter trimming
3. Check for over-represented contaminants or low-complexity sequences (These are reported in the fastp report, and in the bcl2fastq run metrics)
4. Check with who did the sequencing, often low base quality comes with other symptoms reported by the instrument (e.g. cluster density).
5. Re-sequence if issues are severe

### Short Reads

**Symptoms**:

- Either `read1_mean_length` or `read2_mean_length` is below configured `read_length_warn_threshold` / `read_length_fail_threshold`.

**Causes**:

- Degraded DNA input
- Library preparation issues
- Aggressive trimming
- Sequencing platform limitation

**Solutions**:

1. Verify DNA fragmentation status
2. Improve library preparation
3. Review fastp trimming parameters and composition reports
4. Lower thresholds for short-read platforms if appropriate

### High Contamination

Contamination is evaluated from Sylph species abundance. The pipeline computes the abundance of the top species and treats contamination thresholds as the allowed percent of non-top species.

**Symptoms**:

- Top species purity (`top_species_pct`) is below `100 - contamination_warn_threshold` (warning) or below `100 - contamination_fail_threshold` (fail). Practically, with `contamination_fail_threshold: 10`, your top species must be >90% for a PASS.
- Multiple species reported by Sylph with non-trivial abundance.

**Causes**:

- Mixed sample/strain
- Cross-contamination during processing
- Environmental (or Lab or kit) contamination
- Host DNA contamination

**Solutions**:

1. Review the Sylph output files and `species`/`species_abundance` fields
2. Check sample handling and extraction records
3. Consider re-extraction or re-sequencing
4. If mixed species are expected for your study, relax contamination thresholds in the config

## GC Content Considerations

**GC Percentage**: Genome GC content varies by species:

- **25-35%** - Some Gram-negatives (e.g., *Vibrio*)
- **40-60%** - Most bacteria (typical range)
- **60-75%** - Some Gram-positives (e.g., *Bacillus*)

**Interpretation**:

- GC content in results file is **observed** from the sample
- Bactscout compares this to reference species GC content (stored in database via qualibact metrics)
- Major deviation might indicate contamination or misidentification

## Data Quality Decisions

### When to PASS a Failed Sample

Sometimes you may want to analyze samples that don't meet all thresholds:

- **Low coverage**: Acceptable if coverage ~20x and species identification is confident. For read mapping low coverage may be tolerable. For genome assembly, you could proceed but understand that some regions of the genome may be missing or fragmented.
- **Low Q30%**: Acceptable if concentrated in specific regions (adapters), i.e. if you could trim or filter reads and recover quality
- **Short reads**: Acceptable if sufficient for your analysis (assembly, variant calling)
- **Contamination 10-15%**: May be acceptable if minor species identified and handled appropriately

**Decision framework**:

1. Review the specific failing metric
2. Consult with your team or stakeholders
3. Consider your analysis goals
4. Decide if the data quality is sufficient for your purposes
5. Document your decision rationale

### When to REJECT a Failed Sample

- Very low coverage (<5x) - insufficient information
- Very poor Q30% (<50%) - unreliable base calls
- High contamination (>40%) - unreliable species ID or simply the wrong organism
- Many mixed species for single-species analysis - cannot interpret results confidently

## MLST & Strain Typing Results

**What is MLST**?

- **Multi-Locus Sequence Typing** assigns a sequence type (ST) based on ~7 housekeeping genes
- Used for epidemiology and strain tracking
- Allows comparison with public databases
- BactScout performs MLST for supported species using stringMLST databases
- A single isolate should have one ST; mixed ST calls suggest mixed strains

**MLST Results**:

- `mlst_type` - Sequence type number (e.g., "ST-10")
- Usually available only for species with defined schemes (E. coli, Salmonella, etc.)
- Identical ST = likely same clonal lineage
- Different ST = different strain lineage

For single-species samples with available MLST databases, BactScout performs Multi-Locus Sequence Typing (MLST) to assign a sequence type (ST) for epidemiological tracking.

### Understanding MLST Status

MLST has two possible status values:

| Status | Meaning | What it means for your sample |
|--------|---------|------|
| **PASSED** | Valid ST assigned | ST was successfully determined and is a known sequence type (ST > 0) |
| **WARNING** | ST missing or unknown | No valid ST could be assigned - this is informational and does NOT cause overall sample QC failure |

### When MLST Results in WARNING

Missing or invalid MLST results (WARNING status) can occur due to:

1. **No valid ST found**

   - Partial coverage of housekeeping genes
   - Sequence divergence from reference strains

2. **Insufficient coverage over genes**

   - Some housekeeping genes have low or zero coverage
   - Sample contamination reducing coverage of target genes
   - Random read distribution

3. **No MLST database available**

   - Species not included in BactScout's MLST databases
   - Add additional databases via configuration


### No MLST Database for Species

If your species doesn't have MLST results:

1. Check `bactscout_config.yml` to see available databases
2. To add MLST for additional species:
   ```yaml
   # In config file, specify new databases
   mlst_species:
     species_new: "PUBMLST Database Name"
   ```
3. Install the corresponding stringMLST database:
   ```bash
   stringMLST.py -S new_scheme --install
   ```
See the [MLST Species Guide](./mlst-species.md) for details on supported species and database preparation.

## See Also

- [Output Format Reference](../usage/output-format.md) - CSV column descriptions
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
