"""Detect whether network connectivity is available."""

import socket


def is_online():
    """Return True when the network is reachable."""
    try:
        connection = socket.create_connection(("1.1.1.1", 53), 1)
        connection.close()
        return True
    except OSError:
        return False
