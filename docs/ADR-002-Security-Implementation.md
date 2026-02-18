# ADR-002: Security Implementation

## Status
Implemented

## Context
The system needed to address security vulnerabilities including:
- CORS allowing all origins (`allow_origins=["*"]`)
- No input sanitization for user inputs
- Potential XSS and injection vulnerabilities

## Decision

### 1. CORS Configuration
- Replace wildcard CORS with configurable allowed origins
- Use environment variable `ALLOWED_ORIGINS` with comma-separated list
- Default to `http://localhost:3000` for development

```python
# Before
allow_origins=["*"]

# After
allow_origins=settings.allowed_origins_list
```

### 2. Input Sanitization
Created `app/security.py` with three sanitization functions:

- **`sanitize_input()`**: HTML escape + length limits
- **`sanitize_css_selector()`**: Block dangerous patterns (javascript:, on*=)
- **`sanitize_url()`**: Validate URL scheme, block javascript:/data:/file:

### 3. Data Validation
Created `app/data_management.py` with:

- **`DataValidator`**: Content and metadata validation
- **PII Detection**: Email, phone, SSN, credit card patterns
- **PII Sanitization**: Automatic masking of sensitive data

## Consequences

### Positive
- Prevents XSS attacks via HTML escaping
- Blocks injection attacks in CSS selectors
- Protects against malicious URLs
- GDPR compliance via PII handling
- Production-safe CORS configuration

### Negative
- Additional processing overhead for sanitization
- Must configure allowed origins per environment

## Implementation

### Environment Variables
```
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
DATA_VALIDATION_ENABLED=true
PII_SANITIZATION_ENABLED=true
```

### API Endpoints Modified
- `/ingest`: Content validation + PII sanitization
- `/chat`: Input sanitization
- `/extract`: URL + CSS selector validation
- `/scrape/job-posting`: URL validation

## References
- [OWASP Input Validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [CORS Security](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
