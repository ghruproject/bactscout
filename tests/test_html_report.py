"""Reporting reads recorded decisions, preserves units and escapes untrusted data."""

import csv
import json
import re

import pytest

from bactscout.reporting import generate_report


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return path


def short_sample(**changes):
    row = {
        "sample_id": "AP001",
        "a_final_status": "WARNING",
        "species": "Klebsiella pneumoniae",
        "species_abundance": "100.0",
        "read_total_reads": "1139700",
        "read_total_bases": "170955000",
        "read_q30_rate": ".906612",
        "read_q30_status": "PASSED",
        "read_q30_message": "Meets threshold",
        "read1_mean_length": "150",
        "read2_mean_length": "150",
        "gc_content": "57.2015",
        "gc_content_status": "PASSED",
        "coverage_estimate_sylph": "29.34",
        "coverage_status": "WARNING",
        "coverage_estimate_sylph_message": "Coverage below recommended 30x",
        "coverage_estimate_qualibact": "30.26",
        "coverage_estimate_qualibact_status": "PASSED",
        "duplication_rate": ".000114065",
        "n_content_rate": "",
        "n_content_status": "WARNING",
        "n_content_message": "N-content unavailable; no aggregate N-base count",
        "adapter_detection_status": "WARNING",
        "adapter_detection_message": "Overrepresentation analysis disabled",
        "mlst_st": "14",
        "mlst_status": "PASSED",
        "resource_duration_sec": "20.5",
    }
    row.update(changes)
    return row


def long_sample(**changes):
    row = {
        "sample_id": "long_example",
        "platform": "ont_r10",
        "status": "FAILED",
        "read_count": "100",
        "total_bases": "500000",
        "n50": "5208",
        "median_q": "7.18",
        "top_taxon": "",
        "coverage_estimate_sylph": "",
        "coverage_estimate_calc": "0",
        "contamination_pct": "",
        "flag_quality": "FAILED",
        "flag_n50": "WARNING",
        "flag_coverage_calc": "FAILED",
        "reasons": "Low quality; no taxon detected",
    }
    row.update(changes)
    return row


def data_from_html(path):
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="report-data" type="application/json">(.*?)</script>', text, re.S
    )
    return json.loads(match[1]), text


def metric(sample, name):
    return next(item for item in sample["metrics"] if item["label"] == name)


def test_short_read_units_flags_and_missing_measurements(tmp_path):
    source = write_csv(tmp_path / "AP001_summary.csv", [short_sample()])
    data, html = data_from_html(generate_report(source, tmp_path / "report.html"))
    sample = data["samples"][0]
    assert sample["status"] == "WARNING"
    assert sample["quality"] == "90.66%"
    assert metric(sample, "GC content")["value"] == "57.20%"
    assert metric(sample, "Reads")["value"] == "1,139,700"
    assert metric(sample, "Duplication")["value"] == "0.01%"
    assert metric(sample, "N-content")["value"] == "Unavailable"
    assert metric(sample, "N-content")["status"] == "WARNING"
    assert metric(sample, "Sylph coverage")["status"] == "WARNING"
    assert metric(sample, "Genome-size coverage")["status"] == "PASSED"
    assert sample["mlst"] == "14"
    assert "N-content unavailable; no aggregate N-base count" in sample["review"]
    assert "Overrepresentation analysis disabled" in sample["review"]
    assert sample["resources"] == [{"label": "duration sec", "value": "20.5"}]
    assert "--accent: #1f5f8b" in html  # Actual copied SpecCheck palette.


def test_real_zero_is_not_missing_and_mixed_abundances_keep_full_raw_data(tmp_path):
    source = write_csv(
        tmp_path / "summary.csv",
        [
            short_sample(
                n_content_rate="0",
                n_content_status="PASSED",
                species_abundance="87.5;12.5",
                species="Klebsiella pneumoniae;Escherichia coli",
            )
        ],
    )
    sample = data_from_html(generate_report(source, tmp_path / "report.html"))[0][
        "samples"
    ][0]
    assert metric(sample, "N-content")["value"] == "0.00%"
    assert metric(sample, "Dominant taxonomic abundance")["value"] == "87.50%"
    assert sample["raw"]["species_abundance"] == "87.5;12.5"
    assert "Escherichia coli" in sample["species"]


def test_disabled_overrepresentation_is_explicitly_unavailable(tmp_path):
    source = write_csv(
        tmp_path / "summary.csv",
        [
            short_sample(
                adapter_detection_message="Overrepresented-sequence analysis unavailable or disabled. Adapter contamination has not been assessed by this check."
            )
        ],
    )
    data, _ = data_from_html(generate_report(source, tmp_path / "report.html"))
    adapter = metric(data["samples"][0], "Overrepresented-sequence check")
    assert adapter["value"] == "Unavailable"
    assert adapter["status"] == "WARNING"
    assert "has not been assessed" in adapter["message"]


def test_legacy_coverage_aliases_do_not_change_raw_source_columns(tmp_path):
    row = short_sample()
    row["coverage_alt_estimate"] = row.pop("coverage_estimate_qualibact")
    row["coverage_alt_status"] = row.pop("coverage_estimate_qualibact_status")
    source = write_csv(tmp_path / "legacy.csv", [row])
    data, _ = data_from_html(generate_report(source, tmp_path / "report.html"))
    sample = data["samples"][0]
    assert sample["calculated_coverage"] == "30.26×"
    assert sample["raw"] == row


def test_long_schema_has_phred_n50_and_distinct_missing_and_zero(tmp_path):
    source = write_csv(tmp_path / "sample_long_summary.csv", [long_sample()])
    data, _ = data_from_html(generate_report(source, tmp_path / "report.html"))
    sample = data["samples"][0]
    assert sample["read_type"] == "Long reads"
    assert sample["quality"] == "7.18 Q"
    assert metric(sample, "Read N50")["value"] == "5,208 bp"
    assert sample["sylph_coverage"] == "Unavailable"
    assert sample["calculated_coverage"] == "0.00×"
    assert sample["mlst"] == "Not applicable"
    assert sample["status"] == "FAILED"
    assert data["needs_review"] == 1


def test_merged_summaries_take_precedence_and_support_both_read_types(tmp_path):
    write_csv(tmp_path / "final_summary.csv", [short_sample()])
    write_csv(tmp_path / "final_summary_long.csv", [long_sample(sample_id="AP001")])
    write_csv(tmp_path / "AP001" / "AP001_summary.csv", [short_sample()])
    data, _ = data_from_html(generate_report(tmp_path, tmp_path / "report.html"))
    assert len(data["samples"]) == 2
    assert {sample["read_type"] for sample in data["samples"]} == {
        "Short reads",
        "Long reads",
    }


def test_directory_scan_ignores_other_csv_files(tmp_path):
    write_csv(tmp_path / "AP001" / "AP001_summary.csv", [short_sample()])
    write_csv(tmp_path / "AP001" / "tool-output.csv", [{"unrelated": "value"}])
    data, _ = data_from_html(generate_report(tmp_path, tmp_path / "report.html"))
    assert len(data["samples"]) == 1


@pytest.mark.parametrize(
    "content",
    [
        "sample_id,a_final_status,read_q30_rate\nfoo,WARNING,.8,unquoted extra\n",
        "sample_id,a_final_status,read_q30_rate\nfoo,WARNING\n",
        'sample_id,a_final_status,read_q30_rate\n"unterminated,WARNING,.8\n',
        "sample_id,a_final_status,a_final_status\nfoo,WARNING,PASSED\n",
    ],
)
def test_malformed_csv_fails_without_clobbering_report(tmp_path, content):
    source = tmp_path / "sample.csv"
    source.write_text(content)
    output = tmp_path / "report.html"
    output.write_text("previous report")
    with pytest.raises(ValueError, match="Malformed|Duplicate column"):
        generate_report(source, output)
    assert output.read_text() == "previous report"


def test_duplicate_ids_are_rejected_without_silent_data_loss(tmp_path):
    source = write_csv(tmp_path / "summary.csv", [short_sample(), short_sample()])
    with pytest.raises(ValueError, match="Duplicate short reads sample_id"):
        generate_report(source, tmp_path / "report.html")


