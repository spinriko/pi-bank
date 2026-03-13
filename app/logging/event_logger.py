"""Append structured JSONL access events to local storage."""

import json

from logging.log_rotation import rotate_if_needed


def log_event(event_dict):
    """Append one event dictionary to the configured JSONL log file."""
    from config.config_loader import get

    rotate_if_needed()
    log_path = get("log_path")

    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(event_dict, separators=(",", ":")) + "\n")
