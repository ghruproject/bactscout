/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { FASTP              } from '../modules/nf-core/fastp/main'
include { SYLPH_PROFILE      } from '../modules/nf-core/sylph/profile/main'
include { SYLPH_DOWNLOAD_DB  } from '../modules/sylph_download/main'
include { ARIBA_RUN          } from '../modules/nf-core/ariba/run/main'
include { ARIBA_GETREF       } from '../modules/nf-core/ariba/getref/main'


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~§~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow GHRUREADQC {

    take:
    ch_reads // channel: paired FASTQ files with metadata

    main:
    
    ch_versions = Channel.empty()
    
    // Print detected reads for debugging
    ch_reads.view { meta, reads ->
        "Processing sample: ${meta.id}, Files: ${reads}"
    }

    //
    // MODULE: FastP - Read trimming and quality filtering
    //
    // Add adapter_fasta to the input tuple and include discard_trimmed_pass parameter
    ch_reads_with_adapter = ch_reads.map { meta, reads -> [meta, reads, []] }
    
    FASTP (
        ch_reads_with_adapter,
        true,  // discard_trimmed_pass - don't output trimmed reads
        false, // save_trimmed_fail
        false  // save_merged
    )
    ch_versions = ch_versions.mix(FASTP.out.versions)

    //
    // MODULE: Sylph taxonomic profiling (optional - only if database is available)
    //
    
    // Check if Sylph database exists or needs to be downloaded
    ch_sylph_db = Channel.empty()
    ch_profiles = Channel.empty()
    
    if (params.sylph_db) {
        // Check if database file/directory exists
        def db_file = file(params.sylph_db)
        
        if (db_file.exists()) {
            if (db_file.isFile() && db_file.name.endsWith('.syldb')) {
                // Direct database file
                ch_sylph_db = Channel.fromPath(params.sylph_db)
                log.info "Using existing Sylph database: ${params.sylph_db}"
            } else if (db_file.isDirectory()) {
                // Look for .syldb files in directory
                def syldb_files = file("${params.sylph_db}/*.syldb")
                if (syldb_files) {
                    ch_sylph_db = Channel.fromPath("${params.sylph_db}/*.syldb").first()
                    log.info "Found Sylph database in directory: ${params.sylph_db}"
                } else {
                    log.info "No Sylph database found in ${params.sylph_db}, downloading..."
                    SYLPH_DOWNLOAD_DB()
                    ch_sylph_db = SYLPH_DOWNLOAD_DB.out.database
                    ch_versions = ch_versions.mix(SYLPH_DOWNLOAD_DB.out.versions)
                }
            } else {
                log.warn "Sylph database path exists but is not a .syldb file or directory: ${params.sylph_db}"
            }
        } else {
            log.info "Sylph database path does not exist, downloading to: ${params.sylph_db}"
            SYLPH_DOWNLOAD_DB()
            ch_sylph_db = SYLPH_DOWNLOAD_DB.out.database
            ch_versions = ch_versions.mix(SYLPH_DOWNLOAD_DB.out.versions)
        }
        
        // Run Sylph profiling if database is available
        SYLPH_PROFILE (
            ch_reads,
            ch_sylph_db
        )
        ch_versions = ch_versions.mix(SYLPH_PROFILE.out.versions)
        ch_profiles = SYLPH_PROFILE.out.profile_out
    } else {
        log.info "No Sylph database specified (--sylph_db), skipping taxonomic profiling"
    }

    //
    // MODULE: ARIBA antimicrobial resistance profiling (optional)
    //
    
    ch_ariba_db = Channel.empty()
    ch_amr_results = Channel.empty()
    
    if (params.ariba_db) {
        // Check if ARIBA database exists or needs to be downloaded
        def ariba_db_file = file(params.ariba_db)
        
        if (ariba_db_file.exists() && ariba_db_file.name.endsWith('.tar.gz')) {
            // Direct database file
            ch_ariba_db = Channel.fromPath(params.ariba_db)
                .map { db -> [ [id: db.baseName.replace('.tar', '')], db ] }
            log.info "Using existing ARIBA database: ${params.ariba_db}"
        } else if (params.ariba_db in ['card', 'argannot', 'resfinder', 'plasmidfinder', 'ncbi', 'srst2_argannot']) {
            // Download database using ariba getref
            log.info "Downloading ARIBA database: ${params.ariba_db}"
            ch_db_meta = Channel.of([ [id: params.ariba_db], params.ariba_db ])
            
            ARIBA_GETREF(ch_db_meta)
            ch_ariba_db = ARIBA_GETREF.out.db
            ch_versions = ch_versions.mix(ARIBA_GETREF.out.versions)
        } else {
            log.warn "Invalid ARIBA database specified: ${params.ariba_db}. Skipping AMR profiling."
            log.warn "Valid options: card, argannot, resfinder, plasmidfinder, ncbi, srst2_argannot, or path to .tar.gz file"
        }
        
        // Run ARIBA if database is available
        if (!ch_ariba_db.isEmpty()) {
            ARIBA_RUN (
                ch_reads,
                ch_ariba_db
            )
            ch_versions = ch_versions.mix(ARIBA_RUN.out.versions)
            ch_amr_results = ARIBA_RUN.out.results
        }
    } else {
        log.info "No ARIBA database specified (--ariba_db), skipping antimicrobial resistance profiling"
    }


    emit:
    fastp_json    = FASTP.out.json    // channel: [ val(meta), path(json) ]
    fastp_html    = FASTP.out.html    // channel: [ val(meta), path(html) ]
    profiles      = ch_profiles       // channel: [ val(meta), path(tsv) ]
    amr_results   = ch_amr_results    // channel: [ val(meta), path(results) ]
    versions      = ch_versions       // channel: path(versions.yml)

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
