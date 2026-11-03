"""Optional HTML output must not change default analysis or reuse stale results."""

import csv
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

import bactscout.bactscout as cli
from bactscout.collect import collect_sample
from bactscout.long.collect import collect_sample_long
from bactscout.summary import summary_dir

runner = CliRunner()
COMMANDS = [
    (["qc", "reads"], "main"),
    (["collect", "one_R1.fastq.gz", "one_R2.fastq.gz"], "collect_sample"),
    (["summary", "results"], "summary_dir"),
    (["long", "qc", "reads", "--platform", "ont_r10"], "main_long"),
    (
        ["long", "collect", "one.fastq.gz", "--platform", "ont_r10"],
        "collect_sample_long",
    ),
    (["long", "summary", "results"], "summary_dir_long"),
]


def write_csv(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return path


@pytest.mark.parametrize("long_reads", [False, True])
def test_report_command_uses_existing_results_without_analysis(
    tmp_path, monkeypatch, long_reads
):
    row = (
        {
            "sample_id": "one",
            "status": "FAILED",
            "read_count": "1000",
            "median_q": "7",
            "platform": "ont_r10",
        }
        if long_reads
        else {
            "sample_id": "one",
            "a_final_status": "FAILED",
            "read_total_reads": "1000",
            "read_q30_rate": ".5",
            "species": "Escherichia coli",
        }
    )
    source = write_csv(tmp_path / "one.csv", row)
    before = source.read_bytes()
    for _, helper in COMMANDS:
        monkeypatch.setattr(
            cli, helper, Mock(side_effect=AssertionError("Analysis must not run"))
        )
    destination = tmp_path / "report.html"

    result = runner.invoke(cli.app, ["report", str(source), "-o", str(destination)])

    assert result.exit_code == 0, result.output
    assert destination.is_file()
    assert "FAILED" in destination.read_text()
    assert source.read_bytes() == before


@pytest.mark.parametrize("args,helper", COMMANDS)
def test_html_option_renders_only_newly_written_csv(
    tmp_path, monkeypatch, args, helper
):
    source = tmp_path / "new_summary.csv"
    destination = tmp_path / "new_report.html"
    analysis = Mock(return_value=source)
    render = Mock(return_value=destination)
    monkeypatch.setattr(cli, helper, analysis)
    monkeypatch.setattr(cli, "generate_report", render)

    result = runner.invoke(
        cli.app, args + ["-o", str(tmp_path), "--html-report", str(destination)]
    )

    assert result.exit_code == 0, result.output
    analysis.assert_called_once()
    render.assert_called_once_with(source, destination)


@pytest.mark.parametrize("args,helper", COMMANDS)
def test_default_does_not_render_html(tmp_path, monkeypatch, args, helper):
    monkeypatch.setattr(cli, helper, Mock(return_value=tmp_path / "new_summary.csv"))
    render = Mock(side_effect=AssertionError("HTML is opt-in"))
    monkeypatch.setattr(cli, "generate_report", render)

    result = runner.invoke(cli.app, args + ["-o", str(tmp_path)])

    assert result.exit_code == 0, result.output
    render.assert_not_called()
    assert not list(tmp_path.glob("*.html"))


@pytest.mark.parametrize("args,helper", COMMANDS)
def test_failed_processing_never_uses_stale_results(
    tmp_path, monkeypatch, args, helper
):
    (tmp_path / "final_summary.csv").write_text("stale CSV")
    destination = tmp_path / "report.html"
    destination.write_text("previous report")
    monkeypatch.setattr(cli, helper, Mock(return_value=None))
    render = Mock(
        side_effect=AssertionError("Failed processing must not generate HTML")
    )
    monkeypatch.setattr(cli, "generate_report", render)

    result = runner.invoke(
        cli.app, args + ["-o", str(tmp_path), "--html-report", str(destination)]
    )

    assert result.exit_code == 1
    assert "HTML report not generated" in result.output
    render.assert_not_called()
    assert destination.read_text() == "previous report"


def test_bad_report_input_has_actionable_cli_error(tmp_path):
    source = tmp_path / "malformed.csv"
    source.write_text(
        "sample_id,a_final_status,read_total_reads\none,WARNING,100,unquoted extra field\n"
    )
    destination = tmp_path / "report.html"

    result = runner.invoke(cli.app, ["report", str(source), "-o", str(destination)])

    assert result.exit_code == 1
    assert "Could not generate HTML report" in result.output
    assert not destination.exists()


def test_summary_returns_nextflow_destination(tmp_path, monkeypatch):
    work = tmp_path / "nextflow"
    source = work / "input" / "sample" / "sample_summary.csv"
    write_csv(source, {"sample_id": "sample", "a_final_status": "FAILED"})
    monkeypatch.setenv("NXF_TASK_WORKDIR", str(work))

    result = summary_dir("other/input", "other/final_summary.csv")

    assert result == work / "final_summary.csv"
    assert result.is_file()


def test_short_collect_returns_sample_csv_even_with_stale_batch_summary(
    tmp_path, monkeypatch
):
    import importlib

    module = importlib.import_module("bactscout.collect")
    (tmp_path / "final_summary.csv").write_text("stale batch")
    monkeypatch.setattr(module, "load_config", Mock(return_value={}))
    monkeypatch.setattr(
        module, "apply_database_destination", lambda config, database: config
    )
    monkeypatch.setattr(module, "preflight_check", Mock(return_value=True))
    monkeypatch.setattr(
        module, "run_one_sample", Mock(return_value={"status": "success"})
    )

    result = collect_sample(
        "one_R1.fastq.gz", "one_R2.fastq.gz", str(tmp_path), 1, "config", True
    )

    assert result == tmp_path / "one" / "one_summary.csv"


def test_long_collect_returns_sample_csv_even_with_stale_batch_summary(
    tmp_path, monkeypatch
):
    import importlib

    module = importlib.import_module("bactscout.long.collect")
    (tmp_path / "final_summary_long.csv").write_text("stale batch")
    monkeypatch.setattr(module, "load_config", Mock(return_value={}))
    monkeypatch.setattr(
        module, "apply_database_destination", lambda config, database: config
    )
    monkeypatch.setattr(module, "preflight_check_long", Mock(return_value=True))
    monkeypatch.setattr(
        module, "run_one_long_sample", Mock(return_value={"status": "success"})
    )

    result = collect_sample_long(
        "one.fastq.gz", str(tmp_path), 1, "config", "ont_r10", True
    )

    assert result == tmp_path / "one" / "one_long_summary.csv"


@pytest.mark.parametrize("long_reads", [False, True])
def test_collect_preflight_failure_cannot_report_old_sample(
    tmp_path, monkeypatch, long_reads
):
    import importlib

    module = importlib.import_module(
        "bactscout.long.collect" if long_reads else "bactscout.collect"
    )
    old_csv = (
        tmp_path / "one" / ("one_long_summary.csv" if long_reads else "one_summary.csv")
    )
    old_csv.parent.mkdir()
    old_csv.write_text("stale sample")
    monkeypatch.setattr(module, "load_config", Mock(return_value={}))
    monkeypatch.setattr(
        module, "apply_database_destination", lambda config, database: config
    )
    monkeypatch.setattr(
        module,
        "preflight_check_long" if long_reads else "preflight_check",
        Mock(return_value=False),
    )
    analysis = Mock(
        side_effect=AssertionError("Preflight failure must stop processing")
    )
    monkeypatch.setattr(
        module, "run_one_long_sample" if long_reads else "run_one_sample", analysis
    )
    render = Mock(side_effect=AssertionError("Old sample must not be reported"))
    monkeypatch.setattr(cli, "generate_report", render)
    arguments = (
        ["long", "collect", "one.fastq.gz", "--platform", "ont_r10"]
        if long_reads
        else ["collect", "one_R1.fastq.gz", "one_R2.fastq.gz"]
    )

    result = runner.invoke(
        cli.app,
        arguments
        + ["-o", str(tmp_path), "--html-report", str(tmp_path / "report.html")],
    )

    assert result.exit_code == 1
    assert "HTML report not generated" in result.output
    assert old_csv.read_text() == "stale sample"
    analysis.assert_not_called()
    render.assert_not_called()
