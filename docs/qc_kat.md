# KAT (K-mer Analysis Toolkit) QC Metrics

## Overview

KAT (K-mer Analysis Toolkit) integration provides k-mer based quality control analysis for bacterial sequencing samples. This advanced QC layer detects sequencing errors, contamination, and coverage anomalies through analysis of k-mer frequency distributions and GC×coverage patterns.

**Key Features:**
- K-mer histogram analysis for error detection
- GC×coverage matrix analysis for contamination detection
- Automated flag computation for QC decision making
- Graceful degradation when KAT not installed
- Full CLI control for batch and single-sample analysis

## Metrics Overview

KAT analysis produces 23 metrics organized into four categories:

### 1. K-mer Histogram Metrics (10)

These metrics characterize the k-mer frequency distribution, revealing sequencing quality and genome complexity.

#### kat_k
- **Type:** Integer
- **Range:** 19-31
- **Default:** 27
- **Interpretation:** K-mer size used for analysis. Larger k increases specificity for error detection.

#### kat_total_kmers
- **Type:** Integer
- **Range:** > 0
- **Interpretation:** Number of distinct k-mers in the sample
- **Quality Signal:** Higher indicates more k-mer diversity; reflects genome complexity and read quality
- **Typical Values:** 
  - Bacteria: 1M - 50M k-mers depending on genome size

#### kat_total_kmer_instances
- **Type:** Integer
- **Interpretation:** Total count of all k-mer occurrences (sum of coverage × count)
- **Quality Signal:** Higher correlates with sequencing depth
- **Typical Values:**
  - 100x coverage: 2B-5B instances for ~5Mb bacterial genome

#### kat_error_peak_cov
- **Type:** Float
- **Interpretation:** K-mer coverage at the error peak (typically ≤4x)
- **Quality Signal:** Lower is better; indicates minimal sequencing errors
- **Typical Values:**
  - Good samples: 1-2x
  - Poor samples: 3-4x (high error region occupancy)
- **Flag Threshold:** Error region = coverage ≤ 4x (configurable)

#### kat_error_peak_prop
- **Type:** Float
- **Range:** 0.0 - 1.0 (fraction)
- **Interpretation:** Proportion of reads in error region (low-coverage k-mers)
- **Quality Signal:** Lower is better; represents sequencing error rate
- **Typical Values:**
  - Excellent: < 0.02 (< 2%)
  - Good: 0.02 - 0.05
  - Warning: > 0.05 (⚠️ **FLAG**)
- **Warning Threshold:** 0.05 (configurable as `error_prop_warn`)
- **Recommendation:** Inspect sequencing chemistry and flowcell QC

#### kat_main_peak_cov
- **Type:** Float
- **Interpretation:** K-mer coverage at main genomic peak (coverage > 4x)
- **Quality Signal:** Indicates the primary sequencing depth for the sample
- **Typical Values:**
  - 100x coverage target: ~100x
  - 50x coverage target: ~50x
- **Low Coverage Flag:** < 10x (⚠️ **FLAG** - configurable as `main_cov_low`)
- **Recommendation:** If too low, consider additional sequencing

#### kat_main_peak_height
- **Type:** Integer
- **Interpretation:** Number of distinct k-mers at the main peak
- **Quality Signal:** Higher indicates more k-mers at genomic coverage (less bimodal)
- **Typical Values:** 20% - 30% of total k-mers

#### kat_unique_kmers_prop
- **Type:** Float
- **Range:** 0.0 - 1.0 (fraction)
- **Interpretation:** Proportion of k-mers appearing only once (singletons)
- **Quality Signal:** Higher indicates more error k-mers or low coverage regions
- **Typical Values:**
  - Good: 0.1 - 0.3 (10-30%)
  - Poor: > 0.5 (50%+)
- **Recommendation:** Very high singleton rates suggest low coverage or high error

#### kat_median_kmer_cov
- **Type:** Float
- **Interpretation:** Median k-mer coverage (50th percentile)
- **Quality Signal:** Robust coverage statistic less affected by outliers
- **Typical Values:**
  - Close to main peak for good samples
  - Skewed lower for contaminated samples

