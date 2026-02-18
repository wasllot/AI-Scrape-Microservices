"""
Unit Tests for Data Management Module

Tests data validation, PII detection, sanitization, and retention policies.
"""
import pytest
from app.data_management import (
    DataValidator,
    DataHasher,
    DataRetentionManager,
    DataRetentionPolicy,
    RetentionPeriod
)


class TestDataValidator:
    """Tests for DataValidator class"""
    
    def test_validate_content_valid(self):
        """Valid content should pass validation"""
        result = DataValidator.validate_content("Juan Pérez - Desarrollador Full Stack")
        assert result["valid"] is True
        assert "error" not in result
    
    def test_validate_content_too_short(self):
        """Content too short should fail"""
        result = DataValidator.validate_content("abc")
        assert result["valid"] is False
        assert "too short" in result["error"].lower()
    
    def test_validate_content_truncates_long(self):
        """Very long content should be truncated with warning"""
        long_content = "a" * 60000
        result = DataValidator.validate_content(long_content)
        assert "truncated" in result["warnings"][0].lower()
        assert len(result["warnings"]) > 0
    
    def test_scan_for_pii_email(self):
        """Should detect email addresses"""
        content = "Contact me at john@example.com please"
        pii = DataValidator.scan_for_pii(content)
        assert "email" in pii
    
    def test_scan_for_pii_phone(self):
        """Should detect phone numbers"""
        content = "Call me at +1-555-123-4567"
        pii = DataValidator.scan_for_pii(content)
        assert "phone" in pii
    
    def test_scan_for_pii_ssn(self):
        """Should detect SSN"""
        content = "My SSN is 123-45-6789"
        pii = DataValidator.scan_for_pii(content)
        assert "ssn" in pii
    
    def test_scan_for_pii_credit_card(self):
        """Should detect credit card numbers"""
        content = "Card: 4111-1111-1111-1111"
        pii = DataValidator.scan_for_pii(content)
        assert "credit_card" in pii
    
    def test_scan_for_pii_none(self):
        """No PII should return empty list"""
        content = "This is normal content without sensitive data"
        pii = DataValidator.scan_for_pii(content)
        assert pii == []
    
    def test_sanitize_pii_masks_email(self):
        """sanitize_pii should mask email addresses"""
        content = "Email me at john@example.com"
        result = DataValidator.sanitize_pii(content)
        assert "[EMAIL REDACTED]" in result
        assert "john@example.com" not in result
    
    def test_sanitize_pii_masks_all(self):
        """sanitize_pii should mask all PII types"""
        content = "john@example.com, call 555-1234, SSN 123-45-6789, card 4111-1111-1111-1111"
        result = DataValidator.sanitize_pii(content)
        assert "[EMAIL REDACTED]" in result
        assert "[PHONE REDACTED]" in result
        assert "[SSN REDACTED]" in result
        assert "[CARD REDACTED]" in result
    
    def test_sanitize_pii_disabled(self):
        """sanitize_pii with mask=False should not change content"""
        content = "Email: john@example.com"
        result = DataValidator.sanitize_pii(content, mask=False)
        assert "john@example.com" in result
    
    def test_validate_metadata_valid(self):
        """Valid metadata should pass"""
        result = DataValidator.validate_metadata({"type": "cv", "source": "upload"})
        assert result["valid"] is True
    
    def test_validate_metadata_not_dict(self):
        """Non-dict metadata should fail"""
        result = DataValidator.validate_metadata("not a dict")
        assert result["valid"] is False
    
    def test_validate_metadata_sensitive_key(self):
        """Metadata with sensitive keys should warn"""
        result = DataValidator.validate_metadata({"password": "secret123"})
        assert len(result["warnings"]) > 0
        assert "password" in result["warnings"][0].lower()


class TestDataHasher:
    """Tests for DataHasher class"""
    
    def test_hash_content(self):
        """Should generate consistent SHA-256 hash"""
        content = "Hello World"
        hash1 = DataHasher.hash_content(content)
        hash2 = DataHasher.hash_content(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_hash_content_different(self):
        """Different content should have different hashes"""
        hash1 = DataHasher.hash_content("Hello")
        hash2 = DataHasher.hash_content("World")
        assert hash1 != hash2
    
    def test_generate_checksum(self):
        """Should generate checksum for records"""
        records = [{"id": 1, "name": "Test"}, {"id": 2, "name": "Test2"}]
        checksum = DataHasher.generate_checksum(records)
        assert len(checksum) == 64
    
    def test_generate_checksum_consistent(self):
        """Same records should generate same checksum"""
        records = [{"id": 1, "name": "Test"}]
        checksum1 = DataHasher.generate_checksum(records)
        checksum2 = DataHasher.generate_checksum(records)
        assert checksum1 == checksum2


class TestDataRetentionManager:
    """Tests for DataRetentionManager class"""
    
    def test_default_policies_exist(self):
        """Should have default retention policies"""
        manager = DataRetentionManager()
        assert len(manager.policies) > 0
    
    def test_add_policy(self):
        """Should be able to add custom policy"""
        manager = DataRetentionManager()
        policy = DataRetentionPolicy(
            table_name="test_table",
            retention_period=RetentionPeriod.SHORT,
            cleanup_column="created_at"
        )
        manager.add_policy(policy)
        assert len(manager.policies) == 4
    
    def test_get_retention_sql_permanent(self):
        """Permanent retention should return None"""
        policy = DataRetentionPolicy(
            table_name="test",
            retention_period=RetentionPeriod.PERMANENT,
            cleanup_column="created_at"
        )
        manager = DataRetentionManager()
        sql = manager.get_retention_sql(policy)
        assert sql is None
    
    def test_get_retention_sql_delete(self):
        """Should generate DELETE SQL for non-permanent"""
        policy = DataRetentionPolicy(
            table_name="messages",
            retention_period=RetentionPeriod.SHORT,
            cleanup_column="created_at",
            soft_delete=False
        )
        manager = DataRetentionManager()
        sql = manager.get_retention_sql(policy)
        assert "DELETE FROM messages" in sql
        assert "30 days" in sql
    
    def test_get_retention_sql_soft_delete(self):
        """Should generate UPDATE SQL for soft delete"""
        policy = DataRetentionPolicy(
            table_name="messages",
            retention_period=RetentionPeriod.MEDIUM,
            cleanup_column="created_at",
            soft_delete=True
        )
        manager = DataRetentionManager()
        sql = manager.get_retention_sql(policy)
        assert "UPDATE messages" in sql
        assert "deleted_at" in sql
        assert "90 days" in sql
