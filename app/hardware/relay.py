"""Control the door unlock relay output."""


def unlock(duration_ms):
    """Unlock the door for the provided duration in milliseconds."""
    print("[RELAY] Unlocked for " + str(duration_ms) + " ms")
