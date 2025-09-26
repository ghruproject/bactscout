# cgps-discovery/ghrureadqc

[![GitHub Actions CI Status](https://github.com/cgps-discovery/ghrureadqc/actions/workflows/nf-test.yml/badge.svg)](https://github.com/cgps-discovery/ghrureadqc/actions/workflows/nf-test.yml)
[![GitHub Actions Linting Status](https://github.com/cgps-discovery/ghrureadqc/actions/workflows/linting.yml/badge.svg)](https://github.com/cgps-discovery/ghrureadqc/actions/workflows/linting.yml)[![Cite with Zenodo](http://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-1073c8?labelColor=000000)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![nf-test](https://img.shields.io/badge/unit_tests-nf--test-337ab7.svg)](https://www.nf-test.com)

[![Nextflow](https://img.shields.io/badge/version-%E2%89%A524.10.5-green?style=flat&logo=nextflow&logoColor=white&color=%230DC09D&link=https%3A%2F%2Fnextflow.io)](https://www.nextflow.io/)
[![nf-core template version](https://img.shields.io/badge/nf--core_template-3.3.2-green?style=flat&logo=nfcore&logoColor=white&color=%2324B064&link=https%3A%2F%2Fnf-co.re)](https://github.com/nf-core/tools/releases/tag/3.3.2)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/cgps-discovery/ghrureadqc)

## Introduction

**cgps-discovery/ghrureadqc** is a bioinformatics pipeline for rapid read quality assessment, taxonomic profiling, and antimicrobial resistance gene detection. The pipeline takes paired-end FASTQ files from a directory and performs optional taxonomic profiling using Sylph and AMR profiling using ARIBA when databases are provided.

The pipeline performs the following steps:

1. **Input Detection**: Automatically detects and pairs FASTQ files from an input directory
2. **Read Trimming**: Uses FastP for quality trimming and adapter removal
3. **Taxonomic Profiling** (optional): Uses Sylph for ultra-fast metagenomic profiling when `--sylph_db` is provided
4. **AMR Profiling** (optional): Uses ARIBA for antimicrobial resistance gene detection when `--ariba_db` is provided
5. **Database Management**: Automatically downloads databases if not found locally

## Usage

> [!NOTE]
> If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how to set-up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline) with `-profile test` before running the workflow on actual data.

Simply provide a directory path containing your paired-end FASTQ files. The pipeline will automatically detect and pair files based on common naming patterns:

- `*_R1.fastq.gz` / `*_R2.fastq.gz`
- `*_R1_*.fastq.gz` / `*_R2_*.fastq.gz`  
- `*_1.fastq.gz` / `*_2.fastq.gz`

Example directory structure:
```
reads/
├── Sample_A_R1.fastq.gz
├── Sample_A_R2.fastq.gz
├── Sample_B_R1.fastq.gz
└── Sample_B_R2.fastq.gz
```

Now, you can run the pipeline using:

<!-- TODO nf-core: update the following command to include all required parameters for a minimal example -->

```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile <docker/singularity/.../institute> \
   --input /path/to/fastq/directory \
   --outdir <OUTDIR>
```

> [!WARNING]
> Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_; see [docs](https://nf-co.re/docs/usage/getting_started/configuration#custom-configuration-files).

## Sylph Database Management

The pipeline includes automatic Sylph database management:

### Basic Usage (Read Trimming Only)
```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile docker \
   --input /path/to/fastq/directory \
   --outdir results
```

### With Taxonomic Profiling
To enable taxonomic profiling, provide the `--sylph_db` parameter:

```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile docker \
   --input /path/to/fastq/directory \
   --sylph_db /path/to/sylph/database \
   --outdir results
```

### Automatic Database Download
The pipeline automatically handles Sylph database management:

1. **Existing Database**: If you specify a path that contains a `.syldb` file, it will be used directly
2. **Database Directory**: If you specify a directory path, the pipeline will look for `.syldb` files in that directory
3. **Automatic Download**: If no database is found at the specified path, the pipeline will automatically download the GTDB-r226-c200-dbv1.syldb database from:
   ```
   http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r226-c200-dbv1.syldb
   ```

### Default Behavior
- By default, `--sylph_db` points to `sylph_db/` in your working directory
- If this directory doesn't exist or is empty, the database will be downloaded automatically
- Downloaded databases are saved to your output directory for reuse

### Examples

**Using existing database file:**
```bash
--sylph_db /data/databases/gtdb-r226-c200-dbv1.syldb
```

**Using database directory:**
```bash
--sylph_db /data/databases/sylph/
```

**Automatic download to default location:**
```bash
# No --sylph_db parameter needed - will download to sylph_db/ if not found
```

**Skip taxonomic profiling:**
```bash
--sylph_db null
```

## ARIBA Antimicrobial Resistance Profiling

The pipeline includes optional antimicrobial resistance (AMR) gene detection using ARIBA:

### Basic Usage (Without AMR Profiling) 
```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile docker \
   --input /path/to/fastq/directory \
   --outdir results
```

### With AMR Profiling
To enable AMR profiling, provide the `--ariba_db` parameter:

```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile docker \
   --input /path/to/fastq/directory \
   --ariba_db card \
   --outdir results
```

### Available ARIBA Databases

The pipeline supports automatic download of several predefined databases:

- **`card`**: Comprehensive Antibiotic Resistance Database (CARD)
- **`resfinder`**: ResFinder database for acquired antimicrobial resistance genes
- **`argannot`**: ARG-ANNOT database for antibiotic resistance genes
- **`plasmidfinder`**: PlasmidFinder database for plasmid identification
- **`ncbi`**: NCBI AMRFinderPlus database
- **`srst2_argannot`**: SRST2-formatted ARG-ANNOT database

### Custom ARIBA Database
You can also provide a path to a custom ARIBA database file:

```bash
--ariba_db /path/to/custom_ariba_database.tar.gz
```

### Examples

**Using CARD database (recommended for comprehensive AMR profiling):**
```bash
--ariba_db card
```

**Using ResFinder database:**
```bash
--ariba_db resfinder
```

**Combined Taxonomic and AMR Profiling:**
```bash
nextflow run cgps-discovery/ghrureadqc \
   -profile docker \
   --input /path/to/fastq/directory \
   --sylph_db /path/to/sylph/database \
   --ariba_db card \
   --outdir results
```

**Skip AMR profiling:**
```bash
# Simply omit the --ariba_db parameter (default behavior)
```

## Module Architecture

This pipeline follows nf-core module standards with the following structure:

### nf-core Official Modules
- **FASTP**: `modules/nf-core/fastp/` - Read trimming and quality control
- **SYLPH_PROFILE**: `modules/nf-core/sylph/profile/` - Fast k-mer based taxonomic profiling  
- **SYLPH_SKETCH**: `modules/nf-core/sylph/sketch/` - K-mer sketching for genomic sequences
- **ARIBA_RUN**: `modules/nf-core/ariba/run/` - Antimicrobial resistance gene detection
- **ARIBA_GETREF**: `modules/nf-core/ariba/getref/` - ARIBA database preparation

### Custom Modules
- **SYLPH_DOWNLOAD_DB**: `modules/sylph_download/` - Automated Sylph database management

All modules include:
- Standard nf-core module structure with `main.nf`, `meta.yml`, and `environment.yml`
- Containerized execution using Conda and Docker/Singularity
- Comprehensive version tracking and metadata management
- Standardized input/output channel structures

### Module Updates

To update to the latest nf-core modules:

```bash
# Install nf-core tools
pip install nf-core

# Update specific modules (example)
nf-core modules update fastp
nf-core modules update sylph/profile
```

## Credits

cgps-discovery/ghrureadqc was originally written by Nabil-Fareed Alikhan.

We thank the following people for their extensive assistance in the development of this pipeline:

<!-- TODO nf-core: If applicable, make list of people who have also contributed -->

## Contributions and Support

If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

## Citations

<!-- TODO nf-core: Add citation for pipeline after first release. Uncomment lines below and update Zenodo doi and badge at the top of this file. -->
<!-- If you use cgps-discovery/ghrureadqc for your analysis, please cite it using the following doi: [10.5281/zenodo.XXXXXX](https://doi.org/10.5281/zenodo.XXXXXX) -->

<!-- TODO nf-core: Add bibliography of tools and data used in your pipeline -->

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [MIT license](https://github.com/nf-core/tools/blob/main/LICENSE).

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
