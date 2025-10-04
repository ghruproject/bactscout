#!/usr/bin/env python3
"""
GHRU Read QC Pipeline - Preflight Checks Module

This module contains runtime validation methods that verify all required components
are available and properly configured before pipeline execution begins.

Key Validation Areas:
    - Database Availability: Checks for required Sylph and MLST databases
    - Tool Accessibility: Verifies containerization platform or conda environment tools
    - System Resources: Validates sufficient compute resources are available
    - Input Validation: Ensures input data formats and structures are correct
    - Output Permissions: Confirms write access to output directories

Author: Nabil-Fareed Alikhan
License: See repository LICENSE file
"""

import os
import platform
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict

import psutil
import yaml  # Ensure PyYAML is installed in the environment

from bactscout.software.run_stringmlst import get_command as get_mlst_command
from bactscout.util import print_header, print_message


def load_config(config_path) -> dict[str, str]:
    """
    Load configuration from YAML file.

    """
    # Load yaml and parse configurations

    with open(config_path, encoding="utf-8") as f:
        config_dict = yaml.safe_load(f)
    return config_dict


def get_sylph_db(
    sylph_db_file,
    sylph_db_url,
) -> None:
    if not os.path.exists(sylph_db_file):
        try:
            print_message(f"Downloading Sylph database from {sylph_db_url}...", "info")
            urllib.request.urlretrieve(sylph_db_url, sylph_db_file)
            print_message("Sylph database downloaded successfully.", "info")
        except Exception as e:
            print_message(f"Failed to download Sylph database: {e}", "error")
    else:
        print_message("Sylph database found.", "info")


def check_databases(config_dict) -> bool:
    """
    Verify required databases exist and are accessible.

    Returns:
        bool: True if all specified databases are valid
    """
    print_message("Checking required databases...", "info")
    db_path = config_dict.get("bactscout_dbs_path", "")
    os.makedirs(db_path, exist_ok=True)
    print_message("Checking Sylph...", "info")
    sylph_db_url = config_dict.get(
        "sylph_db_url",
        "http://faust.compbio.cs.cmu.edu/sylph-stuff/gtdb-r226-c1000-dbv1.syldb",
    )
    sylph_db_file = os.path.join(
        db_path, config_dict.get("sylph_db", "gtdb-r226-c1000-dbv1.syldb")
    )
    get_sylph_db(sylph_db_file, sylph_db_url)
    # For each species in mlst_species, check database availability. Otherwise download and format for mlst.
    for species_name, species_db_name in config_dict.get("mlst_species", {}).items():
        if not db_path:
            print_message("MLST database path not specified in configuration.", "error")
            return False
        mlst_files = [f"{species_name}_config.txt", f"{species_name}_profile.txt"]
        files_found = True
        for mlst_file in mlst_files:
            # check if file exists
            full_file_path = os.path.join(db_path, species_name, mlst_file)
            if not os.path.exists(full_file_path):
                files_found = False
        if not files_found:
            print_message(
                f"MLST files for species '{species_name}' not found in {db_path}. Trying to download...",
                "warning",
            )
            species_db_path = os.path.join(os.path.abspath(db_path), species_name)
            species_prefix = os.path.join(
                os.path.abspath(db_path), species_name, species_name
            )
            # remove existing partial db if any
            if os.path.exists(species_db_path):
                shutil.rmtree(species_db_path, ignore_errors=True)
            try:
                mlst_cmd = get_mlst_command()
                subprocess.run(
                    mlst_cmd
                    + [
                        # pixi run stringmlst.py --getMLST --species 'Klebsiella pneumoniae' -P bactscout_dbs/kleb/kleb
                        "--getMLST",
                        "--species",
                        species_db_name,
                        "-P",
                        species_prefix,
                    ],
                    check=True,
                    cwd=db_path,
                )
            except subprocess.CalledProcessError as e:
                print_message(
                    f"Failed to download MLST database for species '{species_name}': {e}",
                    "error",
                )
                return False
        else:
            print_message(
                f"MLST database for species '{species_name}' found in {db_path}.",
                "info",
            )
    print_message("All required databases are validated successfully.", "info")
    return True


def check_system_resources(config_dict) -> bool:
    """
    Assess available system resources (CPU, memory, disk space).

    Returns:
        bool: True if sufficient resources are available
    """
    # Check system resources against config_dict['system_resources']

    required_cpus = config_dict.get("system_resources", {}).get("cpus", 1)
    required_memory = config_dict.get("system_resources", {}).get("memory", "1.GB")

    # Parse memory requirement
    def parse_memory(mem_str):
        units = {"KB": 1 << 10, "MB": 1 << 20, "GB": 1 << 30}
        mem_str = str(mem_str).replace(" ", "").upper()
        for unit in units:
            if mem_str.endswith(unit):
                try:
                    return int(float(mem_str[: -len(unit)]) * units[unit])
                except ValueError:
                    return 0
        try:
            return int(mem_str)
        except ValueError:
            return 0

    required_memory_bytes = parse_memory(required_memory)
    available_cpus = psutil.cpu_count(logical=False) or psutil.cpu_count()
    available_memory_bytes = psutil.virtual_memory().total
    failed = False
    if available_cpus < required_cpus:
        print_message(
            f"Insufficient CPUs: Required {required_cpus}, available {available_cpus}.",
            "error",
        )
        failed = True
    if available_memory_bytes < required_memory_bytes:
        print_message(
            f"Insufficient memory: Required {required_memory_bytes // (1 << 30)} GB, available {available_memory_bytes // (1 << 30)} GB.",
            "error",
        )
        failed = True
    if failed:
        return False
    print_message("System resources validated successfully.", "info")
    return True


def check_software(config_dict) -> bool:
    cmds = {
        "fastp": [shutil.which("fastp"), "--version"],
        "sylph": [shutil.which("sylph"), "--version"],
        "stringmlst.py": [shutil.which("stringmlst.py"), "-v"],
    }
    # If commands are not found, shutil.which returns None, try with pixi run.
    for tool, cmd in cmds.items():
        if cmd[0] is None:
            cmds[tool] = ["pixi", "run", "--"] + [tool] + cmd[1:]

    passed = True
    for tool, cmd in cmds.items():
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                print_message(f"{tool} check failed:\n{result.stdout.strip()}", "error")
                passed = False
            # Some tools print version on first line; fall back to entire output
            line = (
                result.stdout.strip().splitlines()[0] if result.stdout.strip() else "ok"
            )
            print_message(f"{tool} is available: {line}", "info")
        except Exception as e:
            print_message(f"Error checking {tool}: {e}", "error")
            passed = False
    return passed
