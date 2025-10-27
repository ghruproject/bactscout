# Frequently Asked Questions

## Installation & Setup

### Q: Do I need to install all the dependencies myself?
**A:** No! Pixi handles this automatically. Just install Pixi, run `pixi install`, and all dependencies (fastp, Sylph, ARIBA, etc.) are installed in an isolated environment.

### Q: Can I use BactScout with conda or pip?
**A:** While it's technically possible, we strongly recommend Pixi for:
- Reproducibility (lock files)
- Isolated environments (no conflicts)
- Automatic package downloads
- CI/CD compatibility

If you prefer conda/pip, you'll need to manually install: Python 3.11+, fastp, sylph, ariba, stringmlst, and required Python packages.

### Q: Can I run BactScout on Windows?
**A:** Not directly - BactScout uses Unix-based tools (fastp, Sylph, ARIBA). Options:
- Use **WSL2** (Windows Subsystem for Linux 2)
- Use **Docker** for Windows
- Run on a Linux system

### Q: How much disk space do I need?
**A:** 
- BactScout installation: ~2-3 GB (with dependencies)
- Reference databases: ~20-30 GB
- Per sample output: ~500 MB - 2 GB (varies with read depth)
- Typical batch (100 samples): ~100-200 GB including databases

## Running BactScout

### Q: What's the difference between `qc` and `collect`?
**A:**
- `qc`: Process multiple samples in a directory (batch mode)
- `collect`: Process a single pair of FASTQ files (single sample mode)

Use `qc` for high-throughput screening, `collect` for individual samples or integration.

### Q: How long does analysis take?
**A:** Typical processing time per sample:
- **Small** (100k reads): 2-5 minutes
- **Medium** (1M reads): 5-15 minutes  
- **Large** (>1M reads): 15-30+ minutes

Depends on thread count, system speed, and read depth.

### Q: Can I run multiple analyses in parallel?
**A:** Yes, you can run multiple BactScout instances:
- Different samples/batches on same machine
- Use different output directories: `-o output_batch1/`, `-o output_batch2/`
- Monitor resource usage (CPU, memory)
- Recommended: 1-2 instances to avoid resource contention

### Q: What's the maximum number of threads I can use?
**A:** Use up to your system's CPU count:
```bash
nproc  # Show available CPUs

pixi run bactscout qc data/ -t $(nproc)  # Use all CPUs
```

More threads = faster but higher memory usage. Balance with available RAM.

### Q: Can I skip quality checks?
**A:** Yes, use `--skip-preflight`:
```bash
pixi run bactscout qc data/ --skip-preflight
```

This skips FASTQ format validation. Use only if you trust your input data.

## Results & Quality Control

### Q: What does "FAIL" in quality_pass mean?
**A:** A sample fails when any metric doesn't meet thresholds:
- Coverage < 30x
- Q30% < 80%
- Read length < 100 bp
- Contamination > 10%

Check which metric failed and see [Quality Control Guide](../guide/quality-control.md).

### Q: Can I adjust quality thresholds?
**A:** Yes, edit `bactscout_config.yml`:
```yaml
coverage_threshold: 20           # Stricter or more lenient
q30_pass_threshold: 0.75         # Lower for relaxed QC
read_length_pass_threshold: 80
contamination_threshold: 15
```

Then run: `pixi run bactscout qc data/ -c my_config.yml`

### Q: What if my samples don't meet thresholds?
**A:** First, understand why:
1. Review the specific failing metric
2. Check fastp HTML report for details
3. Consider if threshold is appropriate for your application

Options:
- Lower thresholds if acceptable for your study
- Re-sequence with higher depth
- Improve sample prep/quality

