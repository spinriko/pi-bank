"""Send access validation requests and parse API responses."""

import base64
import json
import ssl
import urllib.request


def validate_access(uid, pin, zone, device, team):
    """Validate credentials against the remote API and return parsed JSON."""
    from config.config_loader import get

    payload = {
        "p_badge_uid": uid,
        "p_pin_code": pin,
        "p_zone_code": zone,
        "p_source_device": device,
        "p_source_team": team,
    }

    credentials = get("api_username") + ":" + get("api_password")
    auth_value = "Basic " + base64.b64encode(credentials.encode("utf-8")).decode("ascii")

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        get("api_url"),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_value,
        },
        method="POST",
    )

    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=2, context=context) as response:
        return json.loads(response.read().decode("utf-8"))
