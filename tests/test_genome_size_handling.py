from bactscout.thread import blank_sample_results, handle_genome_size


def write_metrics_file(
    tmp_path, species_name, genome_low, genome_high, gc_low, gc_high
):
    safe = species_name.replace(" ", "_").replace(".", "_")
    p = tmp_path / "metrics.csv"
    p.write_text(
        f"{safe},Genome_Size,{genome_low},{genome_high}\n{safe},GC_Content,{gc_low},{gc_high}\n"
    )
    return str(p)


def test_handle_genome_size_coverage_pass_and_gc_pass(tmp_path):
    species = ["Escherichia coli"]
    metrics = write_metrics_file(tmp_path, "Escherichia coli", 900, 1100, 50, 52)
    cfg = {"metrics_file": metrics}

    # expected genome_size = (900+1100)/2 = 1000
    # read_total_bases = 30000 => estimated_coverage = 30 -> meets default threshold (30)
    fastp_stats = {"read_total_bases": 30000, "gc_content": 51}
    final = blank_sample_results("S1")

    updated = handle_genome_size(species, fastp_stats, final, cfg)

    assert updated["coverage_estimate_qualibact_status"] == "PASSED"
    assert "meets the threshold" in updated["coverage_estimate_qualibact_message"]
    assert updated["gc_content_status"] == "PASSED"


def test_handle_genome_size_coverage_fail_and_gc_warning(tmp_path):
    species = ["Escherichia coli"]
    metrics = write_metrics_file(tmp_path, "Escherichia coli", 900, 1100, 50, 52)
    cfg = {"metrics_file": metrics}

    # read_total_bases small -> estimated_coverage < 30 -> FAILED
    # gc_content slightly outside strict range but within fail percentage -> WARNING
    fastp_stats = {"read_total_bases": 10000, "gc_content": 49}
    final = blank_sample_results("S2")

    updated = handle_genome_size(species, fastp_stats, final, cfg)

    assert updated["coverage_estimate_qualibact_status"] == "FAILED"
    assert updated["gc_content_status"] == "WARNING"


def test_handle_genome_size_multiple_species_appends_warning(tmp_path):
    species = ["Escherichia coli", "Other sp."]
    metrics = write_metrics_file(tmp_path, "Escherichia coli", 900, 1100, 50, 52)
    cfg = {"metrics_file": metrics}

    fastp_stats = {"read_total_bases": 60000, "gc_content": 51}
    final = blank_sample_results("S3")

    updated = handle_genome_size(species, fastp_stats, final, cfg)

    # coverage should pass and the message should include the multiple-species warning
    assert updated["coverage_estimate_qualibact_status"] == "PASSED"
    assert "Multiple species detected" in updated["coverage_estimate_qualibact_message"]


def test_handle_genome_size_gc_outside_range_sets_message_and_leaves_status(tmp_path):
    species = ["Escherichia coli"]
    metrics = write_metrics_file(tmp_path, "Escherichia coli", 900, 1100, 50, 52)
    cfg = {"metrics_file": metrics}

    # gc_content well outside tolerance -> message set to outside expected range
    fastp_stats = {"read_total_bases": 60000, "gc_content": 40}
    final = blank_sample_results("S4")

    updated = handle_genome_size(species, fastp_stats, final, cfg)

    assert "outside expected range" in updated.get("gc_content_message", "")
    # blank_sample_results initializes gc_content_status to FAILED; function doesn't overwrite in 'else' branch
    assert updated.get("gc_content_status") == "FAILED"
