"""Read recorded BactScout decisions; never calculate QC flags in the report."""

import csv
import math
import os
from pathlib import Path
from urllib.parse import quote

MISSING = {"", "na", "n/a", "none", "null", "nan"}
STATUSES = {"PASSED", "WARNING", "FAILED"}


def display(value):
    """Keep real zeroes distinct from an absent measurement."""
    text = str(value).strip() if value is not None else ""
    return "Unavailable" if text.lower() in MISSING else text


def number(value, unit="", factor=1, integer=False):
    text = display(value)
    if text == "Unavailable":
        return text
    try:
        numeric = float(text) * factor
        if not math.isfinite(numeric):
            raise ValueError
    except ValueError:
        return f"Invalid value: {text}"
    formatted = f"{numeric:,.0f}" if integer else f"{numeric:,.2f}"
    return formatted + unit


def _schema(header):
    if "sample_id" not in header:
        return None
    if "a_final_status" in header:
        return "Short reads"
    if "status" in header and ("n50" in header or "platform" in header):
        return "Long reads"
    return None


def _read(path, required=False):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.reader(stream, strict=True)
        try:
            header = next(reader, [])
            mode = _schema(header)
            if mode is None:
                if required:
                    raise ValueError(f"Not a BactScout summary CSV: {path}")
                return []
            if len(set(header)) != len(header):
                raise ValueError(f"Duplicate column names in {path}")
            rows = []
            for values in reader:
                if not values:
                    continue
                if len(values) != len(header):
                    raise ValueError(
                        f"Malformed CSV {path}, line {reader.line_num}: expected "
                        f"{len(header)} columns, found {len(values)}. Regenerate or "
                        "correct the CSV with properly quoted diagnostic messages."
                    )
                row = dict(zip(header, values))
                if display(row["sample_id"]) == "Unavailable":
                    raise ValueError(
                        f"Missing sample_id in {path}, line {reader.line_num}"
                    )
                rows.append((mode, row, path))
            return rows
        except csv.Error as error:
            raise ValueError(
                f"Malformed CSV {path}, line {reader.line_num}: {error}"
            ) from error


def load_records(input_path):
    path = Path(input_path).expanduser().resolve()
    if path.is_file():
        rows = _read(path, required=True)
        root = path.parent
    elif path.is_dir():
        merged = [
            path / name for name in ("final_summary.csv", "final_summary_long.csv")
        ]
        selected = [candidate for candidate in merged if candidate.is_file()]
        if not selected:
            selected = sorted(path.rglob("*.csv"))
        rows = [row for candidate in selected for row in _read(candidate)]
        root = path
    else:
        raise ValueError(f"Report input does not exist: {path}")
    if not rows:
        raise ValueError(f"No BactScout sample rows found in {path}")
    seen = set()
    for mode, row, source in rows:
        key = (mode, row["sample_id"])
        if key in seen:
            raise ValueError(
                f"Duplicate {mode.lower()} sample_id {row['sample_id']!r} in {source}. "
                "Choose one run or a merged summary with unique sample IDs."
            )
        seen.add(key)
    return rows, root


def _fastp_link(sample_id, source, root, output):
    if not sample_id or any(char in sample_id for char in ("/", "\\")):
        return None
    candidates = [source.parent / f"{sample_id}.fastp.html"]
    if source.name in {"final_summary.csv", "final_summary_long.csv"}:
        candidates.extend(
            path
            for path in root.rglob("*.fastp.html")
            if path.name == f"{sample_id}.fastp.html"
        )
    for candidate in sorted(set(candidates)):
        resolved = candidate.resolve()
        if resolved.is_relative_to(root) and resolved.is_file():
            try:
                relative = Path(os.path.relpath(resolved, output.parent)).as_posix()
            except ValueError:  # Windows output and input on separate drives.
                continue
            return quote(relative, safe="/")
    return None


def _metric(row, label, key, status=None, message=None, **formatting):
    return {
        "label": label,
        "value": number(row.get(key), **formatting),
        "status": display(row.get(status)) if status else None,
        "message": display(row.get(message)) if message else None,
    }


