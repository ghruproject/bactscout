# Quality Control Guide

This guide explains how to interpret BactScout's quality control metrics and what they mean for your samples.

## Quality Control Metrics

BactScout evaluates samples on four key dimensions:

### 1. Sequencing Coverage

**Metric**: `coverage` (x-fold depth)

**What it means**: How many times each position in the genome is covered by sequencing reads.

- **10x** - Very low; insufficient for reliable variant calling
- **30x** - Minimum recommended for most applications
- **100x** - High coverage; good for strain-level accuracy
- **200x+** - Very high; potential for ultra-rare variant detection

**Why it matters**:
- Low coverage → random sampling errors
- Adequate coverage → confident consensus sequence
- Very high coverage → potential sequencing artifacts or contamination

**Default threshold**: 30x (adjustable in config)

```yaml
coverage_threshold: 30
```

### 2. Base Quality (Q30)

**Metric**: `q30_percent` (percentage of bases with Phred quality ≥30)

**What it means**: The percentage of sequenced bases that have a high confidence score (Q≥30 = 99.9% accuracy).

- **<50%** - Poor quality; not recommended for analysis
- **50-70%** - Acceptable but marginal; consider re-sequencing
- **70-85%** - Good; suitable for most applications
- **>85%** - Excellent; high confidence in base calls

**Why it matters**:
- Low quality bases → unreliable variant calls
- High quality bases → confident consensus and variant identification

**Default threshold**: 80% (adjustable in config)

```yaml
q30_pass_threshold: 0.80
```

### 3. Read Length

**Metric**: `mean_read_length` (base pairs)

- **<100 bp** - Short reads; limit some analyses
- **100-150 bp** - Standard for Illumina
- **>150 bp** - Extended reads; better assembly and mapping
- **>200 bp** - Long reads; different sequencing platform (Nanopore/PacBio)

**Why it matters**:
- Longer reads → better genome assembly
- Short reads → more difficult variant calling and assembly

**Default threshold**: 100 bp (adjustable in config)

```yaml
read_length_pass_threshold: 100
```

### 4. Contamination

**Metric**: `contamination_pct` (percentage of foreign reads)

**What it means**: The percentage of reads that don't belong to the identified species.

- **<1%** - Excellent; pure sample
- **1-5%** - Minor contamination; usually acceptable
- **5-10%** - Moderate contamination; consider investigation
- **>10%** - Significant contamination; likely problematic

**Possible contamination sources**:
- Environmental DNA
- Cross-contamination during sample handling
- Adapter/vector sequences
- Presence of mixed strains/species

**Why it matters**:
- High contamination → unreliable species identification
- High contamination → inflated coverage calculations
- High contamination → mixed MLST profiles

**Default threshold**: 10% (adjustable in config)

```yaml
contamination_threshold: 10
```

## PASS/FAIL Determination

A sample receives a **PASS** status only when **ALL** of the following are true:

| Metric | Default Threshold | Symbol |
|--------|------------------|--------|
| Coverage | ≥ 30x | ✓ |
| Q30 Bases | ≥ 80% | ✓ |
| Read Length | ≥ 100 bp | ✓ |
| Contamination | ≤ 10% | ✓ |

**Example Scenarios**:

| Coverage | Q30% | Length | Contam% | Result |
|----------|------|--------|---------|--------|
| 50x | 90% | 150bp | 2% | ✅ **PASS** |
| 20x | 90% | 150bp | 2% | ❌ FAIL (coverage too low) |
| 50x | 75% | 150bp | 2% | ❌ FAIL (Q30 too low) |
| 50x | 90% | 80bp | 2% | ❌ FAIL (reads too short) |
| 50x | 90% | 150bp | 15% | ❌ FAIL (contamination too high) |

## Adjusting Thresholds

Different studies may require different thresholds. Edit `bactscout_config.yml`:

### Lenient Thresholds (More samples PASS)

For exploratory studies where perfect quality isn't required:

```yaml
coverage_threshold: 20          # Instead of 30
q30_pass_threshold: 0.70        # Instead of 0.80
read_length_pass_threshold: 80  # Instead of 100
contamination_threshold: 15     # Instead of 10
```

### Strict Thresholds (Fewer samples PASS)

For critical applications requiring high confidence:

```yaml
coverage_threshold: 50          # Instead of 30
q30_pass_threshold: 0.90        # Instead of 0.80
read_length_pass_threshold: 120 # Instead of 100
contamination_threshold: 5      # Instead of 10
```

Run BactScout with custom config:

```bash
pixi run bactscout qc data/ -c strict_config.yml
```

## Interpreting Individual Failures

### Low Coverage

**Symptoms**:
- `coverage` < threshold
- Insufficient total bases

**Causes**:
- Insufficient input material
- Poor DNA extraction
- Sequencing depth set too low
- Library preparation issues

**Solutions**:
1. Re-sequence with higher depth
2. Increase total read count
3. Verify DNA quality/quantity before sequencing
4. Lower threshold if intentional (adjust config)

### Low Q30 Percentage

**Symptoms**:
- `q30_percent` < threshold
- High number of low-quality bases

**Causes**:
- Sequencing toward end of flowcell (quality degradation)
- Poor cluster quality
- Contaminating sequences
- Sequencing chemistry issues

