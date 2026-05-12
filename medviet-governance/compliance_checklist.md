# ND13/2023 Compliance Checklist - MedViet AI Platform

## A. Data Localization
- [x] Store raw patient datasets only in VN-hosted storage buckets and VN database clusters.
- [x] Keep backups in VN regions with encryption enabled and quarterly restore tests.
- [x] Log every outbound transfer request with requester, purpose, destination country, approval ID, and data classification.

## B. Explicit Consent
- [x] Capture explicit patient consent before using records for AI training.
- [x] Support consent withdrawal by excluding revoked patient IDs from future training exports.
- [x] Store consent records with timestamp, purpose, versioned consent text, collection channel, and operator ID.

## C. Breach Notification (72h)
- [x] Maintain an incident response runbook with severity levels, owner rotation, and regulator notification steps.
- [x] Alert automatically on suspicious access patterns, failed authorization spikes, and unexpected restricted-data export attempts.
- [x] Require incident commander review within 24h and regulator/customer notification workflow within 72h when reportable.

## D. DPO Appointment
- [x] Appoint Data Protection Officer for privacy governance reviews.
- [x] DPO contact: dpo@medviet.example

## E. Technical Controls
| ND13 Requirement | Technical Control | Status | Owner |
|-----------------|-------------------|--------|-------|
| Data minimization | PII anonymization pipeline with Presidio recognizers and dataframe anonymization | Done | AI Team |
| Access control | Casbin RBAC on FastAPI endpoints plus OPA policy for data access decisions | Done | Platform Team |
| Encryption | AES-256-GCM envelope encryption for sensitive values; TLS 1.3 required in transit | Done | Infra Team |
| Audit logging | API gateway and application audit logs for token subject, endpoint, action, result, and request ID | Planned | Platform Team |
| Breach detection | Prometheus/Grafana alerts for unusual access, repeated 403/401 responses, and restricted export attempts | Planned | Security Team |
| Data localization | OPA deny rule blocks restricted data export outside VN; transfer logs retained for audit | Done | Security Team |
| Consent tracking | Consent registry keyed by patient_id with purpose, timestamp, and withdrawal status | Planned | Product Team |
| Incident response | 72h notification runbook, on-call escalation, evidence preservation checklist | Planned | Security Team |

## F. Planned Technical Solutions
- Audit logging: add FastAPI middleware that writes structured JSON logs for every protected endpoint. Logs will include timestamp, user, role, resource, action, status code, source IP, and correlation ID, then ship to a write-once log store with 180-day retention.
- Breach detection: configure Prometheus alerts for abnormal read volume, repeated authorization failures, access outside business hours, and OPA restricted-export denies. Grafana dashboards will show per-role access trends and incident drill metrics.
- Consent tracking: add a consent table with `patient_id`, `purpose`, `status`, `consent_version`, `created_at`, and `withdrawn_at`. Training data exports will join against this table and exclude withdrawn or missing consent.
- Incident response: maintain a playbook covering triage, containment, data subject impact analysis, regulator notification, customer communication, and post-incident corrective actions.
- Data localization: enforce VN-only storage locations in infrastructure policy, add OPA checks for export workflows, and require explicit DPO approval for any cross-border transfer exception.
