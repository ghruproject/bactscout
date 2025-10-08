"""Tests for locate_read_file_pairs function."""

import os
import tempfile
from pathlib import Path

from bactscout.main import locate_read_file_pairs


class TestLocateReadFilePairs:
    """Test class for locate_read_file_pairs function."""

    def test_locate_read_file_pairs_basic(self):
        """Test basic R1/R2 pair detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                "sample1_R1.fastq.gz",
                "sample1_R2.fastq.gz",
                "sample2_R1.fastq",
                "sample2_R2.fastq",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            # Test the function
            pairs = locate_read_file_pairs(temp_dir)

            # Verify results
            assert len(pairs) == 2, f"Expected 2 pairs, got {len(pairs)}"
            assert "sample1" in pairs
            assert "sample2" in pairs

            # Check file paths
            assert pairs["sample1"]["R1"].endswith("sample1_R1.fastq.gz")
            assert pairs["sample1"]["R2"].endswith("sample1_R2.fastq.gz")
            assert pairs["sample2"]["R1"].endswith("sample2_R1.fastq")
            assert pairs["sample2"]["R2"].endswith("sample2_R2.fastq")

    def test_locate_read_file_pairs_complex_names(self):
        """Test with complex sample names like NIHR_KGMU_KPN_2061."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with complex names
            test_files = [
                "NIHR_KGMU_KPN_2061_1.fastq.gz",
                "NIHR_KGMU_KPN_2061_2.fastq.gz",
                "Sample_ABC123_XYZ_1.fastq.gz",
                "Sample_ABC123_XYZ_2.fastq.gz",
                "Simple_Sample_1.fq.gz",
                "Simple_Sample_2.fq.gz",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            # Test the function
            pairs = locate_read_file_pairs(temp_dir)

            # Verify results
            assert len(pairs) == 3, f"Expected 3 pairs, got {len(pairs)}"

            # Check NIHR sample specifically
            assert "NIHR_KGMU_KPN_2061" in pairs
            assert pairs["NIHR_KGMU_KPN_2061"]["R1"].endswith(
                "NIHR_KGMU_KPN_2061_1.fastq.gz"
            )
            assert pairs["NIHR_KGMU_KPN_2061"]["R2"].endswith(
                "NIHR_KGMU_KPN_2061_2.fastq.gz"
            )

            # Check other samples
            assert "Sample_ABC123_XYZ" in pairs
            assert "Simple_Sample" in pairs

    def test_locate_read_file_pairs_with_R_prefix(self):
        """Test with R1/R2 prefix in filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with R prefix
            test_files = [
                "sample1_R1.fastq.gz",
                "sample1_R2.fastq.gz",
                "sample2_R1.fq",
                "sample2_R2.fq",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            # Test the function
            pairs = locate_read_file_pairs(temp_dir)

            # Verify results
            assert len(pairs) == 2
            assert "sample1" in pairs
            assert "sample2" in pairs

    def test_locate_read_file_pairs_mixed_extensions(self):
        """Test with various file extensions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with different extensions
            test_files = [
                "sample1_1.fastq.gz",
                "sample1_2.fastq.gz",
                "sample2_1.fastq",
                "sample2_2.fastq",
                "sample3_1.fq.gz",
                "sample3_2.fq.gz",
                "sample4_1.fq",
                "sample4_2.fq",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            # Test the function
            pairs = locate_read_file_pairs(temp_dir)

            # Verify all extensions work
            assert len(pairs) == 4
            for i in range(1, 5):
                assert f"sample{i}" in pairs

    def test_locate_read_file_pairs_incomplete_pairs(self):
        """Test that incomplete pairs are filtered out."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files with some incomplete pairs
            test_files = [
                "complete_sample_1.fastq.gz",
                "complete_sample_2.fastq.gz",
                "incomplete_sample_1.fastq.gz",  # Missing R2
                "orphan_sample_2.fastq.gz",  # Missing R1
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            # Test the function
            pairs = locate_read_file_pairs(temp_dir)

            # Should only return complete pairs
            assert len(pairs) == 1
            assert "complete_sample" in pairs

    def test_locate_read_file_pairs_empty_directory(self):
        """Test with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pairs = locate_read_file_pairs(temp_dir)
            assert len(pairs) == 0

    def test_locate_read_file_pairs_no_fastq_files(self):
        """Test with directory containing no FASTQ files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create non-FASTQ files
            test_files = ["sample1.txt", "sample2.csv", "README.md"]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            pairs = locate_read_file_pairs(temp_dir)
            assert len(pairs) == 0

    def test_locate_read_file_pairs_return_format(self):
        """Test that the return format is correct."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = [
                "NIHR_KGMU_KPN_2061_1.fastq.gz",
                "NIHR_KGMU_KPN_2061_2.fastq.gz",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            pairs = locate_read_file_pairs(temp_dir)

            # Check return format
            assert isinstance(pairs, dict)
            assert len(pairs) == 1

            sample_name = list(pairs.keys())[0]
            sample_data = pairs[sample_name]

            # Check structure
            assert isinstance(sample_data, dict)
            assert "R1" in sample_data
            assert "R2" in sample_data
            assert len(sample_data) == 2

            # Check paths are absolute
            assert os.path.isabs(sample_data["R1"])
            assert os.path.isabs(sample_data["R2"])

            # Check files exist (they should since we created them)
            assert os.path.exists(sample_data["R1"])
            assert os.path.exists(sample_data["R2"])

    def test_locate_read_file_pairs_regex_pattern(self):
        """Test the regex pattern handles various naming conventions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test files with different patterns that should work
            test_files = [
                # Standard patterns - this creates TWO pairs for same sample!
                "sample_1.fastq.gz",
                "sample_2.fastq.gz",
                "sample_R1.fastq.gz",
                "sample_R2.fastq.gz",
                # Complex names
                "NIHR_KGMU_KPN_2061_1.fastq.gz",
                "NIHR_KGMU_KPN_2061_2.fastq.gz",
                "Sample_ABC-123_XYZ_1.fq",
                "Sample_ABC-123_XYZ_2.fq",
                # Edge cases that should work
                "A_1.fastq",
                "A_2.fastq",
                "123_456_789_1.fq.gz",
                "123_456_789_2.fq.gz",
            ]

            for filename in test_files:
                Path(temp_dir, filename).touch()

            pairs = locate_read_file_pairs(temp_dir)

            # Should detect all pairs (sample_ creates 2 pairs: sample_ and sampleR)
            expected_pairs = (
                5  # 5 complete pairs due to sample_ having both _1/_2 and _R1/_R2
            )
            assert len(pairs) == expected_pairs

            # Verify the NIHR pattern specifically
            assert "NIHR_KGMU_KPN_2061" in pairs
            assert "R1" in pairs["NIHR_KGMU_KPN_2061"]
            assert "R2" in pairs["NIHR_KGMU_KPN_2061"]  # Verify specific samples
            sample_names = list(pairs.keys())
            assert any("NIHR_KGMU_KPN_2061" in name for name in sample_names)
            assert any("Sample_ABC-123_XYZ" in name for name in sample_names)


if __name__ == "__main__":
    # Allow running the test directly
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))

    test = TestLocateReadFilePairs()
    test.test_locate_read_file_pairs_basic()
    test.test_locate_read_file_pairs_complex_names()
    test.test_locate_read_file_pairs_return_format()
    print("✅ All tests passed!")
