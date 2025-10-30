"""Tests for FastP command resolution."""

import subprocess
from unittest.mock import MagicMock, mock_open, patch

from bactscout.software.run_fastp import get_command, run_command


def test_get_command_fastp_in_path():
    """Test get_command when fastp is in PATH."""
    with patch("shutil.which") as mock_which:
        # Mock fastp found in PATH
        mock_which.return_value = "/usr/bin/fastp"

        result = get_command()

        assert result == ["/usr/bin/fastp"]
        mock_which.assert_called_once_with("fastp")


def test_get_command_fastp_not_in_path_pixi_available():
    """Test get_command when fastp not in PATH but pixi is available."""
    with patch("shutil.which") as mock_which:
        # Mock fastp not found, but pixi is found
        def which_side_effect(cmd):
            if cmd == "fastp":
                return None
            elif cmd == "pixi":
                return "/usr/local/bin/pixi"
            return None

        mock_which.side_effect = which_side_effect

        result = get_command()

        assert result == ["pixi", "run", "--", "fastp"]
        assert mock_which.call_count == 2


def test_get_command_fallback():
    """Test get_command fallback when neither fastp nor pixi found."""
    with patch("shutil.which") as mock_which:
        # Mock both fastp and pixi not found
        mock_which.return_value = None

        result = get_command()

        assert result == ["fastp"]
        assert mock_which.call_count == 2


def test_get_command_returns_string_or_list():
    """Test that get_command always returns a list."""
    result = get_command()

    assert isinstance(result, list)
    assert len(result) > 0
    assert all(isinstance(item, str) for item in result)


def test_run_command_success(tmp_path):
    """Test run_command successfully runs fastp and returns results."""
    # Create test FASTQ files
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"

    # Mock subprocess.run to avoid actually running fastp
    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_fastp.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open()):
        mock_get_cmd.return_value = ["fastp"]
        mock_run.return_value = MagicMock(returncode=0)

        result = run_command(
            str(r1), str(r2), str(output_dir), message=False, threads=4
        )

        # Check result structure
        assert result["status"] == "success"
        assert result["sample"] == "sample"
        assert "json_report" in result
        assert "html_report" in result
        assert "log_file" in result

        # Verify subprocess.run was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args  #
        print(call_args)
        assert "--thread" in call_args[0][0]
        assert "4" in call_args[0][0]


def test_run_command_failure(tmp_path):
    """Test run_command handles fastp failure."""
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_fastp.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open()):
        mock_get_cmd.return_value = ["fastp"]
        # Simulate CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(1, "fastp", stderr="Error")

        result = run_command(str(r1), str(r2), str(output_dir))

        assert result["status"] == "failed"
        assert "error" in result
        assert "sample" in result
