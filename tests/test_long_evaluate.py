from bactscout.long.evaluate import evaluate_long


def test_evaluate_long_pass_case():
    cfg = {
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
    }
    stats = {"median_q": 17, "n50": 12000}
    result = evaluate_long(stats, 45.0, 40.0, 5.0, cfg, "ont_r10")

    assert result["status"] == "PASSED"
    assert result["flag_quality"] == "PASSED"
    assert result["flag_coverage"] == "PASSED"


def test_evaluate_long_warns_when_genome_size_missing():
    cfg = {
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
    }
    stats = {"median_q": 17, "n50": 12000}
    result = evaluate_long(stats, None, 38.0, 5.0, cfg, "ont_r10")

    assert result["status"] == "WARNING"
    assert result["flag_coverage_calc"] == "WARNING"
    assert "Expected genome size unavailable" in result["reasons"]


def test_evaluate_long_fails_when_no_coverage_can_be_estimated():
    cfg = {
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
    }
    stats = {
        "read_count": 38,
        "total_bases": 212799,
        "n50": 13120,
        "mean_len": 5599,
        "median_len": 3557,
        "mean_q": 16.242884,
        "median_q": 17.204168,
    }

    result = evaluate_long(stats, None, None, None, cfg, "ont_r10")

    assert result["status"] == "FAILED"
    assert result["flag_coverage"] == "FAILED"
    assert result["flag_coverage_sylph"] == "FAILED"
    assert "No coverage estimate available" in result["reasons"]


def test_evaluate_long_fails_on_low_contamination_purity():
    cfg = {
        "platforms": {"ont_r10": {"q_warn": 15, "q_fail": 12}},
        "n50_warn": 8000,
        "n50_fail": 4000,
        "coverage_warn_threshold": 30,
        "coverage_fail_threshold": 20,
        "contamination_warn_threshold": 10,
        "contamination_fail_threshold": 20,
    }
    stats = {"median_q": 17, "n50": 12000}
    result = evaluate_long(stats, 45.0, 40.0, 25.0, cfg, "ont_r10")

    assert result["status"] == "FAILED"
    assert result["flag_contam"] == "FAILED"
