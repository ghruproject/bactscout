"""Tests for genome_download module."""

from unittest.mock import MagicMock, mock_open, patch

import pytest

from bactscout.genome_download import (
    build_ncbi_url,
    download_genome_from_ncbi,
    ensure_genome_downloaded,
    extract_accession_from_path,
    get_cached_genome_path,
)


def test_extract_accession_from_path_full_path():
    """Test extracting accession from full GTDB path."""
    path = (
        "gtdb_genomes_reps_r226/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz"
    )
    result = extract_accession_from_path(path)
    assert result == "GCF_000742135.1"


def test_extract_accession_from_path_filename_only():
    """Test extracting accession from filename only."""
    path = "GCF_000742135.1_genomic.fna.gz"
    result = extract_accession_from_path(path)
    assert result == "GCF_000742135.1"


def test_extract_accession_from_path_gca():
    """Test extracting GCA accession."""
    path = "/path/to/GCA_000005845.2_genomic.fna.gz"
    result = extract_accession_from_path(path)
    assert result == "GCA_000005845.2"


def test_extract_accession_from_path_no_match():
    """Test extraction returns empty string when no accession found."""
    path = "some_random_file.fna.gz"
    result = extract_accession_from_path(path)
    assert result == ""


def test_extract_accession_from_path_empty_string():
    """Test extraction with empty string."""
    result = extract_accession_from_path("")
    assert result == ""


def test_build_ncbi_url_gcf():
    """Test building NCBI URL for GCF accession."""
    accession = "GCF_000742135.1"
    expected = "ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/742/135/GCF_000742135.1/GCF_000742135.1_genomic.fna.gz"
    result = build_ncbi_url(accession)
    assert result == expected


def test_build_ncbi_url_gca():
    """Test building NCBI URL for GCA accession."""
    accession = "GCA_000005845.2"
    expected = "ftp://ftp.ncbi.nlm.nih.gov/genomes/all/GCA/000/005/845/GCA_000005845.2/GCA_000005845.2_genomic.fna.gz"
    result = build_ncbi_url(accession)
    assert result == expected


def test_build_ncbi_url_invalid_accession():
    """Test building URL with invalid accession returns empty string."""
    result = build_ncbi_url("invalid")
    assert result == ""


def test_build_ncbi_url_empty_string():
    """Test building URL with empty string."""
    result = build_ncbi_url("")
    assert result == ""


def test_get_cached_genome_path():
    """Test generating cached genome path."""
    accession = "GCF_000742135.1"
    cache_dir = "/path/to/cache"
    expected = "/path/to/cache/GCF_000742135.1_genomic.fna.gz"
    result = get_cached_genome_path(accession, cache_dir)
    assert result == expected


@patch("bactscout.genome_download.requests.get")
@patch("bactscout.genome_download.Path")
@patch("builtins.open", new_callable=mock_open)
def test_download_genome_from_ncbi_success(mock_file, mock_path, mock_get):
    """Test successful genome download from NCBI."""
    # Mock successful HTTP response
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
    mock_get.return_value = mock_response

    # Mock Path operations
    mock_path_instance = MagicMock()
    mock_path.return_value = mock_path_instance

    accession = "GCF_000742135.1"
    destination = "/tmp/GCF_000742135.1_genomic.fna.gz"

    result = download_genome_from_ncbi(accession, destination)

    assert result is True
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_file.assert_called_once_with(destination, "wb")


@patch("bactscout.genome_download.requests.get")
def test_download_genome_from_ncbi_http_error(mock_get):
    """Test download fails with HTTP error."""
    import requests

    # Mock HTTP error
    mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

    accession = "GCF_000742135.1"
    destination = "/tmp/GCF_000742135.1_genomic.fna.gz"

    result = download_genome_from_ncbi(accession, destination)

    assert result is False


@patch("bactscout.genome_download.requests.get")
def test_download_genome_from_ncbi_timeout(mock_get):
    """Test download fails with timeout."""
    import requests

    # Mock timeout error
    mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

    accession = "GCF_000742135.1"
    destination = "/tmp/GCF_000742135.1_genomic.fna.gz"

    result = download_genome_from_ncbi(accession, destination)

    assert result is False


@patch("bactscout.genome_download.build_ncbi_url")
def test_download_genome_from_ncbi_invalid_accession(mock_build_url):
    """Test download fails with invalid accession."""
    # Mock empty URL (invalid accession)
    mock_build_url.return_value = ""

    accession = "invalid"
    destination = "/tmp/invalid.fna.gz"

    result = download_genome_from_ncbi(accession, destination)

    assert result is False


@patch("bactscout.genome_download.os.path.exists")
@patch("bactscout.genome_download.download_genome_from_ncbi")
def test_ensure_genome_downloaded_already_cached(mock_download, mock_exists):
    """Test ensure_genome_downloaded uses cached file when available."""
    # Mock file already exists
    mock_exists.return_value = True

    accession = "GCF_000742135.1"
    cache_dir = "/tmp/cache"

    result = ensure_genome_downloaded(accession, cache_dir)

    # Should not download if cached
    mock_download.assert_not_called()
    assert result == "/tmp/cache/GCF_000742135.1_genomic.fna.gz"


@patch("bactscout.genome_download.os.path.exists")
@patch("bactscout.genome_download.download_genome_from_ncbi")
def test_ensure_genome_downloaded_not_cached(mock_download, mock_exists):
    """Test ensure_genome_downloaded downloads when not cached."""
    # Mock file doesn't exist
    mock_exists.return_value = False
    # Mock successful download
    mock_download.return_value = True

    accession = "GCF_000742135.1"
    cache_dir = "/tmp/cache"
    expected_path = "/tmp/cache/GCF_000742135.1_genomic.fna.gz"

    result = ensure_genome_downloaded(accession, cache_dir)

    # Should download if not cached
    mock_download.assert_called_once_with(accession, expected_path)
    assert result == expected_path


@patch("bactscout.genome_download.os.path.exists")
@patch("bactscout.genome_download.download_genome_from_ncbi")
def test_ensure_genome_downloaded_force_download(mock_download, mock_exists):
    """Test ensure_genome_downloaded with force_download=True."""
    # Mock file exists but force download
    mock_exists.return_value = True
    mock_download.return_value = True

    accession = "GCF_000742135.1"
    cache_dir = "/tmp/cache"
    expected_path = "/tmp/cache/GCF_000742135.1_genomic.fna.gz"

    result = ensure_genome_downloaded(accession, cache_dir, force_download=True)

    # Should download even if cached
    mock_download.assert_called_once_with(accession, expected_path)
    assert result == expected_path


@patch("bactscout.genome_download.os.path.exists")
@patch("bactscout.genome_download.download_genome_from_ncbi")
def test_ensure_genome_downloaded_download_fails(mock_download, mock_exists):
    """Test ensure_genome_downloaded returns empty string on download failure."""
    # Mock file doesn't exist
    mock_exists.return_value = False
    # Mock download failure
    mock_download.return_value = False

    accession = "GCF_000742135.1"
    cache_dir = "/tmp/cache"

    result = ensure_genome_downloaded(accession, cache_dir)

    assert result == ""


@pytest.mark.slow
@pytest.mark.integration
def test_extract_accession_integration():
    """Integration test: Extract accession from real-world path patterns."""
    test_cases = [
        (
            "gtdb_genomes_reps_r226/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz",
            "GCF_000742135.1",
        ),
        ("GCA_000005845.2_genomic.fna.gz", "GCA_000005845.2"),
        ("/absolute/path/to/GCF_123456789.1_genomic.fna.gz", "GCF_123456789.1"),
        ("./relative/GCA_987654321.3_genomic.fna.gz", "GCA_987654321.3"),
    ]

    for path, expected_accession in test_cases:
        result = extract_accession_from_path(path)
        assert (
            result == expected_accession
        ), f"Failed for path: {path}, got {result}, expected {expected_accession}"
