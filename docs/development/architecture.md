# Architecture

This document describes the BactScout system design and component interactions.

## System Overview

```
Input FASTQ Files
       ↓
┌──────────────────────────────────────┐
│   BactScout CLI (bactscout.py)      │
│  - Argument parsing                  │
│  - Command routing                   │
└──────────────────┬───────────────────┘
                   ↓
      ┌────────────┴────────────┐
      ↓                         ↓
┌─────────────────┐      ┌─────────────────┐
│   QC Command    │      │ Collect Command │
│  (batch mode)   │      │ (single sample) │
└────────┬────────┘      └────────┬────────┘
         ↓                        ↓
    ┌────┴─────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│      Pipeline Execution (main.py)        │
│  - Locate FASTQ pairs                    │
│  - Preflight validation                  │
│  - Per-sample processing queue           │
└──────────────────┬───────────────────────┘
                   ↓
    ┌──────────────┴──────────────┐
    ↓                             ↓
┌──────────────────┐      ┌──────────────────┐
│  Thread Manager  │      │  Process Manager │
│  (thread.py)     │      │  (multiprocessing)│
└────────┬─────────┘      └──────┬───────────┘
         │                       │
    ┌────┴────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│    Individual Sample Processing         │
│  (run_one_sample - thread.py)           │
└────────┬────────────────────────────────┘
         ↓
    ┌────┴──────────────────────────────┐
    ↓                                   ↓
┌──────────────┐     ┌─────────────────────────────┐
│ QC Metrics   │     │   Species Identification    │
│ fastp        │     │   & Contamination Detection │
│ reads_QC     │     │   sylph, ariba              │
└──────────────┘     └─────────────────────────────┘
         ↓                       ↓
    ┌────┴────────────────────────┘
    ↓
┌──────────────────────────────────┐
│  Result Aggregation              │
│  - Per-sample CSV                │
│  - Merge into final_summary.csv   │
└──────────────────────────────────┘
         ↓
    Output Files
```

## Core Modules

### `bactscout.py` - CLI Entry Point

**Responsibilities**:
- Parse command-line arguments (using Typer)
- Route to appropriate command handler
- Validate input arguments
- Display help text

**Commands**:
- `qc` - Batch quality control
- `collect` - Single sample processing
- `summary` - Generate consolidated report

**Key Functions**:
- `main()` - Application entry point
- `qc()` - Batch QC handler
- `collect()` - Single sample handler
- `summary()` - Report generation handler

### `bactscout/main.py` - Pipeline Logic

**Responsibilities**:
- Locate FASTQ file pairs
- Orchestrate per-sample processing
- Aggregate results
- Handle batch workflows

**Key Functions**:
- `main(input_dir, output_dir, threads, config, skip_preflight)` - Batch processor
- `locate_read_file_pairs(directory)` - Find FASTQ pairs
- Results aggregation and CSV generation

### `bactscout/thread.py` - Sample Processing

**Responsibilities**:
- Execute per-sample analysis pipeline
- Manage tool invocations (fastp, sylph, ARIBA)
- Extract and process metrics
- Handle output files

**Key Functions**:
- `run_one_sample(r1_path, r2_path, output_dir, config, threads)` - Main analysis
- Quality metrics extraction
- Species identification
- MLST typing

### `bactscout/preflight.py` - Input Validation

**Responsibilities**:
- Validate FASTQ file format
- Check file accessibility
- Verify database availability
- Pre-flight system checks

**Key Functions**:
- `run_preflight_checks(input_dir, config, skip)` - Main validation
- File format verification
- Database existence checks

### `bactscout/util.py` - Utilities

**Responsibilities**:
- Common helper functions
- Formatted output
- File utilities
- Configuration helpers

**Key Functions**:
- `extract_sample_name(filename)` - Parse sample ID from filename
- `print_message()` - Rich formatted output
- `print_header()` - Section headers

### `bactscout/summary.py` - Report Generation

**Responsibilities**:
- Read per-sample results
- Aggregate into batch summary
- Apply QC thresholds
- Write consolidated CSV

**Key Functions**:
- `generate_summary(input_dir, output_dir, config)` - Main aggregator
- CSV reading and merging
- Quality determination

## Data Flow

### Batch QC Pipeline (`qc` command)

```
1. Input: Directory with FASTQ files
   ↓
2. Locate file pairs (main.py)
   ├─ Find all *_R1/*.fq* files
   └─ Match with corresponding *_R2 files
   ↓
3. Preflight validation (preflight.py)
   ├─ Check FASTQ format
   ├─ Verify database exists
   └─ Check disk space
   ↓
4. For each sample pair (thread.py):
   ├─ fastp: Quality assessment & filtering
   ├─ Sylph: Species identification
   ├─ ARIBA: MLST typing
   └─ Output: sample_results.csv
   ↓
5. Aggregate results (summary.py)
   ├─ Read all sample_results.csv
   ├─ Apply QC thresholds
   └─ Write final_summary.csv
   ↓
6. Output: results directory with:
   ├─ final_summary.csv
   └─ Sample_*/
       ├─ sample_results.csv
       ├─ fastp_report.html
       ├─ sylph_matches.csv
       └─ stringmlst_results.json
```

### Single Sample Pipeline (`collect` command)

```
1. Input: R1 and R2 FASTQ files
   ↓
2. Extract sample name (util.py)
   ├─ Remove extensions (.fastq.gz, .fq.gz)
   ├─ Remove read indicators (_R1, _R2, _1, _2)
   └─ Return clean sample ID
   ↓
3. Preflight validation (preflight.py)
   ├─ Verify files exist
   ├─ Check FASTQ format
   └─ Verify database exists
   ↓
4. Process sample (thread.py: run_one_sample)
   ├─ fastp: Quality assessment
   ├─ Sylph: Species ID & contamination
   ├─ ARIBA: MLST typing
   └─ Generate: sample_results.csv
   ↓
5. Output: Sample_ID/
   ├─ sample_results.csv
   ├─ fastp_report.html
   ├─ sylph_matches.csv
   └─ stringmlst_results.json
```

### Report Generation (`summary` command)

```
1. Input: Directory with sample results
   ↓
2. Discover samples (summary.py)
   └─ Find all Sample_*/sample_results.csv
   ↓
3. Read and parse (pandas)
   └─ Load each CSV into DataFrame
   ↓
4. Concatenate
   └─ Combine all rows
   ↓
5. Apply thresholds (config.yml)
   ├─ Calculate quality_pass
   └─ Determine PASS/FAIL status
   ↓
6. Output: final_summary.csv
   └─ One row per sample with all metrics
```

## Configuration System

```
bactscout_config.yml (YAML)
     ↓
┌────────────────────────────┐
│  Configuration Dictionary  │
│  (parsed by thread.py)     │
└──────────┬─────────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌────────────┐  ┌──────────────┐
│  QC        │  │  Database    │
│ Thresholds │  │  Paths       │
│ - coverage │  │ - sylph_db   │
│ - q30%     │  │ - mlst_dbs   │
│ - reads    │  │ - metrics    │
│ - contam   │  │              │
└────────────┘  └──────────────┘
     ↓                ↓
  Applied to      Used by
  quality_pass    analysis
  determination   tools
```

## External Tool Integration

### fastp - Read Quality Assessment

```
BactScout              fastp
┌──────────────┐      ┌──────────┐
│ Call fastp   │──→   │ Process  │
│ with FASTQ   │      │ FASTQ    │
└──────────────┘      └────┬─────┘
                           ↓
                    JSON + HTML reports
                    + filtered reads
                           ↓
┌──────────────────┐       │
│ Parse JSON       │←──────┘
│ Extract metrics  │
│ - coverage       │
│ - q30%           │
│ - read_length    │
└──────────────────┘
```

### Sylph - Species Identification & Contamination

```
BactScout              Sylph
┌──────────────┐      ┌────────────┐
│ Call sylph   │──→   │ Compare to │
│ with FASTQ   │      │ GTDB       │
└──────────────┘      └────┬───────┘
                           ↓
                    TSV matches (ANI %)
                           ↓
┌──────────────────┐       │
│ Parse TSV        │←──────┘
│ - Best match     │
│ - ANI score      │
│ - Contamination% │
└──────────────────┘
```

### ARIBA - MLST Typing

```
BactScout              ARIBA
┌──────────────┐      ┌──────────┐
│ Call ARIBA   │──→   │ Allele   │
│ (stringmlst  │      │ calling  │
│ for E. coli) │      │ & typing │
└──────────────┘      └────┬─────┘
                           ↓
                    JSON results
                    (ST + alleles)
                           ↓
┌──────────────────┐       │
│ Parse JSON       │←──────┘
│ Extract:         │
│ - Sequence type  │
│ - Allele profile │
│ - Status         │
└──────────────────┘
```

