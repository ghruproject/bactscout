process SYLPH_DOWNLOAD_DB {
    label 'process_low'
    label 'sylph_container'

    publishDir "${params.outdir}/sylph_db", mode: 'copy', pattern: "*.syldb"

    output:
    path "*.syldb", emit: database
    path "versions.yml", emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def db_url = "http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r226-c200-dbv1.syldb"
    def db_name = "gtdb-r226-c200-dbv1.syldb"
    """
    echo "Downloading Sylph database from ${db_url}..."
    wget -O ${db_name} ${db_url}
    
    # Verify the file was downloaded and is not empty
    if [ ! -s ${db_name} ]; then
        echo "Error: Database download failed or file is empty"
        exit 1
    fi
    
    echo "Database downloaded successfully: ${db_name}"
    ls -lh ${db_name}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        wget: \$(wget --version 2>&1 | head -n1 | sed 's/GNU Wget //')
    END_VERSIONS
    """

    stub:
    def db_name = "gtdb-r226-c200-dbv1.syldb"
    """
    touch ${db_name}
    echo "Stub: Would download Sylph database"

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        wget: \$(wget --version 2>&1 | head -n1 | sed 's/GNU Wget //')
    END_VERSIONS
    """
}