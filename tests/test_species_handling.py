from bactscout.thread import (
    handle_species_coverage,
)


def test_handle_species_coverage_various_cases():
    cfg = {}

    # No species detected
    final = {}
    updated, species = handle_species_coverage([], final.copy(), cfg)
    assert species == []
    assert updated["coverage_status"] == "FAILED"
    assert updated["species_status"] == "FAILED"

    # Single species, high coverage, high purity -> PASSED for coverage and contamination
    sp = [("Escherichia coli", 95.0, 40.0)]
    final = {}
    updated, species = handle_species_coverage(sp, final.copy(), cfg)
    assert species == ["Escherichia coli"]
    assert updated["coverage_status"] == "PASSED"
    assert updated["contamination_status"] == "PASSED"

    # Single species, moderate coverage -> WARNING coverage
    sp = [("SppA", 92.0, 25.0)]
    final = {}
    updated, species = handle_species_coverage(sp, final.copy(), cfg)
    assert updated["coverage_status"] == "WARNING"
    assert updated["contamination_status"] == "PASSED"

    # Multiple species -> species_status WARNING and possible contamination FAIL
    sp = [("A", 85.0, 10.0), ("B", 10.0, 1.0)]
    final = {}
    updated, species = handle_species_coverage(sp, final.copy(), cfg)
    assert updated["species_status"] == "WARNING"
    # Contamination should be evaluated and likely FAILED given low top purity (85%)
    assert updated["contamination_status"] == "FAILED"