## Threading Model

### Single-Process, Sequential Processing

**Default behavior**:
```
Main process
├─ Load config
├─ Locate samples
├─ Preflight checks
└─ For each sample:
   ├─ Run fastp
   ├─ Run Sylph
   ├─ Run ARIBA
   ├─ Aggregate results
   └─ Write CSV
```

**Advantages**:
- Simple debugging
- Sequential output
- Low memory overhead

**Disadvantages**:
- Slow for large batches
- Underutilizes multi-core systems

### Future: Parallel Processing

**Potential** (not yet implemented):
```
Main process
├─ Load config
├─ Locate samples
├─ Preflight checks
└─ Thread pool:
   ├─ Worker 1: Sample 1
   ├─ Worker 2: Sample 2
   ├─ Worker 3: Sample 3
   └─ ...Aggregate results
```

## Dependencies

### System Requirements

- Python 3.11+
- Unix-based OS (Linux, macOS, WSL2 on Windows)

### External Tools

- **fastp** - Read QC and trimming
- **Sylph** - k-mer based taxonomic profiling
- **ARIBA** - MLST and resistance gene calling

### Python Packages

Core:
- **Typer** - CLI framework
- **Rich** - Formatted terminal output
- **Pydantic** - Configuration validation
- **Pandas** - Data manipulation

Development:
- **Pytest** - Testing framework
- **Coverage** - Code coverage

## Error Handling

```
Error occurs
     ↓
Try-except block
     ├─ Log error message
     ├─ Print to stderr (Rich)
     └─ Exit with status code
             ↓
┌─────────────┴─────────────┐
↓                           ↓
Recoverable           Non-recoverable
(continue)                 (exit)
```

## Output Organization

```
bactscout_output/
├── final_summary.csv              [Generated by: summary.py]
├── Sample_001/                    [Generated by: thread.py]
│   ├── fastp_report.html          [From fastp]
│   ├── fastp_report.json          [From fastp]
│   ├── reads_QC.json              [Parsed by: thread.py]
│   ├── sample_results.csv         [Generated by: thread.py]
│   ├── sylph_matches.tsv          [From Sylph]
│   ├── sylph_matches.csv          [Converted by: thread.py]
│   ├── stringmlst_results.json    [From ARIBA]
│   └── stringmlst_report.txt      [From ARIBA]
├── Sample_002/
│   └── [same structure]
└── ...
```

## Performance Considerations

### Bottlenecks

1. **I/O Heavy**: FASTQ processing (especially reading/writing)
2. **CPU Heavy**: Sylph k-mer comparison
3. **Memory Heavy**: Loading large reference databases

### Optimization Strategies

1. **Reduce I/O**:
   - Use SSD storage
   - Parallelize sample processing
   - Stream processing where possible

2. **Reduce CPU**:
   - Optimize Sylph parameters
   - Consider pre-filtering

3. **Reduce Memory**:
   - Process fewer samples in parallel
   - Use streaming approaches
   - Compress intermediate files

## Testing Architecture

```
tests/
├── test_fastp.py          [56 tests]
│   ├─ JSON parsing
│   ├─ Edge cases
│   └─ Data extraction
├── test_stringmlst.py     [13 tests]
│   ├─ MLST typing
│   └─ Result parsing
├── test_main.py           [4 tests]
│   └─ Pipeline logic
├── test_file_pairs.py     [10 tests]
│   └─ FASTQ discovery
└── test_bactscout_cli.py  [16 tests]
    └─ CLI interface
```

**Total Coverage**: 98 tests, 100% pass rate

## Extensibility Points

Future extensions could:
1. **Add new analyses**: Create new modules, call from `run_one_sample()`
2. **Add new species**: Update config with new MLST schemes
3. **Add new quality checks**: Extend preflight validation
4. **Change output formats**: Modify `sample_results.csv` generation
5. **Parallelize processing**: Implement ThreadPoolExecutor or multiprocessing

## See Also

- [Testing Guide](./testing.md) - Testing infrastructure
- [Troubleshooting Guide](../guide/troubleshooting.md) - Common issues
- [Configuration Guide](../getting-started/configuration.md) - Config options
