"""
Run logs. Each run writes a plain text log in logs/ and also prints to the screen.
"""

import logging
from datetime import datetime, timezone

from ccz import config


def get_logger(name):
    """Return a logger that writes to logs/<name>_<time>.log and to the screen."""
    config.LOGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = config.LOGS_DIR / f"{name}_{stamp}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", "%Y-%m-%d %H:%M:%S")
    for handler in (logging.FileHandler(path, encoding="utf-8"), logging.StreamHandler()):
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    logger.info("log file: %s", path)
    return logger