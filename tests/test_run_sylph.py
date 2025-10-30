from unittest.mock import patch

from bactscout.software.run_sylph import get_command


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
