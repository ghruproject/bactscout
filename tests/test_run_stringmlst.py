"""Tests for StringMLST command resolution and execution."""

import subprocess
from unittest.mock import MagicMock, mock_open, patch

from bactscout.software.run_stringmlst import get_command, run_command


def test_get_command_stringmlst_in_path():
    """Test get_command when stringMLST.py is found in PATH."""
    with patch("shutil.which") as mock_which:
        # Mock stringMLST.py found in PATH
        mock_which.return_value = "/usr/bin/stringMLST.py"

        result = get_command()

        assert result == ["/usr/bin/stringMLST.py"]
        mock_which.assert_called_once_with("stringMLST.py")


def test_get_command_stringmlst_not_in_path():
    """Test get_command when stringMLST.py not in PATH - falls back to pixi."""
    with patch("shutil.which") as mock_which:
        # Mock stringMLST.py not found
        mock_which.return_value = None

        result = get_command()

        assert result == ["pixi", "run", "--", "stringMLST.py"]
        mock_which.assert_called_once_with("stringMLST.py")


def test_run_command_success(tmp_path):
    """Test run_command successfully runs stringMLST and returns results."""
    # Create test FASTQ files
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"
    species_db = tmp_path / "species_db"
    species_db.mkdir()

    # Create mock MLST output
    mlst_output = "Sample\tST\tclonal_complex\naroE\tglpF\tgmk\tgtr\n"
    mlst_output += "sample\t123\tCC123\t1\t2\t3\t4\n"

    # Mock subprocess.run and file operations
    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_stringmlst.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open(read_data=mlst_output)):
        mock_get_cmd.return_value = ["stringMLST.py"]
        mock_run.return_value = MagicMock(returncode=0)

        # Mock os.path.exists to return True for output file
        with patch("os.path.exists", return_value=True):
            result = run_command(
                str(r1),
                str(r2),
                str(species_db),
                str(output_dir),
                message=False,
            )

        # Check result structure
        assert result["sample_name"] == "sample"
        assert "stringmlst_results" in result
        assert "output_dir" in result

        # Verify subprocess.run was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "--predict" in call_args


def test_run_command_failure(tmp_path):
    """Test run_command handles stringMLST failure."""
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"
    species_db = tmp_path / "species_db"
    species_db.mkdir()

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_stringmlst.get_command"
    ) as mock_get_cmd:
        mock_get_cmd.return_value = ["stringMLST.py"]
        # Simulate CalledProcessError
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "stringMLST.py", stderr="Error"
        )

        result = run_command(str(r1), str(r2), str(species_db), str(output_dir))

        assert "stringmlst_results" in result
        assert "error" in result["stringmlst_results"]
        assert "StringMLST command failed" in result["stringmlst_results"]["error"]


def test_run_command_no_output_file(tmp_path):
    """Test run_command when output file is not created."""
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"
    species_db = tmp_path / "species_db"
    species_db.mkdir()

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_stringmlst.get_command"
    ) as mock_get_cmd, patch("os.path.exists", return_value=False):
        mock_get_cmd.return_value = ["stringMLST.py"]
        mock_run.return_value = MagicMock(returncode=0)

        result = run_command(str(r1), str(r2), str(species_db), str(output_dir))

        assert "stringmlst_results" in result
        assert "error" in result["stringmlst_results"]
        assert "did not create output file" in result["stringmlst_results"]["error"]


def test_run_command_with_message_enabled(tmp_path, capsys):
    """Test run_command with message output enabled."""
    r1 = tmp_path / "sample_R1.fastq.gz"
    r2 = tmp_path / "sample_R2.fastq.gz"
    r1.touch()
    r2.touch()

    output_dir = tmp_path / "output"
    species_db = tmp_path / "species_db"
    species_db.mkdir()

    mlst_output = "Sample\tST\nsample\t789\n"

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_stringmlst.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open(read_data=mlst_output)), patch(
        "os.path.exists", return_value=True
    ):
        mock_get_cmd.return_value = ["stringMLST.py"]
        mock_run.return_value = MagicMock(returncode=0)

        result = run_command(
            str(r1), str(r2), str(species_db), str(output_dir), message=True
        )

        # Check that messages were printed
        captured = capsys.readouterr()
        assert "Running StringMLST" in captured.out
        assert "StringMLST completed successfully" in captured.out

        # Verify result is still correct
        assert result["sample_name"] == "sample"
        assert "stringmlst_results" in result
