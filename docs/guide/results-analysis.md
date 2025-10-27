# Results Analysis Guide

This guide explains how to analyze and interpret BactScout results for common use cases.

## Getting Started with Results

After running BactScout, results are organized as follows:

```
bactscout_output/
├── final_summary.csv        # All samples in one file
├── Sample_001/              # Individual sample directories
│   ├── sample_results.csv   # Per-sample metrics
│   ├── fastp_report.html    # Interactive QC report
│   ├── sylph_matches.csv    # Species identification
│   └── stringmlst_results.json  # Strain typing
├── Sample_002/
└── ...
```

## Common Analysis Tasks

### 1. Quick Overview of Results

**Load and summarize all results**:

```python
import pandas as pd

# Load final summary
df = pd.read_csv('bactscout_output/final_summary.csv')

print(f"Total samples: {len(df)}")
print(f"✓ Passed QC: {(df['quality_pass'] == 'PASS').sum()}")
print(f"✗ Failed QC: {(df['quality_pass'] == 'FAIL').sum()}")

# Show basic statistics
print("\nSequencing depth (coverage):")
print(df['coverage'].describe())

print("\nBase quality (Q30%):")
print(df['q30_percent'].describe())

# Show first few rows
print("\nFirst 5 samples:")
print(df[['sample_id', 'species', 'coverage', 'quality_pass']].head())
```

### 2. Identify High-Quality Samples

```python
# Find all samples that passed QC
high_quality = df[df['quality_pass'] == 'PASS']
print(f"High-quality samples: {len(high_quality)}")

# Show top samples by coverage
top_coverage = df.nlargest(5, 'coverage')[['sample_id', 'coverage', 'species']]
print("\nHighest coverage samples:")
print(top_coverage)

# Show top samples by Q30%
top_quality = df.nlargest(5, 'q30_percent')[['sample_id', 'q30_percent', 'species']]
print("\nHighest quality samples:")
print(top_quality)
```

### 3. Investigate Failed Samples

```python
# Find failed samples
failed = df[df['quality_pass'] == 'FAIL'].copy()
print(f"Failed samples: {len(failed)}\n")

# Find which metric caused failure
for idx, row in failed.iterrows():
    failures = []
    if row['coverage'] < 30:
        failures.append(f"low coverage ({row['coverage']:.1f}x)")
    if row['q30_percent'] < 0.80:
        failures.append(f"low Q30 ({row['q30_percent']:.1f}%)")
    if row['mean_read_length'] < 100:
        failures.append(f"short reads ({row['mean_read_length']:.0f}bp)")
    if row['contamination_pct'] > 10:
        failures.append(f"contamination ({row['contamination_pct']:.1f}%)")
    
    print(f"{row['sample_id']}: {', '.join(failures)}")
```

### 4. Species-Specific Analysis

```python
# Species distribution
print("Species found:")
species_dist = df['species'].value_counts()
print(species_dist)

# For each species, show statistics
print("\n\nDetailed species statistics:")
for species in df['species'].unique():
    subset = df[df['species'] == species]
    print(f"\n{species}:")
    print(f"  Samples: {len(subset)}")
    print(f"  Pass rate: {(subset['quality_pass'] == 'PASS').sum() / len(subset) * 100:.1f}%")
    print(f"  Coverage: {subset['coverage'].mean():.1f}x (range: {subset['coverage'].min():.1f}-{subset['coverage'].max():.1f})")
    print(f"  Q30%: {subset['q30_percent'].mean():.1f}% (range: {subset['q30_percent'].min():.1f}-{subset['q30_percent'].max():.1f})")
```

### 5. Contamination Analysis

```python
# Find contaminated samples
contaminated = df[df['contamination_pct'] > 5].copy()
print(f"Samples with >5% contamination: {len(contaminated)}\n")

# Show details
for idx, row in contaminated.iterrows():
    print(f"{row['sample_id']}:")
    print(f"  Primary species: {row['species']}")
    print(f"  Contamination: {row['contamination_pct']:.1f}%")

# If more detail needed, check individual sylph files
import json
for idx, row in contaminated.head(3).iterrows():
    sample_id = row['sample_id']
    print(f"\n{sample_id} - Sylph matches:")
    try:
        sylph_df = pd.read_csv(f'bactscout_output/{sample_id}/sylph_matches.csv')
        print(sylph_df[['ref_name', 'ani', 'match_percent']].head())
    except:
        print("  (could not read sylph results)")
```

### 6. MLST/Strain Analysis

