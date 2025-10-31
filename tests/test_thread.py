import os

from bactscout.thread import run_one_sample


def test_run_one_sample_nextflow_path_switching(monkeypatch):
    """Verify that when NXF_TASK_WORKDIR is set, run_one_sample tries the Nextflow paths
    for output and input files and prints informative messages when message=True.
    """
    # Set Nextflow workdir
    nxw = "/nx/work"
    monkeypatch.setenv("NXF_TASK_WORKDIR", nxw)

    sample_id = "sample1"
    read1 = "/orig/path/R1.fastq"
    read2 = "/orig/path/R2.fastq"
    output_dir = "/out"

    # expected nextflow-resolved paths
    expected_nx_r1 = os.path.join(nxw, os.path.basename(read1))
    expected_nx_r2 = os.path.join(nxw, os.path.basename(read2))
    expected_nx_output = os.path.join(
        nxw, os.path.basename(f"{output_dir}/{sample_id}")
    )

    # Capture printed messages
    printed = []

    def fake_print_message(msg, level="info"):
        printed.append((level, msg))

    monkeypatch.setattr("bactscout.thread.print_message", fake_print_message)

    # Mock external tool functions to avoid heavy processing
    monkeypatch.setattr("bactscout.thread.run_sylph", lambda *a, **k: {})
    monkeypatch.setattr(
        "bactscout.thread.extract_species_from_report", lambda *a, **k: ([], "")
    )
    monkeypatch.setattr("bactscout.thread.run_fastp", lambda *a, **k: {})
    # Return minimal fastp metrics to let logic continue
    monkeypatch.setattr(
        "bactscout.thread.get_fastp_results",
        lambda *a, **k: {
            "read_total_reads": 0,
            "read_total_bases": 0,
            "read_q20_bases": 0,
            "read_q30_bases": 0,
            "read_q20_rate": 0.0,
            "read_q30_rate": 0.0,
            "read1_mean_length": 0,
            "read2_mean_length": 0,
            "gc_content": 0.0,
            "duplication_rate": 0.0,
            "n_content_rate": 0.0,
            "read1_before_filtering": {},
        },
    )

    # Patch downstream functions to be no-ops where appropriate
    monkeypatch.setattr("bactscout.thread.handle_fastp_results", lambda x, c: x)
    monkeypatch.setattr("bactscout.thread.handle_duplication_results", lambda x, c: x)
    monkeypatch.setattr("bactscout.thread.handle_n_content_results", lambda x, c: x)
    monkeypatch.setattr("bactscout.thread.handle_adapter_detection", lambda x, c: x)
    monkeypatch.setattr(
        "bactscout.thread.handle_species_coverage", lambda sa, fr, c: (fr, [])
    )
    monkeypatch.setattr("bactscout.thread.handle_genome_size", lambda s, f, fr, c: fr)
    # Avoid writing files
    monkeypatch.setattr("bactscout.thread.write_summary_file", lambda *a, **k: None)

    # Control existence checks: original paths do not exist; nextflow paths do
    def fake_exists(path):
        if path in (read1, read2, os.path.join(output_dir, sample_id)):
            return False
        if path in (expected_nx_r1, expected_nx_r2, expected_nx_output):
            return True
        # default to True for other checks
        return True

    monkeypatch.setattr("bactscout.thread.os.path.exists", fake_exists)
    # Avoid actually creating directories
    monkeypatch.setattr("bactscout.thread.os.makedirs", lambda *a, **k: None)

    # Run
    cfg = {"mlst_species": {}, "bactscout_dbs_path": "/never"}
    res = run_one_sample(
        sample_id=sample_id,
        read1_file=read1,
        read2_file=read2,
        output_dir=output_dir,
        config=cfg,
        threads=1,
        message=True,
        report_resources=False,
    )

    # Ensure function completed (returns dict)
    assert isinstance(res, dict)

    # Check that messages include Nextflow path usage for output and inputs
    msgs = "\n".join(m for _, m in printed)
    assert "Using Nextflow path for output" in msgs
    assert "Using Nextflow path for R1" in msgs
    assert "Using Nextflow path for R2" in msgs
