"""Long-read preflight checks."""

import os
import shutil
import subprocess

from bactscout.preflight import check_system_resources, get_sylph_db
from bactscout.util import print_header, print_message


def preflight_check_long(skip_preflight: bool, config_dict: dict) -> bool:
    """Run long-read-specific preflight checks."""
    if skip_preflight:
        print_message("Skipping preflight checks", "warning")
        return True

    print_header("Long-Read Preflight Checks")
    return (
        check_system_resources(config_dict)
        and check_software_long(config_dict)
        and check_databases_long(config_dict)
    )


def check_databases_long(config_dict) -> bool:
    """Verify only the databases required for long-read QC."""
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
    if not os.path.exists(sylph_db_file):
        print_message(f"Sylph database missing: {sylph_db_file}", "error")
        return False
    print_message("Long-read databases validated successfully.", "info")
    return True


def check_software_long(config_dict) -> bool:
    """Verify long-read runtime tools are available."""
    del config_dict
    cmds = {
        "nanoq": [shutil.which("nanoq"), "--version"],
        "sylph": [shutil.which("sylph"), "--version"],
    }
    for tool, cmd in cmds.items():
        if cmd[0] is None:
            cmds[tool] = ["pixi", "run", "--", tool] + cmd[1:]

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
            line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "ok"
            print_message(f"{tool} is available: {line}", "info")
        except (OSError, subprocess.SubprocessError) as e:
            print_message(f"Error checking {tool}: {e}", "error")
            passed = False
    return passed