```python
# Show MLST types found
print("MLST types in dataset:")
mlst_counts = df['mlst_type'].value_counts()
print(mlst_counts)

# Find samples of specific strain
# Example: find all E. coli ST-10
ecoli = df[df['species'] == 'Escherichia coli']
st10 = ecoli[ecoli['mlst_type'] == 'ST-10']
print(f"\nE. coli ST-10 samples: {len(st10)}")

# Show these samples
if len(st10) > 0:
    print(st10[['sample_id', 'coverage', 'quality_pass']])

# Identify clonal outbreaks
print("\n\nPotential outbreak detection:")
for species in df['species'].unique():
    species_data = df[df['species'] == species]
    # Find STs with multiple samples
    st_counts = species_data['mlst_type'].value_counts()
    common_sts = st_counts[st_counts > 1]
    if len(common_sts) > 0:
        print(f"\n{species}:")
        for st, count in common_sts.items():
            print(f"  {st}: {count} samples")
```

### 7. Export Results for Downstream Analysis

**Export failed samples for review**:

```python
failed = df[df['quality_pass'] == 'FAIL']
failed.to_csv('review_failed_samples.csv', index=False)
print("Exported to review_failed_samples.csv")
```

**Export high-quality E. coli for genomic analysis**:

```python
ecoli_hq = df[(df['species'] == 'Escherichia coli') & (df['quality_pass'] == 'PASS')]
sample_list = ecoli_hq['sample_id'].tolist()

with open('ecoli_samples_for_wgs.txt', 'w') as f:
    for sample in sample_list:
        f.write(f"{sample}\n")
        
print(f"Exported {len(sample_list)} E. coli samples")
```

**Create sample sheet for downstream pipeline**:

```python
# Create manifest with FASTQ paths for assembly
hq_samples = df[df['quality_pass'] == 'PASS']

manifest_data = []
for idx, row in hq_samples.iterrows():
    sample_id = row['sample_id']
    # Note: Assumes original FASTQ files are in a known location
    manifest_data.append({
        'sample_id': sample_id,
        'species': row['species'],
        'r1': f'data/{sample_id}_R1.fastq.gz',
        'r2': f'data/{sample_id}_R2.fastq.gz',
        'coverage': row['coverage'],
        'mlst_type': row['mlst_type']
    })

manifest_df = pd.DataFrame(manifest_data)
manifest_df.to_csv('assembly_manifest.csv', index=False)
print("Created assembly_manifest.csv")
```

## Data Integration

### Combine BactScout Results with External Data

**Merge with epidemiological data**:

```python
# Your epidemiological data
epi_data = pd.read_csv('epidemiology_data.csv')  # Has columns: sample_id, location, date

# Merge with BactScout results
merged = df.merge(epi_data, on='sample_id', how='left')

# Analyze by location
print("Results by location:")
for location in merged['location'].unique():
    loc_data = merged[merged['location'] == location]
    print(f"\n{location}:")
    print(f"  Total samples: {len(loc_data)}")
    print(f"  Pass rate: {(loc_data['quality_pass'] == 'PASS').sum() / len(loc_data) * 100:.1f}%")
    print(f"  Species: {loc_data['species'].value_counts().to_dict()}")
    print(f"  Mean coverage: {loc_data['coverage'].mean():.1f}x")
```

**Track temporal patterns**:

```python
# Assuming you have dates
merged['date'] = pd.to_datetime(merged['date'])

# Plot quality over time
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Coverage over time
axes[0, 0].scatter(merged['date'], merged['coverage'], alpha=0.6)
axes[0, 0].axhline(y=30, color='r', linestyle='--', label='Threshold')
axes[0, 0].set_ylabel('Coverage (x)')
axes[0, 0].set_title('Coverage Over Time')
axes[0, 0].legend()

# Q30% over time
axes[0, 1].scatter(merged['date'], merged['q30_percent'] * 100, alpha=0.6)
axes[0, 1].axhline(y=80, color='r', linestyle='--', label='Threshold')
axes[0, 1].set_ylabel('Q30%')
axes[0, 1].set_title('Base Quality Over Time')
axes[0, 1].legend()

# Pass/Fail over time
pass_fail = merged.groupby([merged['date'].dt.to_period('W'), 'quality_pass']).size().unstack()
pass_fail.plot(ax=axes[1, 0], kind='bar', stacked=True)
axes[1, 0].set_ylabel('Number of Samples')
axes[1, 0].set_title('Pass/Fail by Week')

# Species over time
species_time = merged.groupby([merged['date'].dt.to_period('W'), 'species']).size().unstack()
species_time.plot(ax=axes[1, 1], kind='bar', stacked=True)
axes[1, 1].set_ylabel('Number of Samples')
axes[1, 1].set_title('Species Distribution Over Time')

plt.tight_layout()
plt.savefig('temporal_analysis.png', dpi=100)
print("Saved temporal_analysis.png")
```

## Report Generation

### Create Summary Report

