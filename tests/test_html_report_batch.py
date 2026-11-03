"""Batch reports retain recorded QC decisions and paginate the actual controls."""

import json
import shutil
import subprocess

import pytest

from bactscout.reporting import generate_report
from tests.test_html_report import data_from_html, long_sample, short_sample, write_csv


def test_batch_counts_and_recorded_checks(tmp_path):
    rows = [
        short_sample(
            sample_id=f"display-fixture-{index:03}",
            a_final_status=("PASSED", "WARNING", "FAILED")[index % 3],
        )
        for index in range(100)
    ]
    source = write_csv(tmp_path / "summary.csv", rows)
    data, html = data_from_html(generate_report(source, tmp_path / "report.html"))
    assert len(data["samples"]) == 100
    assert data["needs_review"] == 66
    assert [sample["raw"] for sample in data["samples"]] == rows
    assert "option selected>10</option>" in html
    assert [check["label"] for check in data["samples"][0]["review_checks"]] == [
        "Sylph coverage",
        "N-content unavailable",
        "Overrepresentation",
    ]
    # An inconsistent overall PASSED decision must not hide recorded warnings.
    assert data["samples"][0]["status"] == "PASSED"
    assert data["samples"][0]["review_checks"][0] == {
        "label": "Sylph coverage",
        "status": "WARNING",
        "message": "Coverage below recommended 30x",
    }


def test_long_and_legacy_flags_keep_recorded_diagnostics(tmp_path):
    short = short_sample(coverage_estimate_qualibact_status="FAILED")
    short["coverage_alt_status"] = short.pop("coverage_estimate_qualibact_status")
    write_csv(tmp_path / "final_summary.csv", [short])
    write_csv(tmp_path / "final_summary_long.csv", [long_sample()])
    data, _ = data_from_html(generate_report(tmp_path, tmp_path / "report.html"))
    checks = {
        sample["read_type"]: sample["review_checks"] for sample in data["samples"]
    }
    assert ("Genome-size coverage", "FAILED") in [
        (item["label"], item["status"]) for item in checks["Short reads"]
    ]
    assert checks["Long reads"] == [
        {"label": label, "status": flag, "message": "Low quality; no taxon detected"}
        for label, flag in [
            ("Median Q", "FAILED"),
            ("N50", "WARNING"),
            ("Genome-size coverage", "FAILED"),
        ]
    ]


def test_missing_flags_are_not_derived_from_values(tmp_path):
    row = {
        "sample_id": "missing-flags",
        "a_final_status": "",
        "read_q30_rate": "0",
        "coverage_estimate_sylph": "0",
    }
    source = write_csv(tmp_path / "summary.csv", [row])
    sample = data_from_html(generate_report(source, tmp_path / "report.html"))[0][
        "samples"
    ][0]
    assert sample["status"] == "Unavailable"
    assert sample["review_checks"] == []
    assert sample["quality"] == "0.00%"
    assert sample["sylph_coverage"] == "0.00×"
    assert sample["raw"] == row


def test_unavailable_checks_retain_warning_and_verbatim_message(tmp_path):
    message = "Overrepresented-sequence analysis unavailable or disabled. Adapter contamination has not been assessed by this check."
    source = write_csv(
        tmp_path / "summary.csv", [short_sample(adapter_detection_message=message)]
    )
    sample = data_from_html(generate_report(source, tmp_path / "report.html"))[0][
        "samples"
    ][0]
    assert sample["review_checks"][-1] == {
        "label": "Overrepresentation unavailable",
        "status": "WARNING",
        "message": message,
    }


@pytest.mark.skipif(
    shutil.which("node") is None, reason="Node is needed to exercise report controls"
)
def test_actual_controls_keep_review_default_and_paginate_large_batches(tmp_path):
    rows = [
        short_sample(
            sample_id=f"fixture-{index:03}",
            a_final_status="PASSED" if index % 2 else "WARNING",
        )
        for index in range(251)
    ]
    source = write_csv(tmp_path / "summary.csv", rows)
    report = generate_report(source, tmp_path / "report.html")
    data, html = data_from_html(report)
    script = html.split("<script>")[-1].split("</script>")[0]
    # A small DOM stand-in executes the shipped controller and its event handlers;
    # browser QA separately covers geometry, scrolling, focus and mobile layout.
    harness = r"""
const assert = require("node:assert/strict");
class Element {
  constructor() { this.children=[]; this.value=""; this.dataset={}; this.handlers={}; this.classList={add(){},toggle(){}}; }
  append(...items) { this.children.push(...items); }
  replaceChildren() { this.children=[]; }
  setAttribute() {}
  addEventListener(event, callback) { this.handlers[event]=callback; }
  click() { this.handlers.click(); }
}
const elements = new Map();
function element(id) { if (!elements.has(id)) elements.set(id,new Element()); return elements.get(id); }
const filters = ["ALL","REVIEW","PASSED","WARNING","FAILED","Unavailable"].map(status => {
  const node = new Element(); node.dataset.filter=status; return node;
});
global.document={getElementById:element,createElement:()=>new Element(),querySelector:element,
  querySelectorAll:selector => selector === "[data-filter]" ? filters : []};
element("report-data").textContent=JSON.stringify(DATA);
element("page-size").value="10";
SCRIPT
function count() { return element("sample-rows").children.length; }
assert.equal(count(),10);
assert.equal(element("filter-summary").textContent,"Showing 1–10 of 126 matching samples (251 total).");
assert.equal(element("page-summary").textContent,"Page 1 of 13");
filters.find(node => node.dataset.filter === "ALL").click();
assert.equal(count(),10);
assert.equal(element("filter-summary").textContent,"Showing 1–10 of 251 matching samples (251 total).");
element("page-size").value="100"; element("page-size").handlers.change();
assert.equal(count(),100);
element("next-page").click(); assert.equal(count(),100);
assert.equal(element("page-summary").textContent,"Page 2 of 3");
element("next-page").click(); assert.equal(count(),51);
assert.equal(element("next-page").disabled,true);
filters.find(node => node.dataset.filter === "REVIEW").click(); assert.equal(count(),100);
assert.equal(element("page-summary").textContent,"Page 1 of 2");
element("next-page").click(); assert.equal(count(),26);
element("sample-search").value="no match"; element("sample-search").handlers.input();
assert.equal(element("sample-rows").children[0].children[0].textContent,"No samples match these filters.");
assert.equal(element("next-page").disabled,true);
"""
    result = subprocess.run(
        [
            shutil.which("node"),
            "-e",
            harness.replace("DATA", json.dumps(data), 1).replace("SCRIPT", script, 1),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
