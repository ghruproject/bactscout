"""Long-read QC evaluation helpers."""


def _band(value, warn, fail, direction="min"):
    if value is None:
        return "WARNING"
    if direction == "min":
        if value < fail:
            return "FAILED"
        if value < warn:
            return "WARNING"
    else:
        if value > fail:
            return "FAILED"
        if value > warn:
            return "WARNING"
    return "PASSED"


def evaluate_long(stats, cov_calc, cov_sylph, contamination, cfg, platform):
    """Evaluate long-read QC metrics and roll up a final status."""
    platform_cfg = cfg["platforms"][platform]
    reasons = []

    flag_quality = _band(
        stats.get("median_q"), platform_cfg["q_warn"], platform_cfg["q_fail"], "min"
    )
    flag_n50 = _band(stats.get("n50"), cfg["n50_warn"], cfg["n50_fail"], "min")
    flag_contam = _band(
        contamination,
        cfg["contamination_warn_threshold"],
        cfg["contamination_fail_threshold"],
        "max",
    )
    flag_coverage_sylph = _band(
        cov_sylph,
        cfg["coverage_warn_threshold"],
        cfg["coverage_fail_threshold"],
        "min",
    )

    if cov_calc is None:
        flag_coverage_calc = "WARNING"
        reasons.append("Expected genome size unavailable; using Sylph coverage only")
        flag_coverage = "FAILED" if flag_coverage_sylph == "FAILED" else "WARNING"
    else:
        flag_coverage_calc = _band(
            cov_calc,
            cfg["coverage_warn_threshold"],
            cfg["coverage_fail_threshold"],
            "min",
        )
        coverage_flags = {flag_coverage_sylph, flag_coverage_calc}
        if coverage_flags == {"PASSED"}:
            flag_coverage = "PASSED"
        elif "FAILED" in coverage_flags and len(coverage_flags) == 1:
            flag_coverage = "FAILED"
        elif flag_coverage_sylph == "FAILED" and flag_coverage_calc == "FAILED":
            flag_coverage = "FAILED"
        else:
            flag_coverage = "WARNING"

    if flag_quality == "WARNING":
        reasons.append("Median read quality below recommended threshold")
    elif flag_quality == "FAILED":
        reasons.append("Median read quality below minimum threshold")

    if flag_n50 == "WARNING":
        reasons.append("Read N50 below recommended threshold")
    elif flag_n50 == "FAILED":
        reasons.append("Read N50 below minimum threshold")

    if flag_contam == "WARNING":
        reasons.append("Secondary taxa abundance above warning threshold")
    elif flag_contam == "FAILED":
        reasons.append("Secondary taxa abundance above failure threshold")

    if cov_calc is not None:
        if flag_coverage == "WARNING":
            reasons.append("Coverage below recommended threshold")
        elif flag_coverage == "FAILED":
            reasons.append("Coverage below minimum threshold")
    elif flag_coverage_sylph == "FAILED":
        reasons.append("Sylph coverage below minimum threshold")

    critical_flags = [flag_quality, flag_n50, flag_coverage, flag_contam]
    if "FAILED" in critical_flags:
        status = "FAILED"
    elif "WARNING" in critical_flags:
        status = "WARNING"
    else:
        status = "PASSED"

    return {
        "status": status,
        "flag_quality": flag_quality,
        "flag_n50": flag_n50,
        "flag_coverage": flag_coverage,
        "flag_contam": flag_contam,
        "flag_coverage_calc": flag_coverage_calc,
        "flag_coverage_sylph": flag_coverage_sylph,
        "reasons": "; ".join(reasons),
    }
