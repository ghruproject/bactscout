"""Nanoq wrapper for long-read summary statistics."""

import json
import os
import shutil
import subprocess


def get_command():
    """Get the nanoq command, trying PATH first then pixi."""
    cmd = shutil.which("nanoq")
    if cmd is not None:
        return [cmd]
    if shutil.which("pixi"):
        return ["pixi", "run", "--", "nanoq"]
    return ["nanoq"]


def run_nanoq(reads_file, sample_dir, threads=1):
    """Run nanoq and parse summary statistics from its JSON report."""
    del threads
    if not os.path.exists(sample_dir):
        os.makedirs(sample_dir, exist_ok=True)

    out = os.path.join(sample_dir, "nanoq_stats.json")
    log_file = os.path.join(sample_dir, "nanoq.log")
    full_cmd = get_command() + ["-i", reads_file, "-s", "-j", "-r", out]

    with open(log_file, "w", encoding="utf-8") as log:
        subprocess.run(full_cmd, stdout=log, stderr=subprocess.STDOUT, check=True, text=True)

    with open(out, encoding="utf-8") as f:
        data = json.load(f)

    return {
        "read_count": data.get("reads", 0),
        "total_bases": data.get("bases", 0),
        "n50": data.get("n50", 0),
        "mean_len": data.get("mean_length", 0),
        "median_len": data.get("median_length", 0),
        "mean_q": data.get("mean_quality"),
        "median_q": data.get("median_quality"),
    }