#### kat_mean_kmer_cov
- **Type:** Float
- **Interpretation:** Mean k-mer coverage (average)
- **Quality Signal:** Sensitive to high-coverage contaminants
- **Typical Values:**
  - Normal distribution: Mean ≈ Median
  - Contaminated: Mean >> Median (pulled up by contaminant peaks)

### 2. GC×Coverage Matrix Metrics (4)

These metrics analyze the GC% vs coverage distribution, revealing contamination and unusual composition.

#### kat_gcp_num_bins
- **Type:** Integer
- **Interpretation:** Number of non-empty bins in the GC×coverage matrix
- **Quality Signal:** Lower indicates simpler, more uniform GC/coverage distribution
- **Typical Values:**
  - Clean samples: 50-200 bins
  - Contaminated: 200-500+ bins

#### kat_gcp_top_bin_prop
- **Type:** Float
- **Range:** 0.0 - 1.0
- **Interpretation:** Proportion of reads in the largest GC×coverage bin
- **Quality Signal:** Higher indicates more uniform sample composition
- **Typical Values:**
  - Clean samples: 0.3 - 0.6 (30-60%)
  - Contaminated: < 0.3 (spread across multiple bins)

#### kat_gcp_multi_modal
- **Type:** Binary (0 or 1)
- **Interpretation:** Indicates detection of multiple GC×coverage modes
- **Quality Signal:** Value of 1 suggests contamination or significant heterogeneity
- **Detection Method:** Flags if multiple bins contain > 10% of reads
- **Interpretation Examples:**
  - 0 = Clean, unimodal distribution
  - 1 = ⚠️ **FLAG** - Possible contamination or mixed sample

#### kat_gcp_lowcov_gc_prop
- **Type:** Float
- **Range:** 0.0 - 1.0
- **Interpretation:** Proportion of low-coverage reads with extreme GC%
- **Quality Signal:** Indicates alien DNA or contamination
- **Detection Method:** 
  - Low coverage = < 2x (main_cov_low × 0.2)
  - Extreme GC = < 25% or > 75% GC
- **Typical Values:**
  - Clean: < 0.01 (< 1%)
  - Questionable: 0.01 - 0.05
  - ⚠️ **Flag threshold:** > 0.02 for contamination flag

### 3. Quality Flags (3 Binary)

Automated flags derived from metrics above for rapid QC decision making.

#### kat_flag_low_coverage
- **Type:** Binary (0 or 1)
- **Threshold:** `kat_main_peak_cov < main_cov_low` (default: 10x)
- **Meaning:** Primary sequencing depth is insufficient
- **Action:** Recommend additional sequencing
- **QC Impact:** Contributes to WARNING status

#### kat_flag_high_error
- **Type:** Binary (0 or 1)
- **Threshold:** `kat_error_peak_prop > error_prop_warn` (default: 5%)
- **Meaning:** Error region contains too many reads
- **Action:** Investigate chemistry, cluster density, cycle length
- **QC Impact:** Contributes to WARNING status

#### kat_flag_contamination
- **Type:** Binary (0 or 1)
- **Thresholds:** Multi-modal (`kat_gcp_multi_modal == 1`) OR extreme GC (`kat_gcp_lowcov_gc_prop > 0.02`)
- **Meaning:** Sample shows signs of contamination or anomalous composition
- **Action:** Verify sample provenance and prepare for analysis
- **QC Impact:** Contributes to WARNING status

### 4. Metadata

#### kat_version
- **Interpretation:** Version of KAT used for reproducibility
- **Example:** "kat version 2.4.2"

#### kat_status
- **Possible Values:** PASSED, WARNING, FAILED, SKIPPED
- **Interpretation:**
  - PASSED: No KAT flags raised
  - WARNING: One or more flags raised (still usable)
  - FAILED: Multiple flags raised (requires investigation)
  - SKIPPED: KAT not available or disabled

#### kat_message
- **Interpretation:** Descriptive message explaining KAT analysis results
- **Example:** "K-mer analysis detected elevated error rate. Error peak contains 7.3% of reads."

## Configuration

### YAML Configuration

```yaml
kat:
  enabled: true                    # Enable/disable KAT analysis
  k: 27                            # K-mer size (19-31, default 27)
  threads: 4                       # Threads for KAT (default 4)
  
  # Which subcommands to run
  run:
    hist: true                     # Histogram (RECOMMENDED)
    gcp: true                      # GC×coverage (RECOMMENDED)
    comp: false                    # Composition (FUTURE)
    sect: false                    # Sector coverage (FUTURE)
  
  # Thresholds for metric interpretation
  thresholds:
    error_cov_cutoff: 4           # Error region boundary (default 4x)
    error_prop_warn: 0.05         # Error proportion warning (default 5%)
    main_cov_low: 10              # Low coverage threshold (default 10x)
    gcp_multi_modal_bin_prop: 0.1 # Multi-modal threshold (default 10%)
    comp_shared_prop_warn: 0.9    # Composition threshold (future use)
```

### CLI Overrides

```bash
# Enable KAT (disable in config)
bactscout qc input/ --kat

# Disable KAT (enable in config)
bactscout qc input/ --kat False

# Set k-mer size
bactscout qc input/ --k 31

# Combined
bactscout collect r1.fq r2.fq --kat --k 25
```

## Interpretation Guide

### Optimal Sample (No Flags)

```
kat_error_peak_prop: 0.01 (1%)
kat_main_peak_cov: 50.0
kat_gcp_multi_modal: 0
kat_gcp_lowcov_gc_prop: 0.001
→ Status: PASSED ✓
```

**Interpretation:** Good quality sequencing. Expected high-utility data for genomic analysis.

### Warning: High Error Rate (kat_flag_high_error)

```
kat_error_peak_prop: 0.08 (8%)     ← Above 5% threshold
kat_main_peak_cov: 40.0
kat_gcp_multi_modal: 0
→ Status: WARNING ⚠️
Message: "K-mer analysis detected elevated error rate."
```

**Interpretation:** Elevated sequencing error rate. May impact short-read mapping and variant calling accuracy.

**Troubleshooting:**
1. Check flowcell QC metrics in sequencer logs
2. Verify reagent kit batch
3. Consider re-sequencing if errors > 10%
4. May still be usable for species identification

### Warning: Low Coverage (kat_flag_low_coverage)

```
kat_main_peak_cov: 5.0             ← Below 10x threshold
kat_error_peak_prop: 0.02
kat_gcp_multi_modal: 0
→ Status: WARNING ⚠️
Message: "K-mer analysis indicates low genome coverage. Main peak coverage: 5.0x."
```

**Interpretation:** Insufficient sequencing depth. May lack coverage for reliable variant calling.

**Recommendation:** 
- For whole-genome analysis: Recommend additional sequencing
- For species ID only: Usually acceptable at 5x+
- For MLST/cgMLST: Depends on target coverage

### Warning: Contamination (kat_flag_contamination)

```
kat_gcp_multi_modal: 1             ← Multi-modal detected
kat_gcp_lowcov_gc_prop: 0.03       ← Extreme GC + low cov
→ Status: WARNING ⚠️
Message: "K-mer analysis suggests possible contamination."
```

**Interpretation:** Sample shows multiple peaks in GC×coverage space or unusual composition.

**Troubleshooting:**
1. Verify sample identity
2. Check for mixed culture indicators
3. Inspect assembly for foreign sequences
4. May still be usable with careful post-processing

### Failed: Multiple Issues

```
kat_flag_low_coverage: 1
kat_flag_high_error: 1
kat_flag_contamination: 1
→ Status: FAILED ✗
Message: "K-mer analysis detected multiple QC issues: low coverage (3.0x), high error rate (12%), possible contamination."
```

**Interpretation:** Multiple serious issues detected. Sample quality questionable.

**Recommendation:**
- Investigate root causes
- Consider re-sequencing
- Not recommended for critical analysis

## Threshold Tuning

### Error Region Boundary (error_cov_cutoff)

Default: 4x

- **Lower (e.g., 2x):** More aggressive error detection, fewer k-mers considered "main peak"
- **Higher (e.g., 6x):** Fewer k-mers marked as errors, better for high-error sequencing

**Recommendation:** Keep at 4x for standard Illumina sequencing

### Error Proportion Warning (error_prop_warn)

Default: 0.05 (5%)

- **Lower (e.g., 0.02):** Stricter standard, good for publication-quality data
- **Higher (e.g., 0.10):** More permissive, useful for high-throughput screening

**Recommendation:** 
- 0.02 for high-quality requirements
- 0.05 for standard applications
- 0.10 for rapid screening

### Low Coverage Threshold (main_cov_low)

Default: 10x

- **Lower (e.g., 5x):** Accept lower-depth samples
- **Higher (e.g., 20x):** Require higher minimum coverage

**Recommendation:**
- 5x for species identification
- 10x for standard analysis
- 20x for clinical/publication use
- 30x+ for variant calling on difficult regions

### Multi-modal Detection (gcp_multi_modal_bin_prop)

Default: 0.1 (10%)

- **Lower (e.g., 0.05):** More sensitive to multi-modality
- **Higher (e.g., 0.15):** More permissive, allows more spread

**Recommendation:** 0.1 for balanced sensitivity

## Performance Characteristics

### Runtime

- **Input:** Paired-end FASTQ files
- **Typical Duration:**
  - 50x coverage: 5-10 minutes
  - 100x coverage: 10-20 minutes
  - 200x coverage: 20-40 minutes

### Memory Usage

- **Histogram:** ~2-4 GB RAM
- **GC×coverage:** ~1-2 GB RAM
- **Total:** ~4-6 GB for typical samples

### Output Files

- `kat_hist_k27.hist.gnuplot` - Histogram data (parsed in memory)
- `kat_gcp_k27.gcp.gnuplot` - GC×coverage matrix (parsed in memory)

Files are parsed and deleted after metric extraction.

## Troubleshooting

### KAT Not Found

```
Error: KAT binary not found in PATH
```

**Solution:**
```bash
# Install KAT via conda
conda install -c bioconda kat

# Or via system package manager
apt-get install kat  # Ubuntu/Debian
brew install kat     # macOS (via homebrew-science)
```

**Workaround:** Disable KAT analysis
```bash
bactscout qc input/ --kat False
```

### Timeout

```
KAT analysis timed out (1 hour)
```

**Causes:**
- Very large input files (> 10GB)
- Insufficient system resources
- Disk I/O bottleneck

**Solutions:**
1. Check available memory: `free -h`
2. Check disk space: `df -h`
3. Use SSD for temporary files
4. Process large files individually

### Empty or Invalid Output

```
No valid data in histogram file
```

**Causes:**
- Input FASTQ files are corrupted
- Input files are too small (< 1M reads)
- KAT version incompatibility

**Solutions:**
1. Verify FASTQ integrity: `gzip -t reads.fastq.gz`
2. Check file size: `zcat reads.fastq.gz | wc -l`
3. Update KAT: `conda update kat`

## References

### KAT Documentation
- [KAT GitHub Repository](https://github.com/TGAC/KAT)
- [KAT Manual](https://kat.readthedocs.io/)

### K-mer Analysis Background
- Pell et al. (2012). "Scaling metagenome sequence assembly with probabilistic de Bruijn graphs"
- Baker & Coote (2016). "KAT: a K-mer Analysis Toolkit"

### Application in QC
- See BactScout main documentation for integration with other QC metrics

## Examples

### Example 1: Run with Custom K-mer Size

```bash
bactscout qc samples/ --k 31
```

### Example 2: Disable KAT for Fast Screening

```bash
bactscout qc samples/ --kat False
```

### Example 3: Process Single Sample with KAT

```bash
bactscout collect sample_R1.fq.gz sample_R2.fq.gz --kat --k 27
```

### Example 4: CSV Output with KAT Metrics

The final summary CSV includes all KAT columns:

```
sample_id,kat_total_kmers,kat_error_peak_prop,kat_main_peak_cov,kat_flag_low_coverage,kat_flag_high_error,kat_flag_contamination,kat_status,kat_message,...
Sample_001,2430000,0.021,48.5,0,0,0,PASSED,"K-mer analysis indicates good read quality..."
Sample_002,1890000,0.089,12.0,0,1,0,WARNING,"K-mer analysis detected elevated error rate..."
```

## Version History

- **v2.0.0** (Current): Full KAT integration with metrics, flags, and validation
- **v1.0.0**: Initial KAT module with basic histogram and GCP parsing

---

**Last Updated:** 2025-10-28  
**KAT Compatibility:** ≥ 2.4.2  
**BactScout Version:** ≥ 2.0.0
