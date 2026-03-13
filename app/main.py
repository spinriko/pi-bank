"""Main deterministic loop for access control processing."""

from core.access_engine import process_attempt
from core.break_glass import fallback_decision
from core.credential_collector import collect_credentials
from hardware import indicators, relay
from sentinel import event_logger
from network import net_status


while True:
    indicators.idle_state()

    uid, pin = collect_credentials()

    if net_status.is_online():
        result = process_attempt(uid, pin)
    else:
        result = fallback_decision(uid, pin)

    if result.granted:
        relay.unlock(2000)
        indicators.success_feedback()
    else:
        indicators.failure_feedback(result.reason)

    event_logger.log_event(result.to_dict())
