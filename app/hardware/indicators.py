"""Provide deterministic user feedback states via indicators."""


def idle_state():
    """Set indicators to idle state."""
    print("[IDLE] Ready")


def success_feedback():
    """Show successful access feedback."""
    print("[SUCCESS] Access granted")


def failure_feedback(reason):
    """Show failed access feedback."""
    message = reason if reason else "ACCESS_DENIED"
    print("[FAILURE] " + message)
