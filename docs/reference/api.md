# API Reference

This page documents the BactScout Python API for programmatic use.

## Main Module

### `bactscout.main`

Core pipeline functions for batch processing.

#### `main(input_dir, output_dir, threads, config, skip_preflight)`

Run batch quality control analysis on all samples in a directory.

**Parameters:**
- `input_dir` (Path | str): Directory containing FASTQ files
- `output_dir` (Path | str, optional): Output directory (default: "bactscout_output")
- `threads` (int, optional): Number of threads (default: 2)
- `config` (Path | str, optional): Config file path (default: "bactscout_config.yml")
- `skip_preflight` (bool, optional): Skip validation checks (default: False)

**Returns:**
- None

**Raises:**
- `FileNotFoundError`: If input directory doesn't exist
- `ValueError`: If no FASTQ files found

**Example:**
```python
from bactscout.main import main

main(
    input_dir="data/samples/",
    output_dir="results/",
    threads=4,
    skip_preflight=False
)
```

#### `locate_read_file_pairs(directory)`

Find FASTQ file pairs in a directory.

**Parameters:**
- `directory` (Path | str): Directory to search

**Returns:**
- list[tuple]: List of (R1_path, R2_path) tuples

**Raises:**
- `FileNotFoundError`: If directory doesn't exist

**Example:**
```python
from bactscout.main import locate_read_file_pairs

pairs = locate_read_file_pairs("data/samples/")
for r1, r2 in pairs:
    print(f"{r1.name} paired with {r2.name}")
```

## Thread Module

### `bactscout.thread`

Per-sample analysis pipeline.

#### `run_one_sample(r1_path, r2_path, output_dir, config, threads)`

Process a single FASTQ sample pair through the QC pipeline.

**Parameters:**
- `r1_path` (Path | str): Forward read FASTQ file
- `r2_path` (Path | str): Reverse read FASTQ file
- `output_dir` (Path | str): Output directory for results
- `config` (dict): Configuration dictionary
- `threads` (int, optional): Number of threads (default: 2)

**Returns:**
- dict: Sample results with metrics

**Raises:**
- `FileNotFoundError`: If FASTQ files don't exist
- `RuntimeError`: If external tools fail

**Example:**
```python
from bactscout.thread import run_one_sample
import yaml

# Load config
with open("bactscout_config.yml") as f:
    config = yaml.safe_load(f)

# Process sample
results = run_one_sample(
    r1_path="sample_R1.fastq.gz",
    r2_path="sample_R2.fastq.gz",
    output_dir="output/",
    config=config,
    threads=4
)

print(f"Coverage: {results['coverage']}x")
print(f"Species: {results['species']}")
```

## Preflight Module

### `bactscout.preflight`

Input validation and system checks.

#### `run_preflight_checks(input_dir, config, skip)`

Validate inputs before analysis.

**Parameters:**
- `input_dir` (Path | str): Directory to validate
- `config` (dict): Configuration dictionary
- `skip` (bool): Skip checks if True

**Returns:**
- bool: True if all checks pass

**Raises:**
- `ValueError`: If validation fails
- `FileNotFoundError`: If required databases missing

**Example:**
```python
from bactscout.preflight import run_preflight_checks

is_valid = run_preflight_checks(
    input_dir="data/",
    config=config,
    skip=False
)

if is_valid:
    print("✓ All checks passed")
else:
    print("✗ Validation failed")
```

## Utility Module

### `bactscout.util`

Helper functions and utilities.

#### `extract_sample_name(filename)`

Extract clean sample identifier from FASTQ filename.

**Parameters:**
- `filename` (str | Path): FASTQ filename

**Returns:**
- str: Cleaned sample name

**Algorithm:**
1. Remove extensions (.fastq, .fq, .gz)
2. Remove read indicators (_R1, _R2, _1, _2)
3. Return clean name

**Example:**
```python
from bactscout.util import extract_sample_name

# Examples
extract_sample_name("sample_001_R1.fastq.gz")  # "sample_001"
extract_sample_name("isolate_ABC_1.fq.gz")    # "isolate_ABC"
extract_sample_name("data_R1.fastq")          # "data"
```

#### `print_message(text, emoji=None, color=None)`

Print formatted message using Rich.

**Parameters:**
- `text` (str): Message text
- `emoji` (str, optional): Emoji to prepend
- `color` (str, optional): Color name

**Example:**
```python
from bactscout.util import print_message

print_message("Analysis complete", emoji="✓", color="green")
print_message("Warning message", emoji="⚠", color="yellow")
```

#### `print_header(text, level=1)`

Print formatted section header.

**Parameters:**
- `text` (str): Header text
- `level` (int): Header level (1-3)

**Example:**
```python
from bactscout.util import print_header

print_header("Quality Control Results", level=1)
print_header("Per-Sample Analysis", level=2)
```

## Summary Module

### `bactscout.summary`

Report generation and aggregation.

#### `generate_summary(input_dir, output_dir, config)`

Generate consolidated summary from per-sample results.

