"""Tests for BactScout main functionality."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from bactscout.main import main


class TestBactScoutMain:
    """Test class for BactScout main function."""

    def test_main_with_sample_data(self):
        """Test main function with sample_data directory."""
        # Get paths
        project_root = Path(__file__).parent.parent
        input_dir = project_root / "sample_data"
        config_file = project_root / "bactscout_config.yml"

        # Create temporary output directory
        with tempfile.TemporaryDirectory() as temp_output:
            output_dir = temp_output
            max_threads = 2  # Use fewer threads for testing

            # Verify input directory exists and has FASTQ files
            assert input_dir.exists(), f"Sample data directory not found: {input_dir}"
            fastq_files = list(input_dir.glob("*.fastq.gz"))
            assert len(fastq_files) > 0, f"No FASTQ files found in {input_dir}"

            # Verify config file exists
            assert config_file.exists(), f"Config file not found: {config_file}"

            # Run the main function
            try:
                main(
                    input_dir=str(input_dir),
                    output_dir=output_dir,
                    max_threads=max_threads,
                    config_file=str(config_file),
                )

                # Verify output directory was created and contains results
                output_path = Path(output_dir)
                assert output_path.exists(), "Output directory was not created"

                # Check for sample output directories
                sample_dirs = [d for d in output_path.iterdir() if d.is_dir()]
                assert len(sample_dirs) > 0, "No sample output directories found"

                # Check for expected output files in at least one sample directory
                sample_dir = sample_dirs[0]
                expected_files = ["sylph_report.txt", "*_summary.csv", "*.fastp.json"]

                for pattern in expected_files:
                    files = list(sample_dir.glob(pattern))
                    assert len(files) > 0, (
                        f"Expected file pattern {pattern} not found in {sample_dir}"
                    )

                print(f"✅ Test passed! Output created in {output_dir}")
                print(f"   Found {len(sample_dirs)} sample(s) processed")
                print(f"   Sample directory: {sample_dir}")

            except (
                RuntimeError,
                FileNotFoundError,
                subprocess.CalledProcessError,
            ) as e:
                pytest.fail(f"Main function failed with error: {e}")

    def test_main_function_parameters(self):
        """Test that main function accepts the expected parameters."""
        # This is a basic test to ensure the function signature is correct
        import inspect

        sig = inspect.signature(main)
        expected_params = ["input_dir", "output_dir", "max_threads", "config_file"]

        actual_params = list(sig.parameters.keys())

        for param in expected_params:
            assert param in actual_params, (
                f"Parameter '{param}' not found in main function signature"
            )

        print(f"✅ Main function has expected parameters: {actual_params}")


if __name__ == "__main__":
    # Allow running the test directly
    import subprocess
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))

    test = TestBactScoutMain()
    test.test_main_function_parameters()
    test.test_main_with_sample_data()
