# Troubleshooting Guide

This guide covers common issues and solutions when using BactScout.

## Installation and Setup

### "pixi command not found"

**Problem**: Pixi is not installed or not in PATH.

**Solution**:
```bash
# Install Pixi (macOS/Linux)
curl -fsSL https://pixi.sh/install.sh | bash

# Or with Homebrew
brew install pixi

# Verify installation
pixi --version
```

See [Installation Guide](../getting-started/installation.md) for details.

### "Cannot find project at current location"

**Problem**: Pixi cannot find `pixi.toml`.

**Solution**:
```bash
# Make sure you're in the BactScout directory
pwd  # Should show /path/to/bactscout

# Check if pixi.toml exists
ls pixi.toml

# If not, you're in the wrong directory
cd /path/to/bactscout
```

### "Dependencies not installed"

**Problem**: Error about missing packages when running BactScout.

**Solution**:
```bash
# Reinstall dependencies
pixi install

# Or recreate environment
rm -rf .pixi
pixi install
```

## Running BactScout

### "No FASTQ files found"

**Problem**: QC command says no FASTQ files in directory.

**Cause**: Files don't match expected naming pattern or file extension.

**Solution**:
```bash
# Check what files you have
ls -la data/

# Expected patterns
# Good:  sample_001_R1.fastq.gz, sample_001_R2.fastq.gz
#        sample_001_R1.fq.gz,     sample_001_R2.fq.gz
#        sample_001_1.fastq.gz,   sample_001_2.fastq.gz

# Bad:   sample_001_1.fastq (not compressed)
#        sample_001.R1.fastq.gz   (period instead of underscore)
#        sample_001.fastq.gz      (no R1/R2 indicator)

# Rename files if needed
mv sample_001.R1.fastq.gz sample_001_R1.fastq.gz
mv sample_001.R2.fastq.gz sample_001_R2.fastq.gz
```

### "Invalid argument: R1/R2 files required"

**Problem**: Using `collect` command incorrectly.

**Cause**: Not providing two separate files (R1 and R2).

**Solution**:
```bash
# Correct usage
pixi run bactscout collect sample_R1.fastq.gz sample_R2.fastq.gz

# Wrong: providing directory
pixi run bactscout collect /path/to/data/  # ❌ This is for 'qc' command

# Wrong: only one file
pixi run bactscout collect sample_R1.fastq.gz  # ❌ Need R2 as well

# Wrong: files in wrong order
pixi run bactscout collect sample_R2.fastq.gz sample_R1.fastq.gz  # ❌ R1 must be first
```

### "Thread count must be positive"

**Problem**: Invalid thread argument.

**Solution**:
```bash
# Use positive integer
pixi run bactscout qc data/ -t 4   # ✓ Good

# Not these:
pixi run bactscout qc data/ -t 0   # ❌ Must be >= 1
pixi run bactscout qc data/ -t -1  # ❌ Must be positive
pixi run bactscout qc data/ -t 3.5 # ❌ Must be integer
```

### "Cannot find database"

**Problem**: Reference database not found.

**Cause**: Database files missing or path incorrect in config.

**Solution**:
```bash
# Ensure bactscout_dbs directory exists
ls bactscout_dbs/

# Should contain:
# - gtdb-r226-c1000-dbv1.syldb
# - filtered_metrics.csv
# - acinetobacter_baumannii/
# - escherichia_coli/
# - etc.

# If missing, download:
# Databases auto-download on first run, or manually:
cd bactscout_dbs/
# Download from configured URL in bactscout_config.yml
```

### "Out of memory" error

**Problem**: BactScout uses too much RAM.

**Cause**: Too many threads or insufficient system memory.

**Solution**:
```bash
# Reduce thread count
pixi run bactscout qc data/ -t 2   # Use fewer threads

# Check available memory
free -h  # Linux
vm_stat # macOS

# Stop other programs to free memory
# Consider running on a system with more RAM
```

### "Permission denied" errors

**Problem**: Cannot write to output directory.

**Cause**: Insufficient permissions.

**Solution**:
```bash
# Check permissions
ls -ld bactscout_output/

# Make directory writable
chmod u+w bactscout_output/

# Or remove and recreate
rm -rf bactscout_output/
mkdir bactscout_output/

# Check input file permissions too
chmod u+r data/*.fastq.gz
```

## Quality Control Issues

### Sample fails QC with low coverage

**Problem**: `coverage` < 30x threshold.

**Solution**:
```bash
# 1. Check if this is expected
coverage=$(grep "coverage" sample_results.csv | cut -d',' -f3)
echo "Coverage: ${coverage}x"

# 2. Options:
#    a) Re-sequence with more depth
#    b) Lower threshold if intentional (edit bactscout_config.yml)
#    c) Check if sample name is correct (contamination mix-up?)

# 3. Verify reads exist
zcat data/sample_R1.fastq.gz | wc -l  # Divide by 4 for read count
```

### Sample fails QC with low Q30%

**Problem**: `q30_percent` < 80% threshold.

**Solution**:
```bash
# 1. Check fastp report for details
# Open: bactscout_output/Sample_XXX/fastp_report.html in browser

# 2. Check where quality drops
# Quality often drops at ends of reads (normal)

# 3. Options:
#    a) Check sequencing run quality
#    b) Verify samples are not degraded
#    c) Lower threshold if marginal (edit bactscout_config.yml)
#    d) Consider pre-trimming with stricter fastp settings
```

### Sample fails QC with short reads

**Problem**: `mean_read_length` < 100 bp threshold.

**Cause**: DNA degradation, library prep issues, or platform limitation.

**Solution**:
```bash
# 1. Check read length distribution
# Open: bactscout_output/Sample_XXX/fastp_report.html

# 2. If reads are fragmented:
#    - Verify DNA extraction quality
#    - Check storage conditions
#    - Re-extract if necessary

# 3. Options:
#    a) Re-sequence
#    b) Lower threshold if using platform with shorter reads (edit config)
#    c) Use aggressive trimming to remove low-quality ends
```

### Sample fails QC with high contamination

**Problem**: `contamination_pct` > 10% threshold.

**Solution**:
```bash
# 1. Check what contamination was detected
# Look at: bactscout_output/Sample_XXX/sylph_matches.csv
cat bactscout_output/Sample_XXX/sylph_matches.csv

# 2. Check if it's a real contaminant or misidentification
# - Is the secondary species plausible?
# - Are there mixed strains?

# 3. Options:
#    a) If mixed strains: separate and re-sequence if possible
#    b) If environmental contamination: verify extraction protocol
#    c) If sequencing artifact: lower threshold (edit config)
#    d) Check cross-contamination during library prep

# 4. Investigate further
head bactscout_output/Sample_XXX/reads_QC.json
```

## Species Identification Issues

### "No species identified" or "Unknown species"

**Problem**: Sylph couldn't find matching species.

**Cause**: 
- Species not in GTDB database
- Very divergent organism
- Contaminated/degraded sample

**Solution**:
```bash
# 1. Check what Sylph found
cat bactscout_output/Sample_XXX/sylph_matches.csv

# 2. Check coverage and contamination
# Low coverage or high contamination = poor identification

# 3. Manual verification:
#    - BLAST the reads/assembly against NCBI
#    - Check 16S rRNA gene identification
#    - Use GTDB-Tk for reference mapping

# 4. If organism is rare:
#    - May not be in GTDB
#    - Consider adding custom references
```

### "Multiple species detected" (unexpected)

**Problem**: Sylph found multiple species with similar scores.

**Cause**: 
- True mixed sample
- Closely related species
- Sequencing contamination

**Solution**:
```bash
# 1. Check matched species
cat bactscout_output/Sample_XXX/sylph_matches.csv | head -10

# 2. Calculate ANI differences
# If primary and secondary very close → may need additional analysis
# If primary clearly dominant → first species is likely correct

# 3. For mixed samples (known):
#    - Consider separate analysis per species
#    - Use dedicated metagenomics tools
#    - Increase read depth for better separation

# 4. For unexpected contamination:
#    - Review sample history
#    - Check for cross-contamination
#    - Re-extract if necessary
```

## MLST Issues

### "No MLST result" or "Invalid MLST"

**Problem**: MLST typing failed or returned invalid result.

**Cause**:
- Species doesn't have MLST scheme
- Incomplete alleles in sample
- MLST database issue

**Solution**:
```bash
# 1. Check which species was identified
grep "species" bactscout_output/Sample_XXX/sample_results.csv

# 2. Check if MLST scheme exists for this species
# BactScout includes schemes for:
# - Escherichia coli
# - Salmonella enterica
# - Klebsiella pneumoniae
# - Acinetobacter baumannii
# - Pseudomonas aeruginosa

# 3. If species not in list:
#    - MLST scheme may not be available
#    - Check if genus/species name is exact
#    - Consider adding custom MLST database

# 4. If scheme exists but typing failed:
#    - Check coverage of housekeeping genes
#    - Verify sample quality
#    - Check for incompleteness
cat bactscout_output/Sample_XXX/stringmlst_results.json | grep -E "status|st"
```

### "Partial alleles detected"

**Problem**: MLST result is incomplete (some alleles missing).

**Cause**: 
- Low coverage over some genes
- Sequence divergence
- Sample contamination

**Solution**:
```bash
# 1. Check MLST report
cat bactscout_output/Sample_XXX/stringmlst_report.txt

# 2. If coverage is low:
#    - Re-sequence with higher depth
#    - Check if genes are present at all

# 3. If sequence diverged:
#    - May be novel ST (good for epidemiology!)
#    - Report as incomplete/novel
#    - Consider sequence-based typing instead
```

## Output and Analysis Issues

### "final_summary.csv not created"

**Problem**: Summary command didn't generate output.

**Cause**: 
- No sample results found
- Permission issues
- Path problems

**Solution**:
```bash
# 1. Check if sample directories and results exist
find bactscout_output/ -name "sample_results.csv"

# 2. Verify directory structure
ls -la bactscout_output/

# 3. Check permissions
ls -ld bactscout_output/
chmod u+w bactscout_output/

# 4. Run summary command with explicit paths
pixi run bactscout summary /full/path/to/bactscout_output/ -o /full/path/to/bactscout_output/

# 5. Check for error messages
pixi run bactscout summary bactscout_output/ 2>&1
```

### "CSV file is corrupted or incomplete"

**Problem**: Can't read output CSV files.

**Cause**: Process interrupted, disk full, or permission issue.

**Solution**:
```bash
# 1. Check file integrity
head bactscout_output/final_summary.csv
tail bactscout_output/final_summary.csv

# 2. Check if file is complete (ends with newline)
wc -l bactscout_output/final_summary.csv

# 3. Try re-running analysis
rm bactscout_output/final_summary.csv
pixi run bactscout summary bactscout_output/

# 4. Check disk space
df -h .

# 5. If corrupted beyond repair, re-run QC
```

## Platform-Specific Issues

### macOS: "Library not found"

**Problem**: Missing dylib or framework.

**Solution**:
```bash
# Update pixi environment
pixi install

# Ensure Xcode command line tools are installed
xcode-select --install

# Try clean reinstall
rm -rf .pixi
pixi install
```

### Linux: "GLIBC version mismatch"

**Problem**: Incompatible C library version.

**Solution**:
```bash
# Use pixi environment
pixi run bactscout --version

# Or check GLIBC version
ldd --version

# May need to update OS dependencies
# For Ubuntu/Debian:
sudo apt-get update && sudo apt-get upgrade
```

### Docker: "Cannot allocate memory"

**Problem**: Docker container runs out of memory.

**Solution**:
```bash
# Increase Docker memory limit
# In Docker Desktop settings, increase available memory

# Or limit threads in BactScout
docker run ... bactscout qc data/ -t 2
```

## Data and File Issues

### "FASTQ files are corrupted"

**Problem**: Error reading input files.

**Solution**:
```bash
# Test FASTQ file integrity
gunzip -t data/sample_R1.fastq.gz  # No output = OK

# If corrupted, re-download or re-sequence

# Or try fixing with fas toolkit
# (if gzip is corrupted but FASTQ is ok)
zcat data/sample_R1.fastq.gz > sample_R1.fastq  # Decompress to test
head -1000 sample_R1.fastq | grep "^@"  # Check FASTQ format
```

### "Sample name not detected correctly"

**Problem**: Output directory has wrong sample name.

**Cause**: Unexpected filename format.

**Solution**:
```bash
# Sample name extraction removes:
# - Extensions: .fastq, .fq, .gz
# - Read indicators: _R1, _R2, _1, _2

# Example transformations:
# sample_001_R1.fastq.gz  → sample_001
# 2024-01-abc_R1.fq.gz   → 2024-01-abc
# isolate_1.fastq.gz     → isolate

# If extraction fails:
# 1. Rename file to include sample identifier
#    Example: data/isolate_ABC_R1.fastq.gz
# 2. Use standard naming conventions
# 3. Check output directory name and rename if needed

mv bactscout_output/Sample_unknown/ bactscout_output/Sample_correct_name/
```

## Getting Help

### If you can't solve the issue:

1. **Check log files** (if running in batch mode):
   ```bash
   tail -f bactscout_output/bactscout.log  # If log file exists
   ```

2. **Enable verbose output**:
   - Run with `--skip-preflight` to skip validation
   - Check full error output without truncation

3. **Reproduce with minimal data**:
   - Run on single sample to isolate issue
   - Use smaller test files if possible

4. **Check GitHub**:
   - [BactScout Issues](https://github.com/nfareed/bactscout/issues)
   - Search for similar issues
   - Include error output and system info

5. **Report an issue**:
   - Provide BactScout version: `pixi run bactscout --version`
   - Include command used
   - Include error message and log output
   - Include system info: `uname -a`
   - Attach sample data if possible (anonymize if needed)

## See Also

- [Quality Control Guide](./quality-control.md) - Understanding QC metrics
- [Installation Guide](../getting-started/installation.md) - Setup help
- [Configuration Guide](../getting-started/configuration.md) - Config options
