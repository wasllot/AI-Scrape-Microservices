-- Audit Logs and Consent Management Tables
-- For GDPR compliance and privacy tracking

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50) NOT NULL,
    subject_type VARCHAR(50) NOT NULL,
    subject_id VARCHAR(255) NOT NULL,
    actor_id VARCHAR(255),
    actor_ip INET,
    details JSONB DEFAULT '{}'::jsonb,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit logs
CREATE INDEX IF NOT EXISTS idx_audit_subject ON audit_logs(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id);

-- Consent Records Table
CREATE TABLE IF NOT EXISTS consent_records (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(255) NOT NULL,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for consent records
CREATE INDEX IF NOT EXISTS idx_consent_subject ON consent_records(subject_id, consent_type);
CREATE INDEX IF NOT EXISTS idx_consent_timestamp ON consent_records(timestamp DESC);

-- Data Deletion Requests Table (GDPR Right to Erasure)
CREATE TABLE IF NOT EXISTS deletion_requests (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(255) NOT NULL,
    subject_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    requested_by VARCHAR(255),
    reason TEXT,
    completed_by VARCHAR(255),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_deletion_subject ON deletion_requests(subject_id, subject_type);
CREATE INDEX IF NOT EXISTS idx_deletion_status ON deletion_requests(status);
