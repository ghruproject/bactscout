#!/usr/bin/env nextflow
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    ghruproject/GHRU-readqc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Github : https://github.com/ghruproject/GHRU-readqc
----------------------------------------------------------------------------------------
*/

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS / WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GHRUREADQC  } from './workflows/ghrureadqc'
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    NAMED WORKFLOWS FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

//
// WORKFLOW: Run main analysis pipeline depending on type of input
//
workflow CGPSDISCOVERY_GHRUREADQC {

    take:
    reads_dir // channel: path to directory containing FASTQ files

    main:

    // Create channel from FASTQ files in the input directory
    // Try multiple naming patterns for paired-end reads
    ch_reads = Channel
        .fromFilePairs("${reads_dir}/*_R{1,2}.fastq.gz")
        .mix(Channel.fromFilePairs("${reads_dir}/*_R{1,2}.fq.gz"))
        .mix(Channel.fromFilePairs("${reads_dir}/*_{R1,R2}.fastq.gz"))
        .mix(Channel.fromFilePairs("${reads_dir}/*_{R1,R2}.fq.gz"))
        .mix(Channel.fromFilePairs("${reads_dir}/*_{1,2}.fastq.gz"))
        .mix(Channel.fromFilePairs("${reads_dir}/*_{1,2}.fq.gz"))
        .ifEmpty { error "No FASTQ file pairs found in ${reads_dir}. Please check the directory path and file naming patterns (supported: *_R1/*_R2, *_R1_*/*_R2_*, *_1/*_2)." }
        .unique()
        .map { sample_id, reads ->
            def meta = [:]
            meta.id = sample_id
            meta.single_end = reads.size() == 1
            [ meta, reads ]
        }
    //
    // WORKFLOW: Run pipeline
    //
    GHRUREADQC (
        ch_reads
    )

    emit:
    fastp_json    = GHRUREADQC.out.fastp_json
    fastp_html    = GHRUREADQC.out.fastp_html
    profiles      = GHRUREADQC.out.profiles
    amr_results   = GHRUREADQC.out.amr_results
    versions      = GHRUREADQC.out.versions
}
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow {

    main:

    //
    // WORKFLOW: Run main workflow
    //
    CGPSDISCOVERY_GHRUREADQC (
        params.input
    )
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
