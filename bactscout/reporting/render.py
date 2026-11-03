"""Render standalone reports using SpecCheck's established visual styling."""

import json
import os
import tempfile
from collections import Counter
from html import escape
from pathlib import Path

from bactscout.__version__ import __version__

from .model import STATUSES, adapt_record, load_records

ASSETS = Path(__file__).with_name("assets")


def _script_json(value):
    # JSON is data, never executable source. HTML parsers still recognise </script>
    # inside application/json; escaping '<' prevents that termination sequence.
    return (
        json.dumps(value, ensure_ascii=True, allow_nan=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def generate_report(input_path, output_path):
    """Write an offline HTML report without changing CSV files or QC decisions.

    Accept a BactScout per-sample/merged CSV, or an output directory. Direct
    final_summary CSVs take precedence over individual reports in a directory.
    ValueError explains absent, malformed or ambiguous inputs.
    """
    output = Path(output_path).expanduser().resolve()
    if output.suffix.lower() == ".csv":
        raise ValueError("HTML output must not overwrite CSV data. Choose report.html.")
    records, root = load_records(input_path)
    if any(output == source.resolve() for _, _, source in records):
        raise ValueError(
            "HTML output must not overwrite an input CSV. Choose report.html."
        )
    samples = [
        adapt_record(mode, row, source, root, output) for mode, row, source in records
    ]
    counts = Counter(
        sample["status"] if sample["status"] in STATUSES else "Unavailable"
        for sample in samples
    )
    needs_review = len(samples) - counts["PASSED"]
    kpis = [
        ("Samples", len(samples), "", "ALL"),
        ("Passed", counts["PASSED"], "pass", "PASSED"),
        ("Warnings", counts["WARNING"], "warn", "WARNING"),
        ("Failed", counts["FAILED"], "fail", "FAILED"),
        ("Unavailable status", counts["Unavailable"], "not-evaluated", "Unavailable"),
        ("Pass rate", f"{100 * counts['PASSED'] / len(samples):.1f}%", "", "ALL"),
    ]
    kpi_html = "".join(
        f'<button type="button" class="kpi-card kpi-{tone}" data-filter="{status}">'
        f'<span class="kpi-label">{label}</span><strong class="kpi-value">{value}</strong></button>'
        for label, value, tone, status in kpis
    )
    reasons = Counter(reason for sample in samples for reason in sample["review"])
    reasons_html = (
        "".join(
            f"<li><strong>{count}</strong> {escape(reason)}</li>"
            for reason, count in reasons.most_common(8)
        )
        or "<li>No warning or failure diagnostics were recorded.</li>"
    )
    data = {"samples": samples, "needs_review": needs_review, "version": __version__}
    template = (ASSETS / "report.html").read_text(encoding="utf-8")
    replacements = {
        "@@STYLE@@": (ASSETS / "report.css").read_text(encoding="utf-8"),
        "@@EXTRA_STYLE@@": (ASSETS / "bactscout.css").read_text(encoding="utf-8"),
        "@@SCRIPT@@": (ASSETS / "report.js").read_text(encoding="utf-8"),
        "@@DATA@@": _script_json(data),
        "@@VERSION@@": escape(__version__),
        "@@KPIS@@": kpi_html,
        "@@REVIEW_COUNT@@": str(needs_review),
        "@@SAMPLE_COUNT@@": str(len(samples)),
        "@@REASONS@@": reasons_html,
    }
    # Replace template tokens in one pass: untrusted diagnostics that happen to
    # contain a token must never become a later replacement target.
    import re

    document = re.sub(r"@@[A-Z_]+@@", lambda match: replacements[match[0]], template)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(document)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return output
