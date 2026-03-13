"""Provide deterministic fallback behavior when API is unreachable."""

from config.config_loader import get
from core.access_engine import AccessResult


def fallback_decision(uid, pin):
    """Return fallback access result based on configured break-glass mode."""
    zone = get("zone_code")
    device = get("device_id")
    team = get("team_id")
    mode = get("break_glass_mode")

    granted = False
    reason = "OFFLINE_DENY"

    if mode == "allow_list" and uid in get("break_glass_allow_uids"):
        granted = True
        reason = None

    return AccessResult(
        granted=granted,
        reason=reason,
        employee_id=None,
        full_name=None,
        zone_code=zone,
        badge_uid=uid,
        source_device=device,
        source_team=team,
        network_status="offline",
    )
