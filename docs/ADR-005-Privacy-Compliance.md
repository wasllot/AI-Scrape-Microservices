# ADR-005: Privacy Compliance (GDPR)

## Status
Implemented

## Context
We needed to implement privacy compliance features for GDPR and similar regulations:
- Right to Erasure (Article 17)
- Right to Data Portability (Article 20)
- Consent Management (Article 7)
- Audit Logging for data access

## Decision

### 1. Audit Logging
Created `app/privacy.py` with `AuditLogger`:

- Tracks all data access and modifications
- Records: action, subject, actor, IP, timestamp, details
- Database table with indexed queries

### 2. Privacy Manager
Created `PrivacyManager` with:

- **delete_user_data()**: Right to Erasure implementation
- **export_user_data()**: Right to Data Portability (JSON export)
- **record_consent()**: Consent tracking (Article 7)
- **check_consent()**: Verify consent status

### 3. Database Tables
Migration `003_audit_logs_consent.sql`:

- `audit_logs`: All data operations
- `consent_records`: Consent history
- `deletion_requests`: Deletion request tracking

### 4. Configuration
Added settings:
- `AUDIT_LOGGING_ENABLED`: Enable/disable audit logs
- `PRIVACY_CONSENT_REQUIRED`: Require consent before processing
- `DATA_DELETION_DAYS`: Deadline for deletion requests (default 30)

## Consequences

### Positive
- GDPR compliance for data subjects
- Complete audit trail for data operations
- Automated consent management
- 30-day deletion deadline tracking

### Negative
- Additional database storage
- Performance overhead for logging
- Must run migration for new tables

## API Endpoints

| Endpoint | Method | Purpose |
|---------|--------|---------|
| `/privacy/consent` | POST | Record consent |
| `/privacy/consent/{subject_id}` | GET | Check consent status |
| `/privacy/export/{subject_id}` | GET | Export user data |
| `/privacy/delete/{subject_id}` | DELETE | Request data deletion |

## Configuration
```bash
AUDIT_LOGGING_ENABLED=true
PRIVACY_CONSENT_REQUIRED=false
DATA_DELETION_DAYS=30
```

## References
- [GDPR Article 17 - Right to Erasure](https://gdpr-info.eu/art-17-gdpr/)
- [GDPR Article 20 - Data Portability](https://gdpr-info.eu/art-20-gdpr/)
- [GDPR Article 7 - Consent](https://gdpr-info.eu/art-7-gdpr/)