```python
import pandas as pd
from datetime import datetime

df = pd.read_csv('bactscout_output/final_summary.csv')

# Generate HTML report
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>BactScout Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .metric {{ background-color: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }}
        .pass {{ color: #27ae60; font-weight: bold; }}
        .fail {{ color: #e74c3c; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
        th {{ background-color: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BactScout Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="metric">
        <h2>Summary Statistics</h2>
        <p><strong>Total Samples:</strong> {len(df)}</p>
        <p><strong>Samples Passed QC:</strong> <span class="pass">{(df['quality_pass'] == 'PASS').sum()} ({(df['quality_pass'] == 'PASS').sum() / len(df) * 100:.1f}%)</span></p>
        <p><strong>Samples Failed QC:</strong> <span class="fail">{(df['quality_pass'] == 'FAIL').sum()} ({(df['quality_pass'] == 'FAIL').sum() / len(df) * 100:.1f}%)</span></p>
    </div>
    
    <div class="metric">
        <h2>Sequencing Metrics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Min</th>
                <th>Mean</th>
                <th>Max</th>
                <th>Median</th>
            </tr>
            <tr>
                <td>Coverage (x)</td>
                <td>{df['coverage'].min():.1f}</td>
                <td>{df['coverage'].mean():.1f}</td>
                <td>{df['coverage'].max():.1f}</td>
                <td>{df['coverage'].median():.1f}</td>
            </tr>
            <tr>
                <td>Q30%</td>
                <td>{df['q30_percent'].min():.1f}</td>
                <td>{df['q30_percent'].mean():.1f}</td>
                <td>{df['q30_percent'].max():.1f}</td>
                <td>{df['q30_percent'].median():.1f}</td>
            </tr>
            <tr>
                <td>Read Length (bp)</td>
                <td>{df['mean_read_length'].min():.0f}</td>
                <td>{df['mean_read_length'].mean():.0f}</td>
                <td>{df['mean_read_length'].max():.0f}</td>
                <td>{df['mean_read_length'].median():.0f}</td>
            </tr>
            <tr>
                <td>Contamination %</td>
                <td>{df['contamination_pct'].min():.1f}</td>
                <td>{df['contamination_pct'].mean():.1f}</td>
                <td>{df['contamination_pct'].max():.1f}</td>
                <td>{df['contamination_pct'].median():.1f}</td>
            </tr>
        </table>
    </div>
    
    <div class="metric">
        <h2>Species Distribution</h2>
        <table>
            <tr><th>Species</th><th>Count</th><th>Pass Rate</th></tr>
            {chr(10).join([f"<tr><td>{sp}</td><td>{cnt}</td><td>{(df[df['species'] == sp]['quality_pass'] == 'PASS').sum() / cnt * 100:.1f}%</td></tr>" for sp, cnt in df['species'].value_counts().items()])}
        </table>
    </div>
    
    <div class="metric">
        <h2>Failed Samples</h2>
        {df[df['quality_pass'] == 'FAIL'][['sample_id', 'species', 'coverage', 'q30_percent', 'contamination_pct']].to_html(index=False) if (df['quality_pass'] == 'FAIL').any() else '<p>All samples passed QC ✓</p>'}
    </div>
</body>
</html>
"""

with open('bactscout_report.html', 'w') as f:
    f.write(html_content)

print("Report saved to bactscout_report.html")
```

## Advanced Analysis

### Quality Score Distribution

```python
import json

# Collect quality metrics across all samples
all_metrics = []

for idx, row in df.iterrows():
    sample_id = row['sample_id']
    try:
        with open(f'bactscout_output/{sample_id}/reads_QC.json') as f:
            metrics = json.load(f)
            metrics['sample_id'] = sample_id
            all_metrics.append(metrics)
    except:
        pass

# Analyze patterns
metrics_df = pd.DataFrame(all_metrics)
print("Quality score distribution:")
print(metrics_df[['sample_id', 'mean_read_length', 'q30_bases_pct', 'gc_content_pct']].describe())
```

### Identify Samples for Specific Downstream Analysis

```python
# For de novo assembly (high coverage, good quality)
assembly_ready = df[(df['coverage'] >= 50) & (df['q30_percent'] >= 0.85) & (df['quality_pass'] == 'PASS')]
print(f"Samples ready for assembly: {len(assembly_ready)}")

# For SNP analysis (high coverage, strict contamination)
snp_ready = df[(df['coverage'] >= 100) & (df['contamination_pct'] < 2) & (df['quality_pass'] == 'PASS')]
print(f"Samples ready for SNP analysis: {len(snp_ready)}")

# For epidemiology (just need species ID)
epidemiology_data = df[df['quality_pass'] == 'PASS'][['sample_id', 'species', 'mlst_type']]
print(f"Samples with valid epidemiology data: {len(epidemiology_data)}")
```

## See Also

- [Quality Control Guide](./quality-control.md) - Understanding QC metrics
- [Output Format Reference](../usage/output-format.md) - Column descriptions
- [Troubleshooting Guide](./troubleshooting.md) - Solving common problems
