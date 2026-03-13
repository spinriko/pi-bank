# Testing Specification
## Access Control System – CircuitPython Implementation

This document defines the complete testing requirements for the access‑control application.  
It ensures deterministic behavior, prevents agent drift, and guarantees that all modules conform to the architecture and responsibilities defined in the agent instruction module.

All tests must be **repeatable**, **isolated**, and **hardware‑safe**.

---

# 1. Testing Philosophy

1. Tests validate **behavior**, not implementation details.
2. Each module is tested **independently** using mocks or stubs.
3. No test may require physical hardware unless explicitly marked as a hardware test.
4. All tests must be deterministic — no randomness, no timing‑dependent behavior.
5. Tests must not modify the architecture or introduce new responsibilities.

---

# 2. Test Categories

## 2.1 Unit Tests
Validate each module in isolation using mocks.

## 2.2 Integration Tests
Validate interactions between:
- credential collection → API client → access engine  
- access engine → indicators → relay  
- logging → file rotation  

## 2.3 Hardware Tests
Validate physical components:
- keypad  
- RFID reader  
- relay  
- LEDs / buzzer  

## 2.4 End‑to‑End Tests
Simulate a full access attempt:
- badge → PIN → API → decision → feedback → logging  

---

# 3. Unit Test Specifications (Module‑Level)

## 3.1 hardware.rfid_reader
**Tests**
- Returns UID string when badge is present  
- Returns `None` when no badge is present  
- Handles read errors gracefully  
- Debounces repeated reads  

**Mocks**
- RFID hardware interface  

---

## 3.2 hardware.keypad
**Tests**
- Correctly collects 4‑digit PIN  
- Rejects non‑digit keys  
- Handles key bounce  
- Times out if no input  

**Mocks**
- Keypad matrix scanner  

---

## 3.3 hardware.indicators
**Tests**
- `idle_state()` sets correct indicator state  
- `success_feedback()` triggers success pattern  
- `failure_feedback(reason)` triggers failure pattern  

**Mocks**
- GPIO pins  
- Display (if present)  

---

## 3.4 hardware.relay
**Tests**
- `unlock(duration_ms)` activates relay  
- Relay deactivates after duration  
- Handles invalid durations  

**Mocks**
- Relay GPIO pin  

---

## 3.5 network.api_client
**Tests**
- Builds correct POST payload  
- Sends request to correct URL  
- Handles HTTP 200 with allow  
- Handles HTTP 200 with deny  
- Handles HTTP errors  
- Handles timeouts  
- Handles malformed JSON  

**Mocks**
- Network stack  
- API responses  

---

## 3.6 network.net_status
**Tests**
- Detects online state  
- Detects offline state  
- Handles intermittent connectivity  

**Mocks**
- Socket connection attempts  

---

## 3.7 core.credential_collector
**Tests**
- Collects UID then PIN in correct order  
- Rejects empty UID  
- Rejects empty PIN  
- Handles cancellation  

**Mocks**
- rfid_reader  
- keypad  

---

## 3.8 core.access_engine
**Tests**
- Interprets allow response  
- Interprets deny response  
- Maps denial reason correctly  
- Produces valid AccessResult  

**Mocks**
- api_client  

---

## 3.9 core.break_glass
**Tests**
- Returns configured fallback decision  
- Logs break‑glass usage  
- Produces valid AccessResult  

**Mocks**
- config_loader  

---

## 3.10 logging.event_logger
**Tests**
- Writes JSONL entry  
- Never logs PIN  
- Includes required fields  
- Handles file write errors  

**Mocks**
- File I/O  

---

## 3.11 logging.log_rotation
**Tests**
- Rotates file at size threshold  
- Creates new log file  
- Preserves old logs  

**Mocks**
- File system  

---

## 3.12 config.config_loader
**Tests**
- Loads settings.json  
- Validates required keys  
- Rejects malformed config  
- Provides default values where allowed  

**Mocks**
- File I/O  

---

# 4. Integration Test Specifications

## 4.1 Credential → API → Decision
Simulate:
- UID read  
- PIN entry  
- API allow  
- API deny  
- API unreachable  

Validate:
- Correct AccessResult  
- Correct indicator behavior  
- Correct relay behavior  

---

## 4.2 Logging Integration
Simulate:
- Success event  
- Denied event  
- Break‑glass event  

Validate:
- Correct JSONL structure  
- No PIN leakage  
- Log rotation triggers  

---

# 5. Hardware Test Specifications

## 5.1 RFID Reader
- Detects badge reliably  
- No false positives  
- UID matches expected  

## 5.2 Keypad
- All keys register  
- No ghosting  
- No bounce  

## 5.3 Relay
- Activates lock  
- Releases lock  
- Timing accuracy ±10%  

## 5.4 Indicators
- LEDs show correct states  
- Buzzer patterns correct  
- Display messages correct  

---

# 6. End‑to‑End Test Scenarios

## Scenario A: Valid Access
1. Present valid badge  
2. Enter correct PIN  
3. API returns allow  

**Expected**
- Door unlocks  
- Success feedback  
- Log entry with `"granted": true`  

---

## Scenario B: Invalid PIN
1. Present valid badge  
2. Enter wrong PIN  
3. API returns deny  

**Expected**
- No unlock  
- Failure feedback  
- Log entry with denial reason  

---

## Scenario C: Unknown Badge
**Expected**
- Deny  
- Failure feedback  
- Log entry  

---

## Scenario D: API Offline (Break‑Glass)
**Expected**
- Fallback decision  
- Log entry with `"network": "offline"`  

---

# 7. Test Coverage Requirements

- 100% of modules must have unit tests  
- 100% of API paths must be tested  
- 100% of denial reasons must be tested  
- 100% of logging fields must be validated  
- 100% of hardware interfaces must have mocks  

---

# 8. Test Execution Rules

- Tests must run offline  
- Tests must not require real API  
- Tests must not require real hardware unless explicitly marked  
- Tests must not modify production settings.json  
- Tests must not write to production logs  

---

# 9. Summary

This testing specification ensures:
- Deterministic behavior  
- Architecture compliance  
- No agent drift  
- Full coverage of all functional and non‑functional requirements  

This document is authoritative and must be followed by any code‑generation agent or human developer.
