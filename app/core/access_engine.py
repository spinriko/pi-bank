"""Process online access attempts using the API decision."""

import time
from dataclasses import dataclass

from config.config_loader import get
from network.api_client import validate_access


@dataclass
class AccessResult:
    """Structured result for an access attempt."""

    granted: bool
    reason: str | None
    employee_id: int | None
    full_name: str | None
    zone_code: str
    badge_uid: str
    source_device: str
    source_team: str
    network_status: str

    def to_dict(self):
        """Convert result to a log-safe dictionary."""
        return {
            "timestamp": int(time.time()),
            "badge_uid": self.badge_uid,
            "zone_code": self.zone_code,
            "device_id": self.source_device,
            "team_id": self.source_team,
            "network_status": self.network_status,
            "access_granted": self.granted,
            "denial_reason": self.reason,
            "employee_id": self.employee_id,
            "full_name": self.full_name,
        }


def process_attempt(uid, pin):
    """Validate credentials online and return an AccessResult."""
    zone = get("zone_code")
    device = get("device_id")
    team = get("team_id")

    try:
        response = validate_access(uid, pin, zone, device, team)
    except Exception:
        return AccessResult(
            granted=False,
            reason="API_UNREACHABLE",
            employee_id=None,
            full_name=None,
            zone_code=zone,
            badge_uid=uid,
            source_device=device,
            source_team=team,
            network_status="online",
        )

    return AccessResult(
        granted=bool(response.get("access_granted", False)),
        reason=response.get("denial_reason"),
        employee_id=response.get("employee_id"),
        full_name=response.get("full_name"),
        zone_code=response.get("zone_code", zone),
        badge_uid=uid,
        source_device=device,
        source_team=team,
        network_status="online",
    )
