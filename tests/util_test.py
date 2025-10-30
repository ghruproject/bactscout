import pytest
import requests


def download_fastq_files(cache_dir, r1_file, r1_url, r2_file, r2_url):
    """
    Download FASTQ files from EBI FTP server if not already cached.

    Returns:
        tuple: (r1_path, r2_path) - Paths to downloaded FASTQ files
    """
    cache_dir.mkdir(exist_ok=True)

    r1_path = cache_dir / r1_file
    r2_path = cache_dir / r2_file

    # Download R1 if not cached
    if not r1_path.exists():
        print(f"Downloading {r1_url}...")
        try:
            response = requests.get(r1_url, timeout=60, stream=True)
            response.raise_for_status()
            with open(r1_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {r1_path}")
        except Exception as e:
            pytest.skip(f"Failed to download R1: {e}")
    else:
        print(f"Using cached {r1_path}")

    # Download R2 if not cached
    if not r2_path.exists():
        print(f"Downloading {r2_url}...")
        try:
            response = requests.get(r2_url, timeout=60, stream=True)
            response.raise_for_status()
            with open(r2_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"Downloaded {r2_path}")
        except Exception as e:
            pytest.skip(f"Failed to download R2: {e}")
    else:
        print(f"Using cached {r2_path}")

    return r1_path, r2_path
