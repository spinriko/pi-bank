"""Initialize and read RFID badge UID values."""


def read_uid():
    """Read a badge UID and return it as a string, or None if unavailable."""
    try:
        uid = input("Scan badge UID: ").strip()
    except EOFError:
        return None

    if not uid:
        return None
    return uid
