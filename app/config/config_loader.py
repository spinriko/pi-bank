"""Load and validate application settings from settings.json."""

import json

_SETTINGS = None
_REQUIRED_KEYS = (
    "device_id",
    "team_id",
    "zone_code",
    "api_url",
    "api_username",
    "api_password",
    "break_glass_mode",
    "break_glass_allow_uids",
    "log_path",
    "log_max_bytes",
)


def _load_settings():
    with open("config/settings.json", "r", encoding="utf-8") as settings_file:
        data = json.load(settings_file)

    for key in _REQUIRED_KEYS:
        if key not in data:
            raise ValueError("Missing required setting: " + key)

    if data["break_glass_mode"] not in ("deny", "allow_list"):
        raise ValueError("break_glass_mode must be one of: deny, allow_list")

    if not isinstance(data["break_glass_allow_uids"], list):
        raise ValueError("break_glass_allow_uids must be a list")

    return data


def get(key):
    """Return a settings value by key."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = _load_settings()
    return _SETTINGS[key]