**Parameters:**
- `input_dir` (Path | str): Directory with sample results
- `output_dir` (Path | str): Output directory
- `config` (dict): Configuration dictionary

**Returns:**
- None (writes final_summary.csv)

**Example:**
```python
from bactscout.summary import generate_summary

generate_summary(
    input_dir="bactscout_output/",
    output_dir="bactscout_output/",
    config=config
)

print("Summary written to: bactscout_output/final_summary.csv")
```

## Data Models

### Configuration Dictionary

```python
{
    # Database paths
    "bactscout_dbs_path": "bactscout_dbs",
    "sylph_db": "gtdb-r226-c1000-dbv1.syldb",
    "metrics_file": "filtered_metrics.csv",
    
    # QC thresholds
    "coverage_threshold": 30,
    "contamination_threshold": 10,
    "q30_pass_threshold": 0.80,
    "read_length_pass_threshold": 100,
    
    # MLST species
    "mlst_species": {
        "escherichia_coli": "Escherichia coli#1",
        "salmonella_enterica": "Salmonella enterica",
        # ...
    },
    
    # System resources
    "system_resources": {
        "cpus": 2,
        "memory": "4.GB"
    }
}
```

### Results Dictionary

```python
{
    "sample_id": "sample_001",
    "species": "Escherichia coli",
    "coverage": 45.3,
    "q30_percent": 0.89,
    "mean_read_length": 150.0,
    "total_bases": 225_000_000,
    "gc_content": 50.5,
    "reference_size_mbp": 4.97,
    "quality_pass": "PASS",
    "contamination_pct": 2.1,
    "mlst_type": "ST-10",
    "sequencing_platform": "Illumina"
}
```

## Usage Examples

### Basic Batch Processing

```python
from bactscout.main import main
import yaml

# Load configuration
with open("bactscout_config.yml") as f:
    config = yaml.safe_load(f)

# Run batch analysis
main(
    input_dir="data/samples/",
    output_dir="results/",
    threads=8,
    skip_preflight=False
)

# Results available in:
# - results/final_summary.csv
# - results/Sample_*/sample_results.csv
```

### Process Single Sample

```python
from bactscout.thread import run_one_sample
from bactscout.util import extract_sample_name
import yaml

# Load configuration
with open("bactscout_config.yml") as f:
    config = yaml.safe_load(f)

# Process single sample
r1 = "sample_R1.fastq.gz"
r2 = "sample_R2.fastq.gz"
sample_name = extract_sample_name(r1)

results = run_one_sample(
    r1_path=r1,
    r2_path=r2,
    output_dir=f"output/{sample_name}/",
    config=config,
    threads=4
)

# Access results
print(f"Species: {results['species']}")
print(f"Coverage: {results['coverage']}x")
print(f"Quality: {results['quality_pass']}")
```

### Analyze Results

```python
import pandas as pd

# Load results
df = pd.read_csv("bactscout_output/final_summary.csv")

# Filter high-quality samples
hq = df[df['quality_pass'] == 'PASS']

# Species distribution
print(df['species'].value_counts())

# Coverage statistics
print(f"Mean coverage: {df['coverage'].mean():.1f}x")
print(f"Min coverage: {df['coverage'].min():.1f}x")
print(f"Max coverage: {df['coverage'].max():.1f}x")

# Find contaminated samples
contaminated = df[df['contamination_pct'] > 5]
print(f"Contaminated samples: {len(contaminated)}")
```

### Custom Pipeline

```python
from pathlib import Path
from bactscout.main import locate_read_file_pairs
from bactscout.thread import run_one_sample
from bactscout.util import extract_sample_name
import yaml

# Load config
with open("bactscout_config.yml") as f:
    config = yaml.safe_load(f)

# Find all samples
pairs = locate_read_file_pairs("data/samples/")

all_results = []

# Process each sample
for r1, r2 in pairs:
    sample_name = extract_sample_name(r1.name)
    output_dir = Path("output") / sample_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Processing {sample_name}...")
    
    results = run_one_sample(
        r1_path=r1,
        r2_path=r2,
        output_dir=output_dir,
        config=config,
        threads=4
    )
    
    all_results.append(results)
    print(f"  ✓ {sample_name}: {results['species']}")

# Aggregate results
import pandas as pd
df = pd.DataFrame(all_results)
df.to_csv("all_results.csv", index=False)
print(f"\nProcessed {len(all_results)} samples")
```

## Error Handling

### Common Exceptions

```python
from bactscout.main import main

try:
    main(input_dir="data/", threads=4)
except FileNotFoundError as e:
    print(f"Input directory not found: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Pipeline error: {e}")
```

## Performance Considerations

### Memory Usage

```python
# Reduce memory usage with fewer threads
results = run_one_sample(
    r1_path=r1,
    r2_path=r2,
    output_dir=output_dir,
    config=config,
    threads=2  # Lower number = less memory
)
```

### Batch Processing

```python
# Process multiple batches sequentially
from pathlib import Path

for batch_dir in Path("data/").glob("batch_*"):
    main(
        input_dir=batch_dir,
        output_dir=f"results/{batch_dir.name}/",
        threads=4
    )
```
