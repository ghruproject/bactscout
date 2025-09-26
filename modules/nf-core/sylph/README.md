# Sylph nf-core Modules

This directory contains the official nf-core modules for [Sylph](https://github.com/bluenote-1577/sylph), a fast k-mer based metagenomic profiler.

## Available Modules

### SYLPH_PROFILE
- **Location**: `modules/nf-core/sylph/profile/`
- **Purpose**: Performs taxonomic profiling of metagenomic samples using k-mer matching
- **Input**: FASTQ files and a Sylph database (.syldb)
- **Output**: TSV file with taxonomic profile results

### SYLPH_SKETCH  
- **Location**: `modules/nf-core/sylph/sketch/`
- **Purpose**: Creates k-mer sketches from genomic sequences
- **Input**: FASTQ files and reference genomes
- **Output**: Sketch files (.sylsp) and database files (.syldb)

## Usage in Workflow

The Sylph modules are integrated into the GHRU-readqc workflow as follows:

```nextflow
include { SYLPH_PROFILE } from '../modules/nf-core/sylph/profile/main'

// In workflow
SYLPH_PROFILE(
    ch_reads,           // Channel with [meta, reads]
    ch_sylph_database   // Path to Sylph database
)
```

## Database Management

The workflow includes automatic database management:
- Downloads the GTDB r226 database if not provided
- Supports custom database paths via `--sylph_db` parameter
- Automatically detects existing databases in specified directories

## Configuration

Module-specific configurations can be set in `conf/modules.config`:

```nextflow
withName: SYLPH_PROFILE {
    ext.args = '--additional-args'
    publishDir = [
        path: { "${params.outdir}/sylph" },
        mode: params.publish_dir_mode,
        saveAs: { filename -> filename.equals('versions.yml') ? null : filename }
    ]
}
```

## Output Files

- **`*.tsv`**: Taxonomic profiling results with abundance estimates
- **`versions.yml`**: Software version information

## Container Information

- **Conda**: `sylph=0.7.0`
- **Container**: `biocontainers/sylph:0.7.0--h919a2d8_0`

## References

- Sylph GitHub: https://github.com/bluenote-1577/sylph
- Publication: [Coming soon]