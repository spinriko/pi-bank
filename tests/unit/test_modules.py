import json
import os
import sys
import tempfile
import types
import unittest
from io import StringIO
from unittest import mock

APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "app"))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

logging_pkg = types.ModuleType("logging")
logging_pkg.__path__ = [os.path.join(APP_DIR, "logging")]
sys.modules["logging"] = logging_pkg

from config import config_loader
from core import access_engine, break_glass, credential_collector
from hardware import indicators, keypad, relay, rfid_reader
from logging import event_logger, log_rotation
from network import api_client, net_status


class RfidReaderTests(unittest.TestCase):
    def test_returns_uid_when_present(self):
        with mock.patch("builtins.input", return_value="ABC123"):
            self.assertEqual(rfid_reader.read_uid(), "ABC123")

    def test_returns_none_when_empty(self):
        with mock.patch("builtins.input", return_value=""):
            self.assertIsNone(rfid_reader.read_uid())

    def test_handles_read_errors_gracefully(self):
        with mock.patch("builtins.input", side_effect=EOFError):
            self.assertIsNone(rfid_reader.read_uid())

    def test_repeated_reads_are_stable(self):
        with mock.patch("builtins.input", side_effect=["A1", "A1"]):
            self.assertEqual(rfid_reader.read_uid(), "A1")
            self.assertEqual(rfid_reader.read_uid(), "A1")


class KeypadTests(unittest.TestCase):
    def test_collects_four_digit_pin(self):
        with mock.patch("builtins.input", return_value="1234"):
            self.assertEqual(keypad.get_pin(), "1234")

    def test_rejects_non_digit_then_accepts_valid(self):
        with mock.patch("builtins.input", side_effect=["12a4", "9999"]):
            self.assertEqual(keypad.get_pin(), "9999")

    def test_handles_key_bounce_by_reprompt(self):
        with mock.patch("builtins.input", side_effect=["1", "12", "123", "1234"]):
            self.assertEqual(keypad.get_pin(), "1234")

    def test_no_input_then_valid(self):
        with mock.patch("builtins.input", side_effect=["", "0000"]):
            self.assertEqual(keypad.get_pin(), "0000")


class IndicatorTests(unittest.TestCase):
    def test_idle_state(self):
        with mock.patch("builtins.print") as p:
            indicators.idle_state()
            p.assert_called_once_with("[IDLE] Ready")

    def test_success_feedback(self):
        with mock.patch("builtins.print") as p:
            indicators.success_feedback()
            p.assert_called_once_with("[SUCCESS] Access granted")

    def test_failure_feedback(self):
        with mock.patch("builtins.print") as p:
            indicators.failure_feedback("INVALID_PIN")
            p.assert_called_once_with("[FAILURE] INVALID_PIN")


class RelayTests(unittest.TestCase):
    def test_unlock_activates(self):
        with mock.patch("builtins.print") as p:
            relay.unlock(2000)
            p.assert_called_once_with("[RELAY] Unlocked for 2000 ms")

    def test_invalid_duration_is_handled(self):
        with mock.patch("builtins.print") as p:
            relay.unlock(-1)
            p.assert_called_once_with("[RELAY] Unlocked for -1 ms")


class ApiClientTests(unittest.TestCase):
    def test_builds_payload_and_sends_to_url(self):
        response = mock.Mock()
        response.read.return_value = b'{"access_granted": true}'
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)

        with mock.patch("config.config_loader.get", side_effect=lambda k: {
            "api_url": "https://example.local/validate",
            "api_token": "token",
        }[k]), mock.patch("network.api_client.urllib.request.urlopen", return_value=response) as urlopen:
            result = api_client.validate_access("UID1", "1234", "ITROOM", "dev", "team")

            self.assertTrue(result["access_granted"])
            request = urlopen.call_args.args[0]
            self.assertEqual(request.full_url, "https://example.local/validate")
            payload = json.loads(request.data.decode("utf-8"))
            self.assertEqual(payload["p_badge_uid"], "UID1")
            self.assertEqual(payload["p_pin_code"], "1234")
            self.assertEqual(payload["p_zone_code"], "ITROOM")
            self.assertEqual(payload["p_source_device"], "dev")
            self.assertEqual(payload["p_source_team"], "team")

    def test_handles_http_200_deny(self):
        response = mock.Mock()
        response.read.return_value = b'{"access_granted": false, "denial_reason": "INVALID_PIN"}'
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)

        with mock.patch("config.config_loader.get", side_effect=lambda k: {
            "api_url": "https://example.local/validate",
            "api_token": "token",
        }[k]), mock.patch("network.api_client.urllib.request.urlopen", return_value=response):
            result = api_client.validate_access("UID1", "0000", "ITROOM", "dev", "team")
            self.assertFalse(result["access_granted"])
            self.assertEqual(result["denial_reason"], "INVALID_PIN")

    def test_handles_http_errors(self):
        with mock.patch("config.config_loader.get", side_effect=lambda k: {
            "api_url": "https://example.local/validate",
            "api_token": "token",
        }[k]), mock.patch("network.api_client.urllib.request.urlopen", side_effect=OSError("http error")):
            with self.assertRaises(OSError):
                api_client.validate_access("UID1", "1234", "ITROOM", "dev", "team")

    def test_handles_timeouts(self):
        with mock.patch("config.config_loader.get", side_effect=lambda k: {
            "api_url": "https://example.local/validate",
            "api_token": "token",
        }[k]), mock.patch("network.api_client.urllib.request.urlopen", side_effect=TimeoutError("timeout")):
            with self.assertRaises(TimeoutError):
                api_client.validate_access("UID1", "1234", "ITROOM", "dev", "team")

    def test_handles_malformed_json(self):
        response = mock.Mock()
        response.read.return_value = b"not-json"
        response.__enter__ = mock.Mock(return_value=response)
        response.__exit__ = mock.Mock(return_value=False)

        with mock.patch("config.config_loader.get", side_effect=lambda k: {
            "api_url": "https://example.local/validate",
            "api_token": "token",
        }[k]), mock.patch("network.api_client.urllib.request.urlopen", return_value=response):
            with self.assertRaises(json.JSONDecodeError):
                api_client.validate_access("UID1", "1234", "ITROOM", "dev", "team")


class NetStatusTests(unittest.TestCase):
    def test_detects_online(self):
        fake_conn = mock.Mock()
        with mock.patch("network.net_status.socket.create_connection", return_value=fake_conn):
            self.assertTrue(net_status.is_online())
            fake_conn.close.assert_called_once()

    def test_detects_offline(self):
        with mock.patch("network.net_status.socket.create_connection", side_effect=OSError("down")):
            self.assertFalse(net_status.is_online())

    def test_handles_intermittent_connectivity(self):
        fake_conn = mock.Mock()
        with mock.patch("network.net_status.socket.create_connection", side_effect=[OSError("down"), fake_conn]):
            self.assertFalse(net_status.is_online())
            self.assertTrue(net_status.is_online())


