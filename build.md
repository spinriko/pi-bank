# Code Generation Agent Instructions
## Access Control System – CircuitPython Implementation

This document defines the **strict rules** the code‑generation agent must follow when producing source code for the access‑control system.  
The agent must treat this document as authoritative and must not deviate from the architecture, file layout, naming conventions, or module responsibilities defined here.

The goal is deterministic, reproducible, non‑drifting code generation.

---

# 1. General Rules

1. The agent **must not invent new modules**, directories, or architectural patterns.
2. The agent **must not merge modules**, combine responsibilities, or create “utility” files.
3. The agent **must not introduce classes** unless explicitly required; simple functions and small data structures are preferred.
4. The agent **must not change function names**, signatures, or return types.
5. The agent **must not introduce asynchronous code**, threads, or concurrency.
6. The agent **must not add business logic** not explicitly defined in the architecture.
7. The agent **must not modify the folder structure**.
8. The agent **must not create circular dependencies**.
9. The agent **must not add external dependencies** beyond CircuitPython‑standard libraries.

All code must be deterministic, minimal, and aligned with the architecture.

---

# 2. Folder Structure (Authoritative)

The agent must generate code **only** within this structure:

app/
├── hardware/
│   ├── rfid_reader.py
│   ├── keypad.py
│   ├── indicators.py
│   └── relay.py
│
├── network/
│   ├── api_client.py
│   └── net_status.py
│
├── core/
│   ├── credential_collector.py
│   ├── access_engine.py
│   └── break_glass.py
│
├── logging/
│   ├── event_logger.py
│   └── log_rotation.py
│
├── config/
│   ├── config_loader.py
│   └── settings.json
│
└── main.py


The agent must not create files outside this tree.

---

# 3. Module Responsibilities (Strict)

Each module has a single responsibility.  
The agent must not add responsibilities or move logic between modules.

## 3.1 hardware.rfid_reader
- Initialize RFID hardware
- Read badge UID
- Expose: `read_uid() -> str | None`

## 3.2 hardware.keypad
- Scan keypad
- Collect 4‑digit PIN
- Expose: `get_pin() -> str`

## 3.3 hardware.indicators
- LEDs, buzzer, display
- Expose:
  - `idle_state()`
  - `success_feedback()`
  - `failure_feedback(reason)`

## 3.4 hardware.relay
- Door unlock control
- Expose: `unlock(duration_ms)`

---

## 3.5 network.api_client
- Build POST payload
- Send HTTPS request
- Parse JSON
- Expose:  
  `validate_access(uid, pin, zone, device, team) -> dict`

## 3.6 network.net_status
- Detect online/offline
- Expose: `is_online() -> bool`

---

## 3.7 core.credential_collector
- Orchestrate badge → PIN sequence
- Expose: `collect_credentials() -> (uid, pin)`

## 3.8 core.access_engine
- Call API client
- Interpret allow/deny
- Expose: `process_attempt(uid, pin) -> AccessResult`

## 3.9 core.break_glass
- Fallback when API unreachable
- Expose: `fallback_decision(uid, pin) -> AccessResult`

---

## 3.10 logging.event_logger
- Append‑only JSONL logging
- Expose: `log_event(event_dict)`

## 3.11 logging.log_rotation
- Optional rotation
- Expose: `rotate_if_needed()`

---

## 3.12 config.config_loader
- Load and validate settings.json
- Expose: `get(key)`

---

# 4. Data Structures

The agent must define a simple `AccessResult` structure:

AccessResult:
granted: bool
reason: str | None
employee_id: int | None
full_name: str | None
zone_code: str


Must include a `.to_dict()` method for logging.

---

# 5. Main Loop (Authoritative)

The agent must implement **exactly** this control flow in `main.py`:

while True:
The agent must not add logic, retries, sleeps, or branching not shown above.

---

# 6. Coding Style Requirements

1. Functions must be small and single‑purpose.
2. No global state except module‑level hardware initialization.
3. No dynamic imports.
4. No unused variables or dead code.
5. No comments that contradict the architecture.
6. All modules must include docstrings describing their responsibility.

---

# 7. Prohibited Behaviors

The agent must **never**:
- invent new hardware
- invent new API fields
- change the API URL or payload
- log PIN values
- implement caching
- implement local authorization logic
- modify the break‑glass rules
- add configuration keys not in settings.json
- introduce classes where not required
- introduce async or threading
- introduce state machines not defined in the architecture

---

# 8. Output Requirements

When generating code, the agent must:

- Output **only** the requested module(s)
- Never rewrite the entire project unless explicitly instructed
- Never modify unrelated modules
- Never generate placeholder code like “TODO”
- Never generate pseudocode unless explicitly asked

All generated code must be **complete, runnable, and aligned with this architecture**.

---

# 9. Summary

This document defines the **complete and authoritative specification** for code generation.  
The agent must treat this as a contract and must not deviate from it under any circumstances.


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