**Solutions**:
1. Review raw FASTQ quality scores (fastp HTML report)
2. Consider adapter trimming (done automatically by BactScout)
3. Check for low-complexity regions
4. Re-sequence if issues are severe

### Short Reads

**Symptoms**:
- `mean_read_length` < threshold
- Reads significantly shorter than expected

**Causes**:
- Degraded DNA input
- Library preparation issues
- Aggressive trimming
- Sequencing platform limitation

**Solutions**:
1. Verify DNA fragmentation status
2. Improve library preparation
3. Check fastp trimming parameters
4. Lower threshold if using short-read platform (adjust config)

### High Contamination

**Symptoms**:
- `contamination_pct` > threshold
- Secondary species detected
- Multiple species in Sylph results

**Causes**:
- Mixed sample/strain
- Cross-contamination during processing
- Environmental contamination
- Host DNA contamination

**Solutions**:
1. Review Sylph output (which species detected)
2. Check sample history/handling
3. Consider sample segregation
4. Verify extraction protocol
5. Lower threshold if mixed species expected (adjust config)

## GC Content Considerations

**GC Percentage**: Genome GC content varies by species:

- **25-35%** - Some Gram-negatives (e.g., *Vibrio*)
- **40-60%** - Most bacteria (typical range)
- **60-75%** - Some Gram-positives (e.g., *Bacillus*)

**Interpretation**:
- GC content in results file is **observed** from the sample
- Compare to reference species GC content (stored in database)
- Major deviation might indicate contamination or misidentification

## Species Identification Quality

**Primary vs Secondary Species**:
- `primary_species` - Best ANI (average nucleotide identity) match
- `primary_species_pct` - ANI to primary species (%)
- `secondary_species` - Second-best match
- `secondary_species_pct` - ANI to secondary species (%)

**Good species identification**:
- `primary_species_pct` > 98% - Confident ID
- `primary_species_pct` > 95% - Good ID
- `primary_species_pct - secondary_species_pct` > 1% - Clear winner

**Uncertain species identification**:
- `primary_species_pct` < 95% - May not be in database
- Primary and secondary ANIs very close - Could be different species

## MLST Typing Interpretation

**What is MLST**?
- **Multi-Locus Sequence Typing** assigns a sequence type (ST) based on 7 housekeeping genes
- Used for epidemiology and strain tracking
- Allows comparison with public databases

**MLST Results**:
- `mlst_type` - Sequence type number (e.g., "ST-10")
- Usually available only for species with defined schemes (E. coli, Salmonella, etc.)
- Identical ST = likely same source or close relative
- Different ST = different strain lineage

**Using MLST for epidemiology**:
1. Use public databases (MLST.net) to find ST information
2. Compare STs to identify outbreak sources
3. Track strain persistence over time

## Data Quality Decisions

### When to PASS a Failed Sample

Sometimes you may want to analyze samples that don't meet all thresholds:

- **Low coverage**: Acceptable if coverage ~20x and species identification is confident
- **Low Q30%**: Acceptable if concentrated in specific regions (adapters)
- **Short reads**: Acceptable if sufficient for your analysis (assembly, variant calling)
- **Contamination 10-15%**: May be acceptable if minor species identified and handled appropriately

**Decision framework**:
1. Review the specific failing metric
2. Check fastp HTML report for quality details
3. Consider your analysis goals
4. Decide if the data quality is sufficient for your purposes
5. Document your decision rationale

### When to REJECT a Failed Sample

- Very low coverage (<5x) - insufficient information
- Very poor Q30% (<50%) - unreliable base calls
- High contamination (>20%) - unreliable species ID
- Mixed species for single-species analysis

## Batch Quality Assessment

After running `qc` on multiple samples, analyze the batch:

```python
import pandas as pd

df = pd.read_csv('bactscout_output/final_summary.csv')

# Batch statistics
print(f"Total samples: {len(df)}")
print(f"PASS rate: {(df['quality_pass'] == 'PASS').sum() / len(df) * 100:.1f}%")

# Coverage distribution
print(f"\nCoverage:")
print(f"  Min: {df['coverage'].min():.1f}x")
print(f"  Mean: {df['coverage'].mean():.1f}x")
print(f"  Max: {df['coverage'].max():.1f}x")

# Q30 distribution
print(f"\nQ30 percentage:")
print(f"  Min: {df['q30_percent'].min():.1f}%")
print(f"  Mean: {df['q30_percent'].mean():.1f}%")
print(f"  Max: {df['q30_percent'].max():.1f}%")

# Species distribution
print(f"\nSpecies distribution:")
print(df['species'].value_counts())

# Failure analysis
if (df['quality_pass'] == 'FAIL').any():
    failed = df[df['quality_pass'] == 'FAIL']
    print(f"\nFailed samples: {len(failed)}")
    print(failed[['sample_id', 'coverage', 'q30_percent', 'mean_read_length', 'contamination_pct']])
```

## See Also

- [Output Format Reference](../usage/output-format.md) - CSV column descriptions
- [Troubleshooting Guide](./troubleshooting.md) - Common issues and solutions
- [Results Analysis Guide](./results-analysis.md) - How to interpret and use results
