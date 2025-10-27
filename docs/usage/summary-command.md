# Summary Command

The `summary` command generates a consolidated quality control report from multiple samples analyzed with the `qc` or `collect` commands.

## Overview

After processing multiple samples individually or in batches, the `summary` command:
- Reads individual sample result CSVs
- Merges them into a single `final_summary.csv`
- Provides a unified view of all samples
- Enables easy comparison and filtering

## Basic Usage

```bash
# Generate summary from QC output directory
pixi run bactscout summary bactscout_output/

# Specify custom output location
pixi run bactscout summary bactscout_output/ -o /results/

# Use different configuration
pixi run bactscout summary bactscout_output/ -c config.yml
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `input_dir` | ✅ Yes | Directory containing sample subdirectories (output from `qc` or `collect`) |

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `bactscout_output` | Location to write `final_summary.csv` |
| `--config` | `-c` | `bactscout_config.yml` | Configuration file path |

## Input Format

The `summary` command expects the standard output directory structure from `qc` or `collect`:

```
bactscout_output/
├── Sample_001/
│   ├── sample_results.csv          # Per-sample results
│   ├── fastp_report.json
│   ├── sylph_matches.csv
│   └── [other files]
├── Sample_002/
│   ├── sample_results.csv
│   └── ...
├── Sample_003/
│   ├── sample_results.csv
│   └── ...
└── final_summary.csv               # Output file (created by summary command)
```

## Output

### `final_summary.csv`

A consolidated CSV file with one row per sample, containing:

- `sample_id` - Sample identifier
- `species` - Best-matching species
- `coverage` - Mean sequencing depth
- `q30_percent` - Percentage of bases with Q≥30
- `mean_read_length` - Average read length
- `total_bases` - Total sequencing bases
- `gc_content` - GC% of genome
- `reference_size_mbp` - Reference genome size
- `quality_pass` - PASS/FAIL determination
- `contamination_pct` - Contamination percentage
- `mlst_type` - MLST sequence type
- `sequencing_platform` - Detected platform (if available)

See [Output Format](./output-format.md) for detailed column descriptions.

## Usage Scenarios

### Workflow: Batch Processing + Summary

Process all samples, then generate report:

```bash
# 1. Run QC on all samples
pixi run bactscout qc samples/ -o batch_results/ -t 4

# 2. Generate summary
pixi run bactscout summary batch_results/ -o batch_results/
```

Result: `batch_results/final_summary.csv` with all results

### Workflow: Individual Processing + Consolidation

Process samples one at a time over multiple days:

```bash
# Day 1: Process first sample
pixi run bactscout collect day1_R1.gz day1_R2.gz -o results/

# Day 2: Process another sample
pixi run bactscout collect day2_R1.gz day2_R2.gz -o results/

# ... more days ...

# Finally: Generate consolidated report
pixi run bactscout summary results/
```

Result: `results/final_summary.csv` with all samples processed over time

### Workflow: Multi-Location Consolidation

Combine results from different runs or locations:

```bash
# Create combined directory
mkdir consolidated_results/
cp -r facility_A_output/*/ consolidated_results/
cp -r facility_B_output/*/ consolidated_results/

# Generate unified summary
pixi run bactscout summary consolidated_results/
```

Result: `consolidated_results/final_summary.csv` with combined data

## Advanced Usage

### Custom Output File Location

```bash
pixi run bactscout summary bactscout_output/ -o /archive/2024-01-reports/
```

Output: `/archive/2024-01-reports/final_summary.csv`

### Using Different Configuration

For studies with different QC thresholds:

```bash
pixi run bactscout summary results/ -c lenient_config.yml
```

The configuration affects how the `quality_pass` column is determined.

## Analyzing Results

### Load Results in Python

```python
import pandas as pd

df = pd.read_csv('bactscout_output/final_summary.csv')

# View first few samples
print(df.head())

# Quality summary
print(f"Pass rate: {(df['quality_pass'] == 'PASS').sum() / len(df) * 100:.1f}%")

# Species distribution
print(df['species'].value_counts())

# Coverage statistics
print(df['coverage'].describe())
```

### Filter and Export

```python
# Find failed samples
failed = df[df['quality_pass'] == 'FAIL']
failed.to_csv('failed_samples.csv', index=False)

# High contamination samples
contaminated = df[df['contamination_pct'] > 5]
print(f"Samples with >5% contamination: {len(contaminated)}")

# Low coverage samples
low_cov = df[df['coverage'] < 30]
print(f"Samples with <30x coverage: {len(low_cov)}")
```

### Compare Species

```python
# Count species
species_counts = df['species'].value_counts()
print(species_counts)

# Species-specific statistics
for species in df['species'].unique():
    subset = df[df['species'] == species]
    print(f"\n{species}:")
    print(f"  Samples: {len(subset)}")
    print(f"  Avg coverage: {subset['coverage'].mean():.1f}x")
    print(f"  Pass rate: {(subset['quality_pass'] == 'PASS').sum() / len(subset) * 100:.1f}%")
```

## Integration with External Tools

### Export to Excel with Formatting

```python
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill

df = pd.read_csv('bactscout_output/final_summary.csv')

# Write to Excel
excel_file = 'bactscout_summary.xlsx'
df.to_excel(excel_file, sheet_name='Results', index=False)

# Add conditional formatting
wb = openpyxl.load_workbook(excel_file)
ws = wb.active
green_fill = PatternFill(start_color='92D050', end_color='92D050', fill_type='solid')
red_fill = PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')

for row in ws.iter_rows(min_row=2):
    for cell in row:
        if cell.column == 9:  # quality_pass column
            if cell.value == 'PASS':
                cell.fill = green_fill
            else:
                cell.fill = red_fill

wb.save(excel_file)
```

### Generate HTML Report

```python
import pandas as pd

df = pd.read_csv('bactscout_output/final_summary.csv')

html = f"""
<html>
<head>
  <title>BactScout Summary Report</title>
  <style>
    body {{ font-family: Arial; margin: 20px; }}
    table {{ border-collapse: collapse; }}
    th, td {{ border: 1px solid #999; padding: 8px; text-align: left; }}
    th {{ background-color: #4CAF50; color: white; }}
    .pass {{ color: green; font-weight: bold; }}
    .fail {{ color: red; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>BactScout QC Summary</h1>
  <p><strong>Total Samples:</strong> {len(df)}</p>
  <p><strong>Pass Rate:</strong> {(df['quality_pass'] == 'PASS').sum() / len(df) * 100:.1f}%</p>
  {df.to_html(index=False, escape=False)}
</body>
</html>
"""

with open('summary_report.html', 'w') as f:
    f.write(html)
```

## Troubleshooting

### "No results found"

Ensure:
- Directory contains sample subdirectories
- Each subdirectory has `sample_results.csv`
- Path is correct and accessible

### "File permission denied"

Check permissions:
```bash
ls -l bactscout_output/
```

### Empty Summary

Verify sample directories exist and contain results:
```bash
find bactscout_output/ -name "sample_results.csv"
```

See [Troubleshooting Guide](../guide/troubleshooting.md) for more help.
