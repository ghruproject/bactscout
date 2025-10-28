#!/usr/bin/env nextflow

/*
 * BactScout Nextflow Workflow
 * 
 * A complete workflow for processing paired-end genomic samples through
 * BactScout (collection & analysis) on HPC or local systems.
 * 
 * Features:
 *  - Automatically discovers paired-end FASTQ files (_R1/_R2 or _1/_2 naming)
 *  - Processes each sample independently (parallelizable)
 *  - Aggregates results into a single summary CSV
 * 
 * Usage:
 *  nextflow run nextflow.nf --input_dir /path/to/reads --output_dir /path/to/output
 */

nextflow.enable.dsl = 2

// ============================================================================
// Parameters
// ============================================================================

params.input_dir = null
params.output_dir = "${launchDir}/bactscout_output"
params.config = "${launchDir}/bactscout_config.yml"
params.threads = 4
params.kat_enabled = null  // null = use config default
params.k_mer_size = null   // null = use config default
params.skip_preflight = false
params.help = false

// ============================================================================
// Help Message
// ============================================================================

if (params.help || params.input_dir == null) {
    log.info"""
    ╔════════════════════════════════════════════════════════════════════════════╗
    ║                 BactScout Nextflow Workflow (HPC-Ready)                     ║
    ║                                                                            ║
    ║  A scalable workflow for bacterial genomic analysis with paired-end reads  ║
    ╚════════════════════════════════════════════════════════════════════════════╝

    USAGE:
      nextflow run nextflow.nf --input_dir <reads_directory> [OPTIONS]

    REQUIRED:
      --input_dir DIR         Directory containing paired-end FASTQ files
                              (files must be named with _R1/_R2 or _1/_2 suffix)

    OPTIONS:
      --output_dir DIR        Output directory for results
                              (default: ./bactscout_output)
      
      --config FILE           Path to BactScout config file
                              (default: ./bactscout_config.yml)
      
      --threads N             Number of threads per sample
                              (default: 4)
      
      --kat_enabled true|false
                              Enable/disable KAT analysis (overrides config)
                              (default: use config setting)
      
      --k_mer_size N          K-mer size for KAT analysis
                              (default: use config setting)
      
      --skip_preflight        Skip preflight checks (not recommended)
                              (default: false)
      
      --help                  Show this help message

    EXAMPLE:
      nextflow run nextflow.nf \\
        --input_dir ./samples \\
        --output_dir ./results \\
        --threads 8 \\
        --kat_enabled true

    WORKFLOW STEPS:
      1. Discover paired-end FASTQ files in input directory
      2. Run BactScout collect on each sample (parallelizable)
      3. Aggregate results into final_summary.csv
    
    REQUIREMENTS:
      - BactScout installed and available in PATH
      - Python 3.9+
      - Paired-end FASTQ files properly named
    """.stripIndent()
    exit 0
}

// ============================================================================
// Process: Run BactScout Collect on Each Sample
// ============================================================================

process collect_sample {
    tag { sample_name }
    
    publishDir "${params.output_dir}/${sample_name}", mode: 'copy'
    
    input:
    tuple val(sample_name), path(read1), path(read2)
    
    output:
    path("${sample_name}_summary.csv"), emit: summary
    path("${sample_name}_qc_report.html"), optional: true, emit: report
    path("**"), emit: all_outputs
    
    script:
    // Build optional parameters
    def kat_param = params.kat_enabled != null ? "--kat ${params.kat_enabled}" : ""
    def k_param = params.k_mer_size != null ? "--k_mer_size ${params.k_mer_size}" : ""
    def skip_param = params.skip_preflight ? "--skip_preflight" : ""
    
    """
    echo "Processing sample: ${sample_name}"
    echo "R1: ${read1}"
    echo "R2: ${read2}"
    
    bactscout collect \\
        ${read1} \\
        ${read2} \\
        --output_dir . \\
        --threads ${params.threads} \\
        --config ${params.config} \\
        ${kat_param} \\
        ${k_param} \\
        ${skip_param}
    
    echo "Sample ${sample_name} processing complete"
    """
}

// ============================================================================
// Process: Generate Final Summary
// ============================================================================

process final_summary {
    publishDir "${params.output_dir}", mode: 'copy'
    
    input:
    path(summaries)
    
    output:
    path("final_summary.csv")
    
    script:
    """
    bactscout summary \\
        --input_dir ${params.output_dir} \\
        --output_file final_summary.csv
    """
}

// ============================================================================
// Workflow
// ============================================================================

workflow {
    
    // ========================================================================
    // Input Validation
    // ========================================================================
    
    if (!params.input_dir) {
        error "ERROR: --input_dir parameter is required"
    }

    input_dir = file(params.input_dir)
    if (!input_dir.exists()) {
        error "ERROR: Input directory does not exist: ${params.input_dir}"
    }

    config_file = file(params.config)
    if (!config_file.exists()) {
        error "ERROR: Config file not found: ${params.config}"
    }
    
    // ========================================================================
    // Find Paired-End Reads
    // ========================================================================
    
    // Strategy: Look for pairs matching _R1/_R2 or _1/_2 patterns
    // Create a channel with [sample_name, read1_file, read2_file]

    read_pairs = channel
        .fromPath("${params.input_dir}/*_R1.fastq.gz", checkIfExists: false)
        .map { file -> 
            def name = file.name.replaceAll(/_R1\.fastq\.gz$/, '')
            def r2_file = file.parent / file.name.replaceAll(/_R1\.fastq\.gz$/, '_R2.fastq.gz')
            [ name, file, r2_file ]
        }
        .mix(
            channel
                .fromPath("${params.input_dir}/*_1.fastq.gz", checkIfExists: false)
                .map { file ->
                    def name = file.name.replaceAll(/_1\.fastq\.gz$/, '')
                    def r2_file = file.parent / file.name.replaceAll(/_1\.fastq\.gz$/, '_2.fastq.gz')
                    [ name, file, r2_file ]
                }
        )
        .unique()
    
    read_pairs.subscribe { sample ->
        log.info "Found sample: ${sample[0]} (R1: ${sample[1].name}, R2: ${sample[2].name})"
    }
    
    // ========================================================================
    // Run BactScout Pipeline
    // ========================================================================
    
    log.info "╔════════════════════════════════════════════════════════════════╗"
    log.info "║           BactScout Nextflow Workflow Starting                  ║"
    log.info "╚════════════════════════════════════════════════════════════════╝"
    
    log.info "Input directory:  ${params.input_dir}"
    log.info "Output directory: ${params.output_dir}"
    log.info "Config file:      ${params.config}"
    log.info "Threads per sample: ${params.threads}"
    
    if (params.kat_enabled != null) {
        log.info "KAT enabled: ${params.kat_enabled}"
    }
    if (params.k_mer_size != null) {
        log.info "K-mer size: ${params.k_mer_size}"
    }
    
    // Run collect_sample for all pairs
    collect_results = collect_sample(read_pairs)
    
    // Generate final summary
    final_summary(collect_results.summary.collect())
    
    log.info "╔════════════════════════════════════════════════════════════════╗"
    log.info "║              BactScout Nextflow Workflow Complete              ║"
    log.info "║   Results available in: ${params.output_dir}/final_summary.csv ║"
    log.info "╚════════════════════════════════════════════════════════════════╝"
}
