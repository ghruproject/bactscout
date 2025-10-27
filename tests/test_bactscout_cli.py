"""Tests for bactscout.py CLI module."""

import importlib.util
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

bactscout_path = Path(__file__).parent.parent / "bactscout.py"
spec = importlib.util.spec_from_file_location("bactscout_cli", bactscout_path)
app: Any = None
if spec and spec.loader:
    bactscout_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bactscout_module)
    app = bactscout_module.app

runner = CliRunner()


class TestCLI:
    """Integration tests for the CLI."""

    def test_app_has_all_commands(self):
        """Test that app has all expected commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "qc" in result.stdout
        assert "collect" in result.stdout
        assert "summary" in result.stdout

    def test_qc_command_help(self):
        """Test qc command help text."""
        result = runner.invoke(app, ["qc", "--help"])
        assert result.exit_code == 0
        assert "--skip-preflight" in result.stdout
        assert "--threads" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout

    def test_collect_command_help(self):
        """Test collect command help text."""
        result = runner.invoke(app, ["collect", "--help"])
        assert result.exit_code == 0
        assert "--threads" in result.stdout
        assert "--output" in result.stdout or "-o" in result.stdout

    def test_summary_command_help(self):
        """Test summary command help text."""
        result = runner.invoke(app, ["summary", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.stdout or "-o" in result.stdout

    def test_invalid_command(self):
        """Test that invalid command returns error."""
        result = runner.invoke(app, ["invalid"])
        assert result.exit_code != 0

    def test_qc_missing_required_argument(self):
        """Test that qc requires input_dir argument."""
        result = runner.invoke(app, ["qc"])
        assert result.exit_code != 0

    def test_collect_missing_required_argument(self):
        """Test that collect requires input_dir argument."""
        result = runner.invoke(app, ["collect"])
        assert result.exit_code != 0

    def test_summary_missing_required_argument(self):
        """Test that summary requires input_dir argument."""
        result = runner.invoke(app, ["summary"])
        assert result.exit_code != 0

    def test_invalid_thread_count_qc(self):
        """Test that invalid thread count returns error for qc."""
        result = runner.invoke(app, ["qc", "/input", "--threads", "invalid"])
        assert result.exit_code != 0

    def test_invalid_thread_count_collect(self):
        """Test that invalid thread count returns error for collect."""
        result = runner.invoke(
            app,
            [
                "collect",
                "/input_R1.fastq.gz",
                "/input_R2.fastq.gz",
                "--threads",
                "invalid",
            ],
        )
        assert result.exit_code != 0

    def test_qc_accepts_output_option(self):
        """Test qc accepts output option."""
        result = runner.invoke(app, ["qc", "/input", "--output", "/output"])
        # Should succeed or fail gracefully, not due to arg parsing
        assert "--output" in result.stdout or result.exit_code in (0, 1)

    def test_collect_accepts_output_option(self):
        """Test collect accepts output option with R1 and R2 files."""
        result = runner.invoke(
            app,
            [
                "collect",
                "/input_R1.fastq.gz",
                "/input_R2.fastq.gz",
                "--output",
                "/output",
            ],
        )
        # Should succeed or fail gracefully, not due to arg parsing (exit code 1 is file not found, which is ok)
        assert result.exit_code in (0, 1)

    def test_qc_accepts_threads_option(self):
        """Test qc accepts threads option."""
        result = runner.invoke(app, ["qc", "/input", "--threads", "4"])
        # Should succeed or fail gracefully, not due to arg parsing
        assert result.exit_code in (0, 1)

    def test_qc_accepts_short_flags(self):
        """Test qc accepts short flags."""
        result = runner.invoke(app, ["qc", "/input", "-t", "4"])
        # Should succeed or fail gracefully, not due to arg parsing
        assert result.exit_code in (0, 1)

    def test_collect_accepts_short_flags(self):
        """Test collect accepts short flags with R1 and R2 files."""
        result = runner.invoke(
            app, ["collect", "/input_R1.fastq.gz", "/input_R2.fastq.gz", "-t", "4"]
        )
        # Should succeed or fail gracefully, not due to arg parsing (exit code 1 is file not found, which is ok)
        assert result.exit_code in (0, 1)

    def test_summary_runs_and_produces_output(self):
        """Test summary command runs and produces output."""
        result = runner.invoke(app, ["summary", "/input"])
        # Should handle missing input gracefully
        assert len(result.output) > 0