def test_html_and_script_content_are_never_executable(tmp_path):
    hostile = (
        '</script><img src=x onerror="alert(1)"><script>alert(2)</script>@@SCRIPT@@'
    )
    source = write_csv(
        tmp_path / "summary.csv",
        [
            short_sample(
                sample_id=hostile,
                n_content_message=hostile,
                species=hostile,
            )
        ],
    )
    data, html = data_from_html(generate_report(source, tmp_path / "report.html"))
    assert data["samples"][0]["id"] == hostile
    assert data["samples"][0]["raw"]["n_content_message"] == hostile
    assert '<img src=x onerror="alert(1)">' not in html
    assert "<script>alert(2)</script>" not in html
    assert "\\u003c/script\\u003e" in html
    assert "&lt;img" in html
    assert "innerHTML" not in html
    assert "@@SCRIPT@@" in data["samples"][0]["id"]


def test_fastp_links_are_local_encoded_and_respect_output_location(tmp_path):
    source = write_csv(
        tmp_path / "results" / "a sample" / "summary.csv",
        [short_sample(sample_id="a sample")],
    )
    (source.parent / "a sample.fastp.html").write_text("report")
    data, _ = data_from_html(
        generate_report(source.parent.parent, tmp_path / "view" / "report.html")
    )
    assert data["samples"][0]["fastp"] == "../results/a%20sample/a%20sample.fastp.html"


def test_fastp_links_never_follow_traversal_or_symlinks_outside_input(tmp_path):
    outside = tmp_path / "outside.fastp.html"
    outside.write_text("outside")
    root = tmp_path / "results"
    root.mkdir()
    source = write_csv(root / "summary.csv", [short_sample()])
    try:
        (root / "AP001.fastp.html").symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks is not available in this environment")
    data, _ = data_from_html(generate_report(source, root / "report.html"))
    assert data["samples"][0]["fastp"] is None
    write_csv(source, [short_sample(sample_id="../outside")])
    data, _ = data_from_html(generate_report(source, root / "report.html"))
    assert data["samples"][0]["fastp"] is None


def test_fastp_link_on_another_windows_drive_is_omitted(tmp_path, monkeypatch):
    import bactscout.reporting.model as model

    source = write_csv(tmp_path / "summary.csv", [short_sample()])
    (tmp_path / "AP001.fastp.html").write_text("report")

    def different_drive(*args):
        raise ValueError("path is on another drive")

    monkeypatch.setattr(model.os.path, "relpath", different_drive)
    data, _ = data_from_html(generate_report(source, tmp_path / "report.html"))
    assert data["samples"][0]["fastp"] is None


def test_output_cannot_overwrite_csv(tmp_path):
    source = write_csv(tmp_path / "summary.csv", [short_sample()])
    before = source.read_bytes()
    with pytest.raises(ValueError, match="must not overwrite"):
        generate_report(source, source)
    assert source.read_bytes() == before


def test_unknown_status_and_invalid_numeric_value_are_preserved(tmp_path):
    source = write_csv(
        tmp_path / "summary.csv",
        [short_sample(a_final_status="ERROR", gc_content="garbage")],
    )
    data, html = data_from_html(generate_report(source, tmp_path / "report.html"))
    assert data["samples"][0]["status"] == "ERROR"
    assert data["needs_review"] == 1
    assert metric(data["samples"][0], "GC content")["value"] == "Invalid value: garbage"
    assert 'knownStatuses.has(sample.status) ? sample.status : "Unavailable"' in html


@pytest.mark.parametrize("kind", ["missing", "empty", "unsupported"])
def test_empty_and_non_report_inputs_fail_helpfully(tmp_path, kind):
    path = tmp_path / "input.csv"
    if kind == "empty":
        path.write_text("sample_id,a_final_status\n")
    elif kind == "unsupported":
        path.write_text("unrelated,value\na,b\n")
    with pytest.raises(
        ValueError,
        match="does not exist|No BactScout sample rows|Not a BactScout summary",
    ):
        generate_report(path, tmp_path / "report.html")


def test_report_has_embedded_assets_and_no_remote_asset_dependency(tmp_path):
    source = write_csv(tmp_path / "summary.csv", [short_sample()])
    _, html = data_from_html(generate_report(source, tmp_path / "report.html"))
    assert "<script src=" not in html
    assert '<link rel="stylesheet"' not in html
    assert "@import" not in html
    assert "https://fonts." not in html
    assert 'class="report-sidebar"' in html
    assert 'id="sample-detail-dialog"' in html
    assert 'id="page-size"' in html
    assert "2948c042" in html
