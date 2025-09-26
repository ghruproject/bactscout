# GHRU ReadQC Pipeline - Usage Examples

This document provides detailed usage examples for the GHRU ReadQC pipeline.

## Quick Start Example

```bash
# 1. Clone the repository
git clone https://github.com/cgps-discovery/GHRU-readqc.git
cd GHRU-readqc

# 2. Create conda environment
conda env create -f environment.yml
conda activate ghru-readqc

# 3. Install Nextflow
curl -s https://get.nextflow.io | bash
sudo mv nextflow /usr/local/bin/

# 4. Generate test data (optional)
python test/generate_test_data.py --num_samples 3 --num_reads 50000

# 5. Run the pipeline
./run_pipeline.sh -i test/data -o results
```

## Detailed Usage Examples

### Example 1: Basic Run with Default Settings

```bash
nextflow run main.nf --input /path/to/fastq/files --outdir results -profile conda
```

### Example 2: Run with Docker

```bash
nextflow run main.nf --input /path/to/fastq/files --outdir results -profile docker
```

### Example 3: Resume a Failed Run

```bash
nextflow run main.nf --input /path/to/fastq/files --outdir results -profile conda -resume
```

### Example 4: Run with Custom Resource Limits

```bash
nextflow run main.nf \
    --input /path/to/fastq/files \
    --outdir results \
    --max_memory 64.GB \
    --max_cpus 8 \
    --max_time 120.h \
    -profile conda
```

### Example 5: Using the Runner Script

```bash
# Basic usage
./run_pipeline.sh -i /path/to/fastq/files -o results

# With specific profile
./run_pipeline.sh -i /path/to/fastq/files -o results -p docker

# Resume previous run
./run_pipeline.sh -i /path/to/fastq/files -o results -r
```

## Input File Naming Conventions

The pipeline automatically detects paired-end FASTQ files using these patterns:

### Supported Patterns:
- `sample_R1.fastq.gz` / `sample_R2.fastq.gz`
- `sample_1.fastq.gz` / `sample_2.fastq.gz`
- `sample_R1.fq.gz` / `sample_R2.fq.gz`
- `sample_1.fq.gz` / `sample_2.fq.gz`

### Example Directory Structure:
```
input_directory/
├── E001_R1.fastq.gz
├── E001_R2.fastq.gz
├── E002_R1.fastq.gz
├── E002_R2.fastq.gz
├── sample_001_1.fq.gz
├── sample_001_2.fq.gz
└── bacterial_isolate_R1.fastq.gz
└── bacterial_isolate_R2.fastq.gz
```

## Understanding the Output

### Key Output Files:

1. **MultiQC Report** (`multiqc/multiqc_report.html`)
   - Comprehensive quality control summary
   - Interactive plots and tables
   - Sample comparison views

2. **Trimmed Reads** (`fastp/`)
   - High-quality trimmed FASTQ files
   - Quality control reports

3. **Species Identification** (`sylph/`)
   - Species identification results
   - Genome size estimates

4. **Selected Genome** (`genome_selection/`)
   - Automatically selected smallest genome
   - Species information and confidence metrics

5. **MLST Results** (`ariba_mlst/`)
   - Multi-locus sequence typing
   - Strain characterization

6. **Read Depth Analysis** (`read_depth/`)
   - Coverage estimates
   - Sequencing depth calculations

### Interpreting Read Depth Results:

The pipeline provides coverage interpretation:
- **≥50x**: High coverage - excellent for most analyses
- **20-50x**: Good coverage - suitable for most analyses  
- **10-20x**: Moderate coverage - may be sufficient for basic analyses
- **5-10x**: Low coverage - limited analysis capabilities
- **<5x**: Very low coverage - may not be suitable for analysis

## Troubleshooting Common Issues

### Issue 1: No FASTQ Files Detected
```bash
Error: No FASTQ files found in input directory
```
**Solution**: Check file naming conventions and ensure files are in the specified directory.

### Issue 2: Memory Errors
```bash
Process xxx terminated with an error exit status (137)
```
**Solution**: Increase memory allocation:
```bash
nextflow run main.nf --input data --outdir results --max_memory 128.GB -profile conda
```

### Issue 3: Conda Environment Issues
```bash
Could not find conda environment
```
**Solution**: Ensure conda is installed and environment is created:
```bash
conda env create -f environment.yml
conda activate ghru-readqc
```

### Issue 4: Database Download Failures
```bash
Error downloading sylph database
```
**Solution**: Check internet connection and available disk space. The GTDB database is ~2GB.

## Performance Optimization

### For Large Datasets:
```bash
nextflow run main.nf \
    --input /path/to/fastq/files \
    --outdir results \
    --max_memory 256.GB \
    --max_cpus 32 \
    --max_time 48.h \
    -profile conda \
    -with-trace \
    -with-timeline \
    -with-report
```

### For Small Test Datasets:
```bash
nextflow run main.nf \
    --input test/data \
    --outdir test_results \
    --max_memory 8.GB \
    --max_cpus 2 \
    -profile conda
```

## Advanced Configuration

### Custom MultiQC Configuration:
Edit `conf/multiqc_config.yml` to customize the report appearance and content.

### Custom Resource Requirements:
Edit `nextflow.config` to adjust process-specific resource requirements.

### Using Different Executors:
The pipeline supports various executors (local, SLURM, PBS, SGE, etc.). Configure in `nextflow.config`.

## Integration with HPC Systems

### SLURM Example:
```bash
nextflow run main.nf \
    --input /path/to/fastq/files \
    --outdir results \
    -profile conda \
    -process.executor slurm \
    -process.queue normal \
    -process.clusterOptions '--account=your_account'
```

### PBS Example:
```bash
nextflow run main.nf \
    --input /path/to/fastq/files \
    --outdir results \
    -profile conda \
    -process.executor pbs \
    -process.queue workq
```

## Best Practices

1. **Always use absolute paths** for input and output directories
2. **Test with small datasets** before running large batches
3. **Monitor resource usage** with `-with-trace` and `-with-timeline`
4. **Use `-resume`** to restart failed runs efficiently
5. **Check log files** in the `work/` directory for debugging
6. **Backup important results** before rerunning pipelines