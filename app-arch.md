# Application Architecture (CircuitPython)

This architecture defines the structure, responsibilities, and boundaries of the access‑control application running on the Raspberry Pi. It is designed for deterministic behavior, clean separation of concerns, and compatibility with automated code‑generation agents.

---

## 1. High‑Level Module Layout



Each module has a single responsibility and exposes a stable, minimal interface.

---
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

## 2. Module Responsibilities

### 2.1 hardware.rfid_reader
- Initialize RFID hardware
- Read badge UID
- Debounce and error‑handle read events
- Expose: `read_uid() -> str | None`

### 2.2 hardware.keypad
- Scan keypad matrix
- Collect 4‑digit PIN
- Mask input for display
- Expose: `get_pin() -> str`

### 2.3 hardware.indicators
- Control LEDs, buzzer, or display
- Provide deterministic feedback states
- Expose:
  - `success_feedback()`
  - `failure_feedback(reason)`
  - `idle_state()`

### 2.4 hardware.relay
- Trigger door unlock mechanism
- Expose: `unlock(duration_ms)`

---

## 3. Network Layer

### 3.1 network.api_client
- Construct POST payload
- Handle HTTPS request
- Parse JSON response
- Enforce timeout and retry policy
- Expose:  
  `validate_access(badge_uid, pin, zone, device, team) -> dict`

### 3.2 network.net_status
- Detect online/offline state
- Expose: `is_online() -> bool`

---

## 4. Core Logic

### 4.1 core.credential_collector
- Orchestrates RFID + PIN collection
- Ensures ordering: badge → PIN
- Expose: `collect_credentials() -> (uid, pin)`

### 4.2 core.access_engine
- Calls API client
- Interprets allow/deny
- Routes to indicators + relay
- Expose: `process_attempt(uid, pin) -> AccessResult`

### 4.3 core.break_glass
- Fallback when API unreachable
- Deterministic deny or allow (configurable)
- Expose: `fallback_decision(uid, pin) -> AccessResult`

---

## 5. Logging Layer

### 5.1 logging.event_logger
- Append‑only JSONL logging
- No PIN storage
- Includes:
  - timestamp
  - badge UID
  - zone
  - device/team
  - result
  - denial reason
  - network status
- Expose: `log_event(event_dict)`

### 5.2 logging.log_rotation
- Optional: rotate logs by size or date
- Expose: `rotate_if_needed()`

---

## 6. Configuration Layer

### 6.1 config.settings.json
Contains:
- device_id  
- team_id  
- zone_code  
- API URL  
- API credentials  
- break‑glass settings  
- logging path  

### 6.2 config.config_loader
- Loads and validates settings
- Expose: `get(key)`

---

## 7. Main Application Loop

### main.py responsibilities:
1. Initialize all modules  
2. Enter deterministic loop:
   - Read badge UID  
   - Read PIN  
   - Check network status  
   - If online → call API  
   - If offline → break‑glass  
   - Trigger indicators  
   - Log event  
   - Return to idle  

### Pseudocode

