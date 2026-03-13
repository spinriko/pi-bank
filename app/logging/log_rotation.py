"""Rotate log file when it reaches configured size."""

import os

from config.config_loader import get


def rotate_if_needed():
    """Rotate active log file if it exceeds max bytes."""
    log_path = get("log_path")
    max_bytes = get("log_max_bytes")

    if not os.path.exists(log_path):
        return

    if os.path.getsize(log_path) < max_bytes:
        return

    rotated_path = log_path + ".1"
    if os.path.exists(rotated_path):
        os.remove(rotated_path)
    os.replace(log_path, rotated_path)
