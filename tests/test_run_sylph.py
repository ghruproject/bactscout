import subprocess
from unittest.mock import MagicMock, mock_open, patch

from bactscout.software.run_sylph import get_command, run_command_single


def test_get_command_sylph_in_path():
    """Test get_command when sylph is found in PATH."""
    with patch("shutil.which") as mock_which:
        # Mock sylph found in PATH
        mock_which.return_value = "/usr/bin/sylph"

        result = get_command()

        assert result == ["/usr/bin/sylph"]
        mock_which.assert_called_once_with("sylph")


def test_get_command_sylph_not_in_path():
    """Test get_command when sylph not in PATH - falls back to pixi."""
    with patch("shutil.which") as mock_which:
        # Mock sylph not found
        mock_which.return_value = None

        result = get_command()

        assert result == ["pixi", "run", "--", "sylph"]
        mock_which.assert_called_once_with("sylph")


def test_get_command_returns_list():
    """Test that get_command always returns a list."""
    result = get_command()
    assert isinstance(result, list)
    assert len(result) > 0


def test_run_command_single_success(tmp_path):
    reads = tmp_path / "sample.fastq.gz"
    reads.touch()
    output_dir = tmp_path / "output"
    config = {"bactscout_dbs_path": "/db", "sylph_db": "db.syldb"}

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_sylph.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open()):
        mock_get_cmd.return_value = ["sylph"]
        mock_run.return_value = MagicMock(returncode=0)

        result = run_command_single(str(reads), str(output_dir), config, threads=3)

        assert result["errors"] is None
        mock_run.assert_called_once()
        command = mock_run.call_args[0][0]
        assert command[:3] == ["sylph", "profile", "/db/db.syldb"]
        assert str(reads) in command
        assert "-t" in command
        assert "3" in command


def test_run_command_single_failure(tmp_path):
    reads = tmp_path / "sample.fastq.gz"
    reads.touch()
    output_dir = tmp_path / "output"
    config = {"bactscout_dbs_path": "/db", "sylph_db": "db.syldb"}

    with patch("subprocess.run") as mock_run, patch(
        "bactscout.software.run_sylph.get_command"
    ) as mock_get_cmd, patch("builtins.open", mock_open(read_data="boom")):
        mock_get_cmd.return_value = ["sylph"]
        mock_run.side_effect = subprocess.CalledProcessError(1, ["sylph"])

        result = run_command_single(str(reads), str(output_dir), config, threads=1)

        assert result["errors"] == "boom"
