# AUDIT Log — Regulatory Compliance Checklist
## Circular SFC 029/2014 — Superfinanciera Colombia

---

## Mandatory Requirements

- [x] Log records the exact modified field name (`modified_field`)
- [x] Log records `previous_value` and `new_value` — anonymized when sensitive
- [x] Log records `timestamp` in UTC timezone
- [x] Log records the IP address of the requester — anonymized (Law 1581/2012)
- [x] AUDIT retention is minimum 5 years — `expires_at = timestamp + 5 years`
- [x] AUDIT documents are never manually modified or deleted
- [x] Sensitive data in `previous_value` and `new_value` is anonymized
- [x] Index exists on `timestamp` for date range queries
- [x] `correlation_id` allows full operation reconstruction

---

## Auditable Fields Covered

| modified_field       | Sensitive | Anonymization example         |
|----------------------|-----------|-------------------------------|
| daily_limit          | No        | "500000" → "1000000"          |
| email                | Yes       | "ju***@gmail.com"             |
| display_name         | Yes       | "Ju** Sa***"                  |
| beneficiary_added    | Yes       | null → "nequi_****7741"       |
| beneficiary_removed  | Yes       | "nequi_****7741" → null       |
| colchon_protection   | No        | "false" → "true"              |

---

## Critical Rules

1. An AUDIT document is NEVER updated or deleted manually
2. To correct an error — insert a NEW AUDIT document documenting the correction
3. IP address is always anonymized — last octet replaced with 0
4. Retention of 5 years is NON-NEGOTIABLE — Circular SFC 029/2014
5. Each field change generates its own independent AUDIT document

---

## Retention Policy

| type        | Retention | Legal basis                        |
|-------------|-----------|------------------------------------|
| ACCESS      | 30 days   | Operational — low long-term value  |
| ERROR       | 90 days   | Debugging and technical support    |
| SECURITY    | 90 days   | Fraud investigation                |
| AUTH        | 1 year    | Session and token traceability     |
| TRANSACTION | 3 years   | Financial traceability             |
| AUDIT       | 5 years   | MANDATORY — Circular SFC 029/2014  |