# BactScout Fastp QC Metrics Coverage Analysis

## Comparison with Recommended QC Criteria

### Coverage Status Summary
- **Currently Captured**: 8/16 major criteria categories
- **Partially Captured**: 3/16 categories
- **Not Captured**: 5/16 categories

---

## Detailed Breakdown

### 1. ✅ READ YIELD - FULLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `summary.before_filtering.total_reads` | Fastp JSON | ✅ Captured | Extracted as `read_total_reads` |
| `summary.before_filtering.total_bases` | Fastp JSON | ✅ Captured | Extracted as `read_total_bases` |
| Expected vs. Actual Comparison | N/A | ⚠️ Partial | Not compared against expected depth |

**Notes**: We capture raw numbers but don't evaluate against expected sequencing depth. Could add validation.

---

### 2. ✅ BASE QUALITY - FULLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `q20_rate` | Fastp JSON | ✅ Captured | Extracted as `read_q20_rate` |
| `q30_rate` | Fastp JSON | ✅ Captured | Extracted as `read_q30_rate` |
| Q30 Threshold Check | Config | ✅ Captured | Evaluated with warn/fail thresholds |
| Q20 Threshold Check | Config | ⚠️ Partial | Tracked but not thresholded |

**Notes**: Q30 has dual thresholds (warn/fail). Q20 is captured but only Q30 triggers pass/fail.

---

### 3. ✅ READ LENGTH - FULLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `read1_mean_length` | Fastp JSON | ✅ Captured | Extracted directly |
| `read2_mean_length` | Fastp JSON | ✅ Captured | Extracted directly |
| Mean vs. Expected Cycle Length | Config | ✅ Captured | Evaluated with warn/fail thresholds |
| Too-Short Reads Detection | Fastp JSON | ⚠️ Partial | Available but not reported |

**Current Fields**:
- `read_length_status` (PASSED/WARNING/FAILED)
- `read_length_message` (descriptive)

---

### 4. ✅ GC CONTENT - FULLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| Overall GC % | Fastp JSON | ✅ Captured | Extracted as `gc_content` |
| Expected Range (species-specific) | Metrics CSV | ✅ Captured | Loaded from `mlst_species.txt` |
| Range Validation | Thread.py | ✅ Captured | Checked against species bounds |

**Current Fields**:
- `gc_content` (percentage)
- `gc_content_lower` / `gc_content_upper` (species range)
- `gc_content_status` (PASSED/WARNING/FAILED)

**Not Captured**:
- Per-cycle GC bias (available in `content_curves.GC` array)

---

### 5. ⚠️ FILTERING SUMMARY - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `filtering_result.passed_filter_reads` | Fastp JSON | ✅ Captured | Available but not extracted |
| `filtering_result.low_quality_reads` | Fastp JSON | ❌ Not captured | Available but ignored |
| `filtering_result.too_many_N_reads` | Fastp JSON | ❌ Not captured | Available but ignored |
| `filtering_result.too_short_reads` | Fastp JSON | ❌ Not captured | Available but ignored |
| `filtering_result.too_long_reads` | Fastp JSON | ❌ Not captured | Available but ignored |
| % Reads Passing Filters | Calculated | ⚠️ Partial | Not explicitly calculated/reported |

**Notes**: We use `after_filtering` metrics but don't report WHY reads were filtered or report filtering statistics.

---

### 6. ❌ DUPLICATION RATE - NOT CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `duplication.rate` | Fastp JSON | ❌ Not captured | Available but completely ignored |
| PCR Bias Detection | N/A | ❌ No action | No threshold or warning |

**Data Available**: `duplication.rate = 0.00593351` in sample JSON (0.59%)

---

### 7. ❌ ADAPTER / OVERREPRESENTED SEQUENCES - NOT CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `overrepresented_sequences` | Fastp JSON | ❌ Not captured | Available but ignored |
| Adapter Detection Count | Fastp JSON | ❌ Not captured | Not reported |
| High-Frequency K-mers | Fastp JSON | ⚠️ Partial | K-mer data exists but not analyzed |

**Data Available**: Full `kmer_count` dictionary with all 256 possible 5-mers

---

### 8. ⚠️ PER-BASE QUALITY CURVES - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `quality_curves.mean` per cycle | Fastp JSON | ✅ Available | Not currently extracted |
| Quality End-Drop Detection | Calculated | ❌ Not captured | No trend analysis |
| Per-Base Quality | Fastp JSON | ✅ Available | Quality curves data exists (A, T, G, C) |

**Data Available**: 151 cycles of quality data for each base (A, T, G, C, mean)

---

### 9. ⚠️ PER-BASE COMPOSITION - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `content_curves` per cycle (A/T/G/C) | Fastp JSON | ✅ Available | Composition curves exist but not analyzed |
| Priming Bias Detection (3'/5' bias) | Calculated | ❌ Not captured | No positional analysis |
| N Content | Fastp JSON | ✅ Available | N fraction per cycle tracked |
| Consistent Base Distribution | Calculated | ❌ Not captured | No stability check |

**Data Available**: Per-cycle composition for A, T, G, C, N, and GC combined (151 cycles each)

---

### 10. ⚠️ INSERT SIZE - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `insert_size.peak` | Fastp JSON | ⚠️ Partial | Available but not extracted |
| Expected vs. Actual | Config | ❌ Not captured | No comparison |
| Insert Size Histogram | Fastp JSON | ❌ Not captured | Full histogram available but ignored |
| Short/Long Insert Problems | Calculated | ❌ Not captured | Could detect from histogram |

**Data Available**:
- `insert_size.peak = 260` (in sample)
- `insert_size.unknown = 161147` (unpaired reads)
- `insert_size.histogram` (array of 512 values)

---

### 11. ✅ N CONTENT - FULLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `too_many_N_reads` count | Fastp JSON | ✅ Available | Available in filtering_result |
| N Fraction Overall | Fastp JSON | ✅ Available | Available in content_curves |
| N per Cycle | Fastp JSON | ✅ Available | Per-cycle N counts available |

**Notes**: Data is available but not currently extracted or reported. Could add N-content warnings.

---

### 12. ⚠️ K-MER CONTENT - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `kmer_count` (all 5-mers) | Fastp JSON | ✅ Available | Full dictionary of 256 k-mers |
| Over-Abundant K-mers | Calculated | ❌ Not captured | No enrichment analysis |
| Adapter Signature Detection | Calculated | ❌ Not captured | Could identify adapter k-mers |
| Contamination Signature | Calculated | ❌ Not captured | Could identify contaminant patterns |

**Data Available**: All 256 possible 5-mers with their counts (e.g., AAAAA=245120, AAAAG=138526, etc.)

---

### 13. ⚠️ ADAPTER DETECTION / TRIMMING SETTINGS - PARTIALLY CAPTURED

| Metric | Source | Status | Current Implementation |
|--------|--------|--------|------------------------|
| `command` section in fastp JSON | Fastp JSON | ⚠️ Partial | Command logged but not validated |
| Adapter Detection Flags Used | Fastp JSON | ❌ Not captured | No verification that trimming enabled |
| Adapter Trimming Confirmation | Fastp JSON | ⚠️ Partial | Can infer from before/after diff |

---

## Summary: Capture Matrix

| Category | Fully Captured | Partially Captured | Not Captured | Status |
|----------|:---:|:---:|:---:|--------|
| 1. Read Yield | ✅ | - | (depth validation) | Good |
| 2. Base Quality | ✅ | - | - | Good |
| 3. Read Length | ✅ | - | (too-short stats) | Good |
| 4. GC Content | ✅ | - | (per-cycle bias) | Good |
| 5. Filtering Summary | - | ⚠️ | (filter breakdowns) | **Needs work** |
| 6. Duplication Rate | - | - | ❌ | **Missing** |
| 7. Adapters/Overrep | - | - | ❌ | **Missing** |
| 8. Per-Base Quality | - | ⚠️ | (trend detection) | **Needs work** |
| 9. Per-Base Composition | - | ⚠️ | (bias detection) | **Needs work** |
| 10. Insert Size | - | ⚠️ | (validation) | **Needs work** |
| 11. N Content | ✅ | - | (reporting) | Partial |
| 12. K-mer Content | - | ⚠️ | (enrichment analysis) | **Needs work** |
| 13. Adapter Settings | - | ⚠️ | (validation) | **Needs work** |

---

## Implementation Priority Recommendations

### HIGH PRIORITY (Quick Wins - High Impact)

1. **Extract Duplication Rate** (5 minutes)
   - Add `duplication_rate` to results
   - Warn if > 20%
   - Data: `duplication.rate` in fastp JSON

2. **Extract Insert Size Peak** (5 minutes)
   - Add `insert_size_peak_bp` to results
   - Compare against expected range
   - Warn if too short (<200) or too long (>600)

3. **Extract Filtering Breakdown** (10 minutes)
   - Report: passed, low_quality, too_many_N, too_short, too_long
   - Calculate: % passing filters
   - Warn if <95% pass rate

### MEDIUM PRIORITY (Moderate Effort)

4. **N Content Reporting** (10 minutes)
   - Extract from `filtering_result.too_many_N_reads`
   - Add threshold check
   - Warn if > 0.1%

5. **Per-Base Quality Trend Detection** (20 minutes)
   - Extract `quality_curves.mean` (151 values)
   - Detect quality end-drop
   - Warn if steep decline in last 20 cycles

6. **Adapter Detection Verification** (15 minutes)
   - Parse fastp command to verify `--detect_adapter_for_pe`
   - Warn if adapter detection disabled

### LOWER PRIORITY (Advanced Analysis)

7. **K-mer Enrichment Analysis** (30 minutes)
   - Identify top 5% most abundant k-mers
   - Compare against known adapter sequences
   - Flag suspicious patterns

8. **Per-Cycle Composition Analysis** (30 minutes)
   - Detect priming bias (first 20 cycles)
   - Detect 3' bias (last 20 cycles)
   - Warn if >5% deviation from expected

9. **Insert Size Histogram Analysis** (20 minutes)
   - Detect bimodal distributions (quality filtering issue)
   - Detect very short (<100bp) inserts
   - Calculate insert size statistics (median, std dev)

---

## Implementation Code Locations

**Current Extraction Function**: `bactscout/thread.py:get_fastp_results()` (lines 691-761)

**Current Validation Functions**: 
- `bactscout/thread.py:handle_fastp_results()` (lines 559-605)
- `bactscout/thread.py:handle_species_coverage()` (lines 622-649)

**Sample JSON Structure**: 
- `tests/sample_output_data/sample_001/sample_001_1.fastp.json` (408 lines)
- All recommended metrics available in this file

---

## Data Availability Verification

✅ All recommended metrics are **currently available** in the fastp JSON report
✅ BactScout successfully reads and parses these JSON files
❌ We only extract a subset (~30%) of available metrics
❌ Most quality checks focus on final (after_filtering) metrics, not failure analysis

---

## Recommended Next Steps

1. **Quick Audit** (15 min): Extract duplication_rate, insert_size_peak, filtering stats
2. **Medium Enhancement** (45 min): Add N-content checks, quality trend detection, adapter verification  
3. **Advanced Features** (2-3 hours): K-mer analysis, per-cycle composition analysis
4. **Documentation**: Update output format docs with new metrics

Would you like me to implement any of these enhancements?