class CredentialCollectorTests(unittest.TestCase):
    def test_collects_uid_then_pin_in_order(self):
        calls = []

        def read_uid_side_effect():
            calls.append("uid")
            return "U-1"

        def get_pin_side_effect():
            calls.append("pin")
            return "1234"

        with mock.patch("core.credential_collector.read_uid", side_effect=read_uid_side_effect), mock.patch(
            "core.credential_collector.get_pin", side_effect=get_pin_side_effect
        ):
            uid, pin = credential_collector.collect_credentials()
            self.assertEqual((uid, pin), ("U-1", "1234"))
            self.assertEqual(calls, ["uid", "pin"])

    def test_rejects_empty_uid(self):
        with mock.patch("core.credential_collector.read_uid", side_effect=[None, "U-1"]), mock.patch(
            "core.credential_collector.get_pin", return_value="1234"
        ):
            uid, pin = credential_collector.collect_credentials()
            self.assertEqual((uid, pin), ("U-1", "1234"))

    def test_rejects_empty_pin_before_valid(self):
        with mock.patch("core.credential_collector.read_uid", return_value="U-1"), mock.patch(
            "core.credential_collector.get_pin", side_effect=["", "1234"]
        ):
            uid, pin = credential_collector.collect_credentials()
            self.assertEqual((uid, pin), ("U-1", ""))

    def test_handles_cancellation(self):
        with mock.patch("core.credential_collector.read_uid", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                credential_collector.collect_credentials()


class AccessEngineTests(unittest.TestCase):
    def _config_get(self, key):
        return {
            "zone_code": "ITROOM",
            "device_id": "dev-1",
            "team_id": "team-1",
        }[key]

    def test_interprets_allow_response(self):
        with mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 1,
                "full_name": "Alice",
                "zone_code": "ITROOM",
                "access_granted": True,
                "denial_reason": None,
            },
        ):
            result = access_engine.process_attempt("UID1", "1234")
            self.assertTrue(result.granted)
            self.assertIsNone(result.reason)
            self.assertEqual(result.employee_id, 1)

    def test_interprets_deny_and_denial_reasons(self):
        reasons = [
            "UNKNOWN_BADGE",
            "EMPLOYEE_INACTIVE",
            "BADGE_INACTIVE",
            "UNKNOWN_ZONE",
            "ZONE_ACCESS_DENIED",
            "INVALID_PIN",
        ]

        for reason in reasons:
            with self.subTest(reason=reason):
                with mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
                    "core.access_engine.validate_access",
                    return_value={
                        "employee_id": 2,
                        "full_name": "Bob",
                        "zone_code": "ITROOM",
                        "access_granted": False,
                        "denial_reason": reason,
                    },
                ):
                    result = access_engine.process_attempt("UID2", "0000")
                    self.assertFalse(result.granted)
                    self.assertEqual(result.reason, reason)

    def test_produces_valid_access_result(self):
        with mock.patch("core.access_engine.get", side_effect=self._config_get), mock.patch(
            "core.access_engine.validate_access",
            return_value={
                "employee_id": 3,
                "full_name": "Cara",
                "zone_code": "ITROOM",
                "access_granted": True,
                "denial_reason": None,
            },
        ):
            result = access_engine.process_attempt("UID3", "1111")
            as_dict = result.to_dict()
            required = {
                "timestamp",
                "badge_uid",
                "zone_code",
                "device_id",
                "team_id",
                "network_status",
                "access_granted",
                "denial_reason",
                "employee_id",
                "full_name",
            }
            self.assertTrue(required.issubset(set(as_dict.keys())))


class BreakGlassTests(unittest.TestCase):
    def test_returns_configured_fallback_decision_deny(self):
        with mock.patch("core.break_glass.get", side_effect=lambda k: {
            "zone_code": "ITROOM",
            "device_id": "dev",
            "team_id": "team",
            "break_glass_mode": "deny",
            "break_glass_allow_uids": [],
        }[k]):
            result = break_glass.fallback_decision("UID1", "1234")
            self.assertFalse(result.granted)
            self.assertEqual(result.reason, "OFFLINE_DENY")
            self.assertEqual(result.network_status, "offline")

    def test_returns_configured_fallback_decision_allow_list(self):
        with mock.patch("core.break_glass.get", side_effect=lambda k: {
            "zone_code": "ITROOM",
            "device_id": "dev",
            "team_id": "team",
            "break_glass_mode": "allow_list",
            "break_glass_allow_uids": ["UID1"],
        }[k]):
            result = break_glass.fallback_decision("UID1", "1234")
            self.assertTrue(result.granted)
            self.assertIsNone(result.reason)


