from bactscout.long.main import locate_long_read_files


def test_locate_long_read_files_uses_extension_only(tmp_path):
    (tmp_path / "isolate_1.fastq.gz").touch()
    (tmp_path / "isolate_R1.fastq.gz").touch()

    read_files, duplicates = locate_long_read_files(tmp_path)

    assert read_files["isolate_1"] == str(tmp_path / "isolate_1.fastq.gz")
    assert read_files["isolate_R1"] == str(tmp_path / "isolate_R1.fastq.gz")
    assert duplicates == {}


def test_locate_long_read_files_detects_duplicate_sample_names(tmp_path):
    (tmp_path / "sample.fastq.gz").touch()
    (tmp_path / "sample.fq.gz").touch()

    read_files, duplicates = locate_long_read_files(tmp_path)

    assert "sample" in read_files
    assert "sample" in duplicates
    assert len(duplicates["sample"]) == 2