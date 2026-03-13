---
title: "RFID Access Reader – Architecture Package"
format:
  html: default
  pdf: default
  revealjs: default
---

# 1. Overview

## 1.1 Mission Statement
Design and implement a Raspberry Pi–based access reader that:
- Reads employee RFID badges
- Collects a 4‑digit PIN (2nd factor)
- Calls the Sentinel Employee Database REST API to validate access
- Determines access rights for any protected zone
- Logs all access attempts for the duration of the project
- Provides user feedback on success/failure
- Operates at any door (no pre‑assigned location)

## 1.2 High‑Level Capabilities
- RFID badge read (UID)
- PIN entry via keypad or touchscreen
- REST API call to validate access
- Deterministic allow/deny decision
- Structured logging
- Offline “break‑glass” mode when internet is unavailable
- Optional peripheral support (LEDs, buzzers, relays)

---

# 2. Requirements

## 2.1 Functional Requirements
- Read RFID badge UID from supported card type.
- Prompt user for 4‑digit PIN after badge read.
- Submit `{badge_uid, pin, zone_code, device_id, team_id}` to Sentinel API.
- Parse API success/denied response.
- Display success/failure to user.
- Log every access attempt (success or failure).
- Support break‑glass mode when API is unreachable.
- Support any installation location (zone is configurable).
- Maintain logs for entire project duration.
- No role/entitlement changes expected during project.
- No lockout mechanism required.
- No alerting required for failed attempts.

## 2.2 Non‑Functional Requirements
- **Security**
  - PIN must not be logged in plaintext.
  - API credentials stored securely.
  - Device must not be susceptible to trivial DoS (rate limiting, debounce).
- **Reliability**
  - Must recover cleanly from power loss.
  - Must handle intermittent network connectivity.
- **Performance**
  - Badge → decision within < 1 second.
- **Maintainability**
  - Configurable zone code.
  - Configurable device/team identifiers.
  - Modular hardware abstraction layer.
- **Portability**
  - Must operate at any door without code changes.

---

# 3. Constraints & Assumptions

- PIN is pre‑registered in the Sentinel DB.
- Access entitlements are static for the duration of the project.
- No schema changes allowed.
- No user‑initiated configuration changes.
- Root credentials provided with kit.
- Peripheral devices optional and not yet inventoried.
- Internet connectivity may be intermittent.
- API definitions provided (see Section 7).

---

# 4. System Architecture

## 4.1 Logical Architecture Diagram (ASCII)


---

# 5. Data Models

## 5.1 Access Request Payload

```json
{
  "p_badge_uid": "string",
  "p_pin_code": "string(4)",
  "p_zone_code": "string",
  "p_source_device": "string",
  "p_source_team": "string"
}

response:
{
  "employee_id": 1,
  "full_name": "Alice Nguyen",
  "zone_code": "ITROOM",
  "access_granted": true,
  "denial_reason": null
}
denied:
{
  "employee_id": 1,
  "full_name": "Alice Nguyen",
  "zone_code": "ITROOM",
  "access_granted": false,
  "denial_reason": "INVALID_PIN"
}
## 5.4 Denial Reasons

The Sentinel Access API may return one of the following denial reasons when `access_granted` is `false`. These values are authoritative and must be handled explicitly by the Access Decision Engine.

| Denial Reason        | Meaning                                                                 |
|----------------------|-------------------------------------------------------------------------|
| `UNKNOWN_BADGE`      | The badge UID is not registered in the employee database.               |
| `EMPLOYEE_INACTIVE`  | The employee record exists but is marked inactive.                      |
| `BADGE_INACTIVE`     | The badge is assigned but has been disabled or revoked.                 |
| `UNKNOWN_ZONE`       | The requested `p_zone_code` does not exist in the entitlement model.    |
| `ZONE_ACCESS_DENIED` | The employee does not have access rights to the requested zone.         |
| `INVALID_PIN`        | The supplied 4‑digit PIN does not match the employee’s registered PIN.  |

### Handling Requirements
- All denial reasons must be logged.
- PIN values must **never** be logged.
- User‑facing messaging must not expose internal system details (e.g., “badge inactive” is acceptable; “database lookup failed” is not).
- Denial reasons must be mapped to deterministic UI feedback (LED, buzzer, display).
