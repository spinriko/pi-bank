"""Orchestrate credential collection in badge-then-PIN order."""

from hardware.keypad import get_pin
from hardware.rfid_reader import read_uid


def collect_credentials():
    """Collect and return a badge UID and PIN tuple."""
    uid = None
    while uid is None:
        uid = read_uid()
    pin = get_pin()
    return uid, pin
