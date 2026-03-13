"""Initialize and read RFID badge UID values."""

import time

_reader = None
_last_uid = None
_last_uid_time = 0.0

try:
    import board
    import busio
    import digitalio
    import adafruit_mfrc522

    _spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
    _cs = digitalio.DigitalInOut(board.CE0)
    _rst = digitalio.DigitalInOut(board.D25)
    _reader = adafruit_mfrc522.MFRC522(_spi, _cs, _rst)
except Exception:
    _reader = None


def _read_uid_hardware():
    status, _tag_type = _reader.request(_reader.REQIDL)
    if status != _reader.OK:
        return None

    status, raw_uid = _reader.anticoll()
    if status != _reader.OK:
        return None

    uid = "".join("{:02X}".format(part) for part in raw_uid)
    return uid


def _debounced(uid):
    global _last_uid, _last_uid_time
    now = time.monotonic()

    if uid == _last_uid and (now - _last_uid_time) < 0.8:
        return None

    _last_uid = uid
    _last_uid_time = now
    return uid


def read_uid():
    """Read a badge UID and return it as a string, or None if unavailable."""
    if _reader is not None:
        uid = _read_uid_hardware()
        if uid is None:
            return None
        return _debounced(uid)

    try:
        uid = input("Scan badge UID: ").strip()
    except EOFError:
        return None

    if not uid:
        return None
    return _debounced(uid)