class EventLoggerTests(unittest.TestCase):
    def test_writes_jsonl_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "events.jsonl")

            with mock.patch("config.config_loader.get", return_value=log_path), mock.patch(
                "logging.event_logger.rotate_if_needed"
            ):
                event_logger.log_event({"access_granted": True})

            with open(log_path, "r", encoding="utf-8") as f:
                line = f.read().strip()
                self.assertEqual(json.loads(line)["access_granted"], True)

    def test_never_logs_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "events.jsonl")
            event = {"access_granted": False, "denial_reason": "INVALID_PIN"}

            with mock.patch("config.config_loader.get", return_value=log_path), mock.patch(
                "logging.event_logger.rotate_if_needed"
            ):
                event_logger.log_event(event)

            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn("p_pin_code", content)
                self.assertNotIn('"pin"', content.lower())
                self.assertNotIn("1234", content)

    def test_includes_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = os.path.join(tmp, "events.jsonl")
            event = {
                "timestamp": 1,
                "badge_uid": "UID1",
                "zone_code": "ITROOM",
                "device_id": "dev",
                "team_id": "team",
                "network_status": "online",
                "access_granted": True,
                "denial_reason": None,
                "employee_id": 1,
                "full_name": "Alice",
            }

            with mock.patch("config.config_loader.get", return_value=log_path), mock.patch(
                "logging.event_logger.rotate_if_needed"
            ):
                event_logger.log_event(event)

            with open(log_path, "r", encoding="utf-8") as f:
                parsed = json.loads(f.read().strip())
            self.assertEqual(set(parsed.keys()), set(event.keys()))

    def test_handles_file_write_errors(self):
        with mock.patch("config.config_loader.get", return_value="/bad/path"), mock.patch(
            "logging.event_logger.rotate_if_needed"
        ), mock.patch("builtins.open", side_effect=OSError("write error")):
            with self.assertRaises(OSError):
                event_logger.log_event({"access_granted": True})


class LogRotationTests(unittest.TestCase):
    def test_rotates_at_threshold_and_preserves_old(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "events.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write("x" * 20)

            with mock.patch("logging.log_rotation.get", side_effect=lambda k: {
                "log_path": path,
                "log_max_bytes": 10,
            }[k]):
                log_rotation.rotate_if_needed()

            self.assertFalse(os.path.exists(path))
            self.assertTrue(os.path.exists(path + ".1"))

    def test_no_rotation_under_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "events.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                f.write("x" * 5)

            with mock.patch("logging.log_rotation.get", side_effect=lambda k: {
                "log_path": path,
                "log_max_bytes": 10,
            }[k]):
                log_rotation.rotate_if_needed()

            self.assertTrue(os.path.exists(path))
            self.assertFalse(os.path.exists(path + ".1"))


class ConfigLoaderTests(unittest.TestCase):
    def setUp(self):
        config_loader._SETTINGS = None

    def test_loads_settings_json(self):
        payload = {
            "device_id": "d",
            "team_id": "t",
            "zone_code": "z",
            "api_url": "u",
            "api_token": "tok",
            "break_glass_mode": "deny",
            "break_glass_allow_uids": [],
            "log_path": "p",
            "log_max_bytes": 1,
        }

        with mock.patch("config.config_loader.open", mock.mock_open(read_data=json.dumps(payload))):
            self.assertEqual(config_loader.get("device_id"), "d")

    def test_validates_required_keys(self):
        payload = {
            "device_id": "d",
            "team_id": "t",
        }

        with mock.patch("config.config_loader.open", mock.mock_open(read_data=json.dumps(payload))):
            with self.assertRaises(ValueError):
                config_loader.get("device_id")

    def test_rejects_malformed_config(self):
        with mock.patch("config.config_loader.open", mock.mock_open(read_data="{bad json")):
            with self.assertRaises(json.JSONDecodeError):
                config_loader.get("device_id")

    def test_returns_value_by_key(self):
        payload = {
            "device_id": "d",
            "team_id": "t",
            "zone_code": "z",
            "api_url": "u",
            "api_token": "tok",
            "break_glass_mode": "deny",
            "break_glass_allow_uids": [],
            "log_path": "p",
            "log_max_bytes": 1,
        }

        with mock.patch("config.config_loader.open", mock.mock_open(read_data=json.dumps(payload))):
            self.assertEqual(config_loader.get("team_id"), "t")


if __name__ == "__main__":
    unittest.main()
