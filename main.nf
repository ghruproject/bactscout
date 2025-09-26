#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * GHRU ReadQC Pipeline
 * A Nextflow pipeline for quality control of paired-end FASTQ files
 */

def helpMessage() {
    log.info"""
    Usage:
    nextflow run main.nf --input <input_dir> --outdir <output_dir>

    Required arguments:
    --input         Directory containing paired FASTQ files (*.fastq.gz or *.fq.gz)
    --outdir        Output directory for results

    Optional arguments:
    --help          Show this help message
    """.stripIndent()
}

// Show help message
if (params.help) {
    helpMessage()
    exit 0
}

// Check required parameters
if (!params.input) {
    log.error "Error: --input parameter is required"
    exit 1
}

if (!params.outdir) {
    log.error "Error: --outdir parameter is required"
    exit 1
}

/*
 * PROCESS DEFINITIONS
 */

process FASTP {
    tag "$meta.id"
    publishDir "${params.outdir}/fastp", mode: 'copy'
    
    conda 'bioconda::fastp=0.23.4'
    
    input:
    tuple val(meta), path(reads)
    
    output:
    tuple val(meta), path("*_trimmed_R{1,2}.fastq.gz"), emit: reads
    path("*.json"), emit: json
    path("*.html"), emit: html
    
    script:
    def prefix = meta.id
    """
    fastp \\
        --in1 ${reads[0]} \\
        --in2 ${reads[1]} \\
        --out1 ${prefix}_trimmed_R1.fastq.gz \\
        --out2 ${prefix}_trimmed_R2.fastq.gz \\
        --json ${prefix}_fastp.json \\
        --html ${prefix}_fastp.html \\
        --thread ${task.cpus} \\
        --detect_adapter_for_pe \\
        --cut_front \\
        --cut_tail \\
        --cut_window_size 4 \\
        --cut_mean_quality 15 \\
        --qualified_quality_phred 15 \\
        --unqualified_percent_limit 40 \\
        --length_required 36
    """
}

process SYLPH {
    tag "$meta.id"
    publishDir "${params.outdir}/sylph", mode: 'copy'
    
    conda 'bioconda::sylph=0.6.1'
    
    input:
    tuple val(meta), path(reads)
    
    output:
    tuple val(meta), path("*.tsv"), emit: profile
    
    script:
    def prefix = meta.id
    """
    # Download and prepare sylph database if not available
    if [ ! -f "gtdb-r214-c200-s85.syldb" ]; then
        sylph download gtdb-r214
    fi
    
    sylph profile \\
        -t ${task.cpus} \\
        -d gtdb-r214-c200-s85.syldb \\
        ${reads[0]} ${reads[1]} \\
        -o ${prefix}_sylph_profile.tsv
    """
}

process PICK_SMALLEST_GENOME {
    tag "$meta.id"
    publishDir "${params.outdir}/genome_selection", mode: 'copy'
    
    conda 'conda-forge::python=3.11'
    
    input:
    tuple val(meta), path(sylph_profile)
    
    output:
    tuple val(meta), path("*_selected_genome.txt"), emit: selected_genome
    
    script:
    def prefix = meta.id
    """
    python ${projectDir}/bin/pick_smallest_genome.py \\
        --input ${sylph_profile} \\
        --output ${prefix}_selected_genome.txt
    """
}

process ARIBA_MLST {
    tag "$meta.id"
    publishDir "${params.outdir}/ariba_mlst", mode: 'copy'
    
    conda 'bioconda::ariba=2.14.6'
    
    input:
    tuple val(meta), path(reads)
    
    output:
    tuple val(meta), path("${meta.id}_mlst/*"), emit: results
    
    script:
    def prefix = meta.id
    """
    # Get MLST database (using a generic one - can be customized)
    if [ ! -d "mlst_db" ]; then
        ariba getref mlst_db --species "Escherichia coli"
        ariba prepareref -f mlst_db.fa -m mlst_db.tsv mlst_db_prepared
    fi
    
    ariba run \\
        mlst_db_prepared \\
        ${reads[0]} ${reads[1]} \\
        ${prefix}_mlst \\
        --threads ${task.cpus}
    """
}

process CALCULATE_DEPTH {
    tag "$meta.id"
    publishDir "${params.outdir}/read_depth", mode: 'copy'
    
    conda 'conda-forge::python=3.11'
    
    input:
    tuple val(meta), path(reads), path(selected_genome)
    
    output:
    tuple val(meta), path("*_read_depth.txt"), emit: depth
    
    script:
    def prefix = meta.id
    """
    python ${projectDir}/bin/calculate_depth.py \\
        --reads ${reads[0]} ${reads[1]} \\
        --genome_info ${selected_genome} \\
        --output ${prefix}_read_depth.txt
    """
}

process MULTIQC {
    publishDir "${params.outdir}/multiqc", mode: 'copy'
    
    conda 'bioconda::multiqc=1.19'
    
    input:
    path('*')
    
    output:
    path("multiqc_report.html"), emit: report
    path("multiqc_data"), emit: data
    
    script:
    """
    # Copy MultiQC config if it exists
    if [ -f "${projectDir}/conf/multiqc_config.yml" ]; then
        cp "${projectDir}/conf/multiqc_config.yml" ./multiqc_config.yml
        CONFIG_ARG="--config multiqc_config.yml"
    else
        CONFIG_ARG=""
    fi
    
    multiqc . \\
        --title "GHRU ReadQC Report" \\
        --filename multiqc_report.html \\
        --force \\
        \$CONFIG_ARG
    """
}

/*
 * WORKFLOW DEFINITION
 */

workflow {
    // Create channel for input FASTQ files
    input_ch = Channel
        .fromFilePairs("${params.input}/*{_R1,_R2,_1,_2}{.fastq,.fq}{.gz,}", size: 2)
        .map { name, files -> 
            def meta = [id: name.replaceAll(/(_R[12]|_[12]).*/, '')]
            [meta, files]
        }
    
    // Step 1: Quality trimming and filtering with fastp
    FASTP(input_ch)
    
    // Step 2: Species identification and genome size estimation with sylph
    SYLPH(FASTP.out.reads)
    
    // Step 3: Pick smallest genome size
    PICK_SMALLEST_GENOME(SYLPH.out.profile)
    
    // Step 4: MLST typing with ARIBA
    ARIBA_MLST(FASTP.out.reads)
    
    // Step 5: Calculate read depth
    depth_input = FASTP.out.reads
        .join(PICK_SMALLEST_GENOME.out.selected_genome)
    CALCULATE_DEPTH(depth_input)
    
    // Step 6: Generate MultiQC report
    multiqc_input = FASTP.out.json
        .mix(FASTP.out.html)
        .collect()
    
    MULTIQC(multiqc_input)
}