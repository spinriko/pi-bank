"""Scan keypad and collect a 4-digit PIN."""


def get_pin():
    """Read and return a 4-digit PIN string."""
    while True:
        pin = input("Enter 4-digit PIN: ").strip()
        if len(pin) == 4 and pin.isdigit():
            return pin