### Q: Why do some samples have "Unknown" species?
**A:** Reasons:
- Species not in GTDB database
- Poor quality/coverage (can't identify confidently)
- Heavily contaminated sample
- Novel/rare organism

Solutions:
- Check if contamination is high (>5%)
- Try manual BLAST identification
- Add custom reference genomes

### Q: How do I interpret contamination % in mixed samples?
**A:** If you intentionally have mixed samples:
- Contamination % shows other species present
- Use Sylph output to see all detected species
- May need specialized metagenomics tools for detailed analysis

### Q: Can I reprocess samples with different thresholds?
**A:** Sort of:
- Re-running BactScout: It overwrites previous results
- Using `summary` with different config: Changes only `quality_pass` determination
- Better approach: Run once, then filter results in analysis script

## MLST & Strain Typing

### Q: Which species support MLST typing?
**A:** BactScout includes schemes for:
- *Escherichia coli*
- *Salmonella enterica*
- *Klebsiella pneumoniae*
- *Acinetobacter baumannii*
- *Pseudomonas aeruginosa*

To add more, install additional ARIBA databases.

### Q: What does sequence type (ST) mean?
**A:** ST is a unique number assigned based on alleles at 7 housekeeping genes:
- Same ST = likely same source/lineage
- Different ST = different strain
- Novel ST = new combination not in database
- Useful for epidemiological tracking and outbreak investigation

### Q: What if MLST is partial or fails?
**A:** Common causes:
- Low coverage over specific genes
- Sample contamination
- Sequence divergence (novel variants)

Solutions:
- Increase sequencing depth
- Check coverage for housekeeping genes
- Verify sample quality

## Data Management

### Q: How should I organize input data?
**A:** For `qc` command (batch processing):
```
data/
├── sample_001_R1.fastq.gz
├── sample_001_R2.fastq.gz
├── sample_002_R1.fastq.gz
├── sample_002_R2.fastq.gz
└── ...
```

Supported naming:
- `*_R1.fastq.gz`, `*_R2.fastq.gz`
- `*_1.fastq.gz`, `*_2.fastq.gz`
- `*_R1.fq.gz`, `*_R2.fq.gz`

### Q: Can I use compressed (gzip) FASTQ files?
**A:** Yes! BactScout handles both:
- `.fastq.gz` (compressed) - recommended for storage
- `.fastq` (uncompressed) - faster I/O but more space

### Q: How do I manage large result directories?
**A:** Strategies:
- Archive old results: `tar -czf batch_2024-01.tar.gz bactscout_output/`
- Compress HTML reports: `gzip bactscout_output/*/fastp_report.html`
- Keep only CSV summaries, delete per-sample files if needed
- Backup `final_summary.csv` separately

### Q: Can I export results to other formats?
**A:** BactScout outputs CSV (easy to convert):

```python
import pandas as pd

df = pd.read_csv('bactscout_output/final_summary.csv')

# Excel
df.to_excel('results.xlsx', index=False)

# JSON
df.to_json('results.json', orient='records')

# SQL database
# df.to_sql('samples', sqlite3.connect('results.db'))
```

## Configuration

### Q: How do I set permanent defaults?
**A:** Edit `bactscout_config.yml` in project root. These become defaults for all runs.

### Q: Can I have multiple configs?
**A:** Yes, create copies and use with `-c` flag:
```bash
pixi run bactscout qc data/ -c strict_config.yml
pixi run bactscout qc data/ -c lenient_config.yml
```

### Q: How do I add new reference genomes?
**A:** 
1. Format as FASTA files
2. Place in `bactscout_dbs/species_name/`
3. Update Sylph GTDB index
4. Update ARIBA if adding MLST/resistance

See [Configuration Guide](../getting-started/configuration.md#adding-new-species).

## Performance & Optimization

### Q: How can I speed up analysis?
**A:**
1. Increase threads: `-t 8` or `-t $(nproc)`
2. Use SSD storage for I/O speed
3. Pre-filter low-quality reads with fastp
4. Run multiple instances on different samples

### Q: How can I reduce memory usage?
**A:**
1. Decrease threads: `-t 2` uses less memory than `-t 8`
2. Reduce batch size (process fewer samples at once)
3. Enable streaming/chunked processing if available
4. Upgrade to system with more RAM

### Q: Is there a GUI?
**A:** No, BactScout is command-line only. But:
- Results are CSV (easily viewed in Excel, R, Python)
- HTML reports are interactive and visual
- Results can be loaded in analysis tools of your choice

## Troubleshooting

### Q: What's in the log output?
**A:** BactScout outputs:
- Progress indicators (which sample, which step)
- Quality metrics for each sample
- Error/warning messages
- File locations of results

### Q: How do I report a bug?
**A:** 
1. Check [GitHub Issues](https://github.com/nfareed/bactscout/issues)
2. Provide:
   - BactScout version: `pixi run bactscout --version`
   - Command used
   - Error message and full output
   - System info: `uname -a`
   - Sample data (if possible, anonymized)
3. Create new issue with detailed reproduction steps

### Q: Where are results stored?
**A:** By default in `bactscout_output/`:
- Use `-o` to specify different location
- Per-sample results in `Sample_XXX/` directories
- Batch summary in `final_summary.csv`

### Q: Can I resume interrupted analysis?
**A:** Not directly. However:
- Check which samples were already processed
- Delete incomplete samples from output
- Run QC again (it will reprocess everything)
- Consider per-sample `collect` command for better control

## Using Results

### Q: How do I load results in Python?
**A:**
```python
import pandas as pd

df = pd.read_csv('bactscout_output/final_summary.csv')

# Filter, analyze, plot
high_qual = df[df['quality_pass'] == 'PASS']
print(high_qual.describe())
```

See [Results Analysis Guide](../guide/results-analysis.md).

### Q: How do I create visualizations?
**A:** Use fastp HTML reports for quality visuals. For custom plots:

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('bactscout_output/final_summary.csv')

# Box plot of coverage by species
df.boxplot(column='coverage', by='species')
plt.show()

# Scatter: coverage vs Q30%
plt.scatter(df['coverage'], df['q30_percent'])
plt.xlabel('Coverage (x)')
plt.ylabel('Q30%')
plt.show()
```

### Q: Can I integrate with other pipelines?
**A:** Yes:
- BactScout outputs standard CSV
- Results can feed into assembly, SNP calling, AMR detection, etc.
- Python/R scripts can read CSV and prepare data
- See [Results Analysis Guide](../guide/results-analysis.md) for export examples

## Contributing

### Q: How can I contribute?
**A:** See [Contributing Guide](../contributing.md) for details on:
- Reporting issues
- Submitting code changes
- Testing requirements
- Development setup

### Q: Can I add my own analyses?
**A:** BactScout is modular and extensible:
1. Fork the repository
2. Add your analysis in new module
3. Integrate into CLI
4. Submit pull request
5. See [Development Guide](../development/architecture.md)

## Still Have Questions?

- Check [Troubleshooting Guide](../guide/troubleshooting.md) for common issues
- Read [Quality Control Guide](../guide/quality-control.md) for QC interpretation
- Review [Output Format](../usage/output-format.md) for column descriptions
- Check configuration [Examples](../getting-started/configuration.md)
- Search [GitHub Issues](https://github.com/nfareed/bactscout/issues)

If your question isn't answered here, please open an issue on GitHub!
