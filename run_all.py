"""
Run the whole pipeline in order: clean the raw data, build the hourly table,
check it, train the final models, and make a forecast.
Stops at the first failure with a clear message and a non-zero exit code.

Usage:
    python run_all.py              # raw data already in data/raw
    python run_all.py --download   # also download air quality and weather first
"""

import argparse
import os
import subprocess
import sys
import time

import pandas as pd

from ccz import config
from ccz.logs import get_logger
from ccz.validate import DataCheckError, check_hourly

PIPELINE = [
    "01_clean_tomtom.py",
    "02_clean_air.py",
    "03_build_hourly_table.py",
    "CHECK",
    "25_train_final.py",
    "26_predict.py",
]


def run_script(name, log):
    """Run one script. Copy its output into the log. Return True if it worked."""
    path = config.PROJECT_ROOT / "scripts" / name
    if not path.exists():
        log.error("Missing script: %s", path)
        return False
    start = time.time()
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, str(path)], capture_output=True, text=True,
        encoding="utf-8", cwd=config.PROJECT_ROOT, env=env,
    )
    for line in (result.stdout + result.stderr).strip().splitlines():
        log.info("    %s", line)
    seconds = time.time() - start
    if result.returncode != 0:
        log.error("FAILED: %s (exit code %s, %.0fs)", name, result.returncode, seconds)
        return False
    log.info("Done: %s (%.0fs)", name, seconds)
    return True


def run_checks(log):
    """Run the data checks on the hourly table. Return True if all pass."""
    try:
        for item in check_hourly(pd.read_csv(config.HOURLY_FILE)):
            log.info("Check passed: %s", item)
        return True
    except (DataCheckError, FileNotFoundError) as err:
        log.error("DATA CHECK FAILED: %s", err)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run the whole pipeline.")
    parser.add_argument("--download", action="store_true",
                        help="download air quality and weather first")
    args = parser.parse_args()

    log = get_logger("run_all")
    steps = (["00_download_air_weather.py"] if args.download else []) + PIPELINE
    start = time.time()
    for step in steps:
        ok = run_checks(log) if step == "CHECK" else run_script(step, log)
        if not ok:
            log.error("Pipeline stopped. Fix the problem above and run again.")
            sys.exit(1)
    log.info("Pipeline finished in %.0fs.", time.time() - start)


if __name__ == "__main__":
    main()