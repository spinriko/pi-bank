import json
import os
import sys
import tempfile
import unittest
from unittest import mock

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from core import access_engine, break_glass, credential_collector
from hardware import indicators, relay
from sentinel import event_logger, log_rotation


class CredentialApiDecisionIntegrationTests(unittest.TestCase):
    def _config_get(self, key):
        return {
            "zone_code": "ITROOM",
            "device_id": "dev-1",
            "team_id": "team-1",
        }[key]

    def test_uid_pin_to_api_allow(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UID1"), mock.patch(
            "core.credential_collector.get_pin", return_value="1234"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 10,
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

    def test_uid_pin_to_api_deny(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UID1"), mock.patch(
            "core.credential_collector.get_pin", return_value="0000"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 10,
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

    def test_api_unreachable(self):
        with mock.patch("core.credential_collector.read_uid", return_value="UID1"), mock.patch(
            "core.credential_collector.get_pin", return_value="9999"
        ), mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access", side_effect=OSError("offline")
        ):
            uid, pin = credential_collector.collect_credentials()
            result = access_engine.process_attempt(uid, pin)
            self.assertFalse(result.granted)
            self.assertEqual(result.reason, "API_UNREACHABLE")


class LoggingIntegrationTests(unittest.TestCase):
    def test_success_denied_break_glass_events_and_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "events.jsonl")

            success_event = {
                "timestamp": 1,
                "badge_uid": "U1",
                "zone_code": "ITROOM",
                "device_id": "dev",
                "team_id": "team",
                "network_status": "online",
                "access_granted": True,
                "denial_reason": None,
                "employee_id": 1,
                "full_name": "Alice",
            }
            denied_event = {
                **success_event,
                "timestamp": 2,
                "access_granted": False,
                "denial_reason": "INVALID_PIN",
            }

            with mock.patch("config.config_loader.get", return_value=log_path), mock.patch(
                "sentinel.event_logger.rotate_if_needed", wraps=log_rotation.rotate_if_needed
            ), mock.patch("sentinel.log_rotation.get", side_effect=lambda k: {
                "log_path": log_path,
                "log_max_bytes": 1,
            }[k]):
                event_logger.log_event(success_event)
                event_logger.log_event(denied_event)
                offline = break_glass.AccessResult(
                    granted=False,
                    reason="OFFLINE_DENY",
                    employee_id=None,
                    full_name=None,
                    zone_code="ITROOM",
                    badge_uid="U2",
                    source_device="dev",
                    source_team="team",
                    network_status="offline",
                ).to_dict()
                event_logger.log_event(offline)

            active_exists = os.path.exists(log_path)
            rotated_exists = os.path.exists(log_path + ".1")
            self.assertTrue(active_exists or rotated_exists)

            contents = []
            if active_exists:
                with open(log_path, "r", encoding="utf-8") as f:
                    contents.append(f.read())
            if rotated_exists:
                with open(log_path + ".1", "r", encoding="utf-8") as f:
                    contents.append(f.read())

            combined = "\n".join(contents)
            self.assertNotIn("1234", combined)
            self.assertNotIn("p_pin_code", combined)
            self.assertIn("network_status", combined)


if __name__ == "__main__":
    unittest.main()