def adapt_record(mode, row, source, root, output):
    original_row = row
    short = mode == "Short reads"
    status = display(row.get("a_final_status" if short else "status"))
    metrics = []
    if short:
        specs = [
            ("Reads", "read_total_reads", None, None, {"integer": True}),
            ("Sequenced bases", "read_total_bases", None, None, {"integer": True}),
            (
                "Bases at Q30",
                "read_q30_rate",
                "read_q30_status",
                "read_q30_message",
                {"factor": 100, "unit": "%"},
            ),
            (
                "Read 1 mean length",
                "read1_mean_length",
                "read_length_status",
                "read_length_message",
                {"unit": " bp"},
            ),
            (
                "Read 2 mean length",
                "read2_mean_length",
                "read_length_status",
                "read_length_message",
                {"unit": " bp"},
            ),
            (
                "GC content",
                "gc_content",
                "gc_content_status",
                "gc_content_message",
                {"unit": "%"},
            ),
            (
                "Sylph coverage",
                "coverage_estimate_sylph",
                "coverage_status",
                "coverage_estimate_sylph_message",
                {"unit": "×"},
            ),
            (
                "Genome-size coverage",
                "coverage_estimate_qualibact",
                "coverage_estimate_qualibact_status",
                "coverage_estimate_qualibact_message",
                {"unit": "×"},
            ),
            (
                "Dominant taxonomic abundance",
                "species_abundance",
                "contamination_status",
                "contamination_message",
                {"unit": "%"},
            ),
            (
                "Duplication",
                "duplication_rate",
                "duplication_status",
                "duplication_message",
                {"factor": 100, "unit": "%"},
            ),
            (
                "N-content",
                "n_content_rate",
                "n_content_status",
                "n_content_message",
                {"unit": "%"},
            ),
        ]
        # Older summaries store these same measurements under legacy column names.
        row = dict(row)
        # The short-read summary may retain abundances for several taxa. Show
        # the first (dominant) measurement here and retain the entire raw list.
        if "species_abundance" in row:
            dominant_abundance = row["species_abundance"].split(";", 1)[0].strip()
        else:
            dominant_abundance = None
        for current, legacy in {
            "coverage_estimate_sylph": "coverage_estimate",
            "coverage_estimate_sylph_message": "coverage_message",
            "coverage_estimate_qualibact": "coverage_alt_estimate",
            "coverage_estimate_qualibact_status": "coverage_alt_status",
            "coverage_estimate_qualibact_message": "coverage_alt_message",
        }.items():
            if current not in row and legacy in row:
                row[current] = row[legacy]
    else:
        specs = [
            ("Reads", "read_count", None, None, {"integer": True}),
            ("Sequenced bases", "total_bases", None, None, {"integer": True}),
            ("Median read quality", "median_q", "flag_quality", None, {"unit": " Q"}),
            ("Read N50", "n50", "flag_n50", None, {"unit": " bp", "integer": True}),
            ("Mean read length", "mean_len", None, None, {"unit": " bp"}),
            (
                "Sylph coverage",
                "coverage_estimate_sylph",
                "flag_coverage_sylph",
                None,
                {"unit": "×"},
            ),
            (
                "Genome-size coverage",
                "coverage_estimate_calc",
                "flag_coverage_calc",
                None,
                {"unit": "×"},
            ),
            (
                "Non-dominant abundance",
                "contamination_pct",
                "flag_contam",
                None,
                {"unit": "%"},
            ),
        ]
    for label, key, flag, message, formatting in specs:
        metric = _metric(row, label, key, flag, message, **formatting)
        if short and key == "species_abundance":
            metric["value"] = number(dominant_abundance, **formatting)
        metrics.append(metric)
    if short:
        adapter_message = display(row.get("adapter_detection_message"))
        adapter_unavailable = adapter_message.startswith(
            ("Overrepresented-sequence analysis unavailable", "No reads processed.")
        )
        metrics.extend(
            [
                {
                    "label": "MLST sequence type",
                    "value": display(row.get("mlst_st")),
                    "status": display(row.get("mlst_status")),
                    "message": display(row.get("mlst_message")),
                },
                {
                    "label": "Overrepresented-sequence check",
                    "value": "Unavailable"
                    if adapter_unavailable
                    else "See recorded diagnostic",
                    "status": display(row.get("adapter_detection_status")),
                    "message": display(row.get("adapter_detection_message")),
                },
            ]
        )
    diagnostics = []
    for key, value in row.items():
        if key.endswith("_message") or key == "reasons":
            if display(value) != "Unavailable" and value not in diagnostics:
                diagnostics.append(value)
    review = []
    for key, flag in row.items():
        if flag not in {"WARNING", "FAILED"}:
            continue
        if key == "a_final_status" or key == "status":
            continue
        if short:
            message = row.get(key.removesuffix("_status") + "_message")
            if key == "coverage_status":
                message = row.get("coverage_estimate_sylph_message", message)
        else:
            message = row.get("reasons")
        text = message or key.replace("_", " ")
        if text not in review:
            review.append(text)
    if status not in {"PASSED"} and not review:
        review = [row.get("reasons") or "No diagnostic explanation was recorded."]
    metric_map = {metric["label"]: metric["value"] for metric in metrics}
    resources = [
        {
            "label": key.removeprefix("resource_").replace("_", " "),
            "value": display(value),
        }
        for key, value in row.items()
        if key.startswith("resource_")
    ]
    return {
        "id": row["sample_id"],
        "read_type": mode,
        "status": status,
        "species": display(row.get("species" if short else "top_taxon")),
        "platform": "Paired-end short reads" if short else display(row.get("platform")),
        "quality": metric_map["Bases at Q30" if short else "Median read quality"],
        "sylph_coverage": metric_map["Sylph coverage"],
        "calculated_coverage": metric_map["Genome-size coverage"],
        "mlst": display(row.get("mlst_st")) if short else "Not applicable",
        "metrics": metrics,
        "review": review,
        "diagnostics": diagnostics,
        "resources": resources,
        "raw": original_row,
        "source": str(source.relative_to(root)),
        "fastp": _fastp_link(row["sample_id"], source, root, output) if short else None,
    }
