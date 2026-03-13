import os
import sys
import unittest
from unittest import mock

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

if "logging" in sys.modules and not hasattr(sys.modules["logging"], "__path__"):
    del sys.modules["logging"]

from core import access_engine, break_glass, credential_collector
from hardware import indicators, relay


class EndToEndScenarioTests(unittest.TestCase):
    def _config_get(self, key):
        return {
            "zone_code": "ITROOM",
            "device_id": "dev-1",
            "team_id": "team-1",
            "break_glass_mode": "deny",
            "break_glass_allow_uids": [],
        }[key]

    def test_scenario_a_valid_access(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UID1"), mock.patch(
            "core.credential_collector.get_pin", return_value="1234"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 1,
                "full_name": "Alice",
                "zone_code": "ITROOM",
                "access_granted": True,
                "denial_reason": None,
            },
        ), mock.patch("hardware.relay.unlock") as unlock, mock.patch(
            "hardware.indicators.success_feedback"
        ) as success:
            uid, pin = credential_collector.collect_credentials()
            result = access_engine.process_attempt(uid, pin)
            if result.granted:
                relay.unlock(2000)
                indicators.success_feedback()

            self.assertTrue(result.granted)
            unlock.assert_called_once_with(2000)
            success.assert_called_once()

    def test_scenario_b_invalid_pin(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UID1"), mock.patch(
            "core.credential_collector.get_pin", return_value="0000"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 1,
                "full_name": "Alice",
                "zone_code": "ITROOM",
                "access_granted": False,
                "denial_reason": "INVALID_PIN",
            },
        ), mock.patch("hardware.relay.unlock") as unlock, mock.patch(
            "hardware.indicators.failure_feedback"
        ) as failure:
            uid, pin = credential_collector.collect_credentials()
            result = access_engine.process_attempt(uid, pin)
            if not result.granted:
                indicators.failure_feedback(result.reason)

            self.assertFalse(result.granted)
            unlock.assert_not_called()
            failure.assert_called_once_with("INVALID_PIN")

    def test_scenario_c_unknown_badge(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UNKNOWN"), mock.patch(
            "core.credential_collector.get_pin", return_value="1234"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": None,
                "full_name": None,
                "zone_code": "ITROOM",
                "access_granted": False,
                "denial_reason": "UNKNOWN_BADGE",
            },
        ):
            uid, pin = credential_collector.collect_credentials()
            result = access_engine.process_attempt(uid, pin)
            self.assertFalse(result.granted)
            self.assertEqual(result.reason, "UNKNOWN_BADGE")

    def test_scenario_d_api_offline_break_glass(self):
        with mock.patch("core.break_glass.get", side_effect=self._config_get):
            result = break_glass.fallback_decision("UID1", "1234")
            self.assertFalse(result.granted)
            self.assertEqual(result.network_status, "offline")


if __name__ == "__main__":
    unittest.main()
