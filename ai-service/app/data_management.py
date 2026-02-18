"""
Data Management Module

Provides:
- Data validation utilities
- Retention policy management
- Backup/restore utilities
- Data sanitization for PII
"""
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class RetentionPeriod(Enum):
    """Data retention periods"""
    TEMPORARY = 7      # 7 days
    SHORT = 30         # 30 days
    MEDIUM = 90        # 90 days
    LONG = 365         # 1 year
    PERMANENT = -1     # Never delete


@dataclass
class DataRetentionPolicy:
    """Data retention policy configuration"""
    table_name: str
    retention_period: RetentionPeriod
    cleanup_column: str  # Column to check for cleanup
    soft_delete: bool = True


class DataValidator:
    """
    Data validation utilities for ingested content.
    """
    
    MAX_CONTENT_LENGTH = 50000
    MIN_CONTENT_LENGTH = 10
    
    # Patterns for potentially sensitive data
    EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    PHONE_PATTERN = re.compile(r'\+?[\d\s\-\(\)]{10,}')
    SSN_PATTERN = re.compile(r'\d{3}-\d{2}-\d{4}')
    CREDIT_CARD_PATTERN = re.compile(r'\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}')
    
    @classmethod
    def validate_content(cls, content: str) -> Dict[str, Any]:
        """
        Validate content for ingestion.
        
        Returns:
            Dict with validation result and any warnings
        """
        result = {"valid": True, "warnings": []}
        
        if not content or len(content.strip()) < cls.MIN_CONTENT_LENGTH:
            result["valid"] = False
            result["error"] = f"Content too short (min {cls.MIN_CONTENT_LENGTH} chars)"
            return result
        
        if len(content) > cls.MAX_CONTENT_LENGTH:
            result["warnings"].append(f"Content truncated from {len(content)} to {cls.MAX_CONTENT_LENGTH} chars")
            content = content[:cls.MAX_CONTENT_LENGTH]
        
        # Check for potential PII
        pii_found = cls.scan_for_pii(content)
        if pii_found:
            result["warnings"].append(f"Potential PII detected: {', '.join(pii_found)}")
            result["contains_pii"] = True
            result["pii_types"] = pii_found
        
        return result
    
    @classmethod
    def scan_for_pii(cls, content: str) -> List[str]:
        """Scan content for potential PII"""
        pii_types = []
        
        if cls.EMAIL_PATTERN.search(content):
            pii_types.append("email")
        if cls.PHONE_PATTERN.search(content):
            pii_types.append("phone")
        if cls.SSN_PATTERN.search(content):
            pii_types.append("ssn")
        if cls.CREDIT_CARD_PATTERN.search(content):
            pii_types.append("credit_card")
        
        return pii_types
    
    @classmethod
    def sanitize_pii(cls, content: str, mask: bool = True) -> str:
        """
        Sanitize PII from content.
        
        Args:
            content: Content to sanitize
            mask: If True, replace with [REDACTED], otherwise remove
            
        Returns:
            Sanitized content
        """
        if not mask:
            return content
        
        sanitized = cls.EMAIL_PATTERN.sub('[EMAIL REDACTED]', content)
        sanitized = cls.PHONE_PATTERN.sub('[PHONE REDACTED]', sanitized)
        sanitized = cls.SSN_PATTERN.sub('[SSN REDACTED]', sanitized)
        sanitized = cls.CREDIT_CARD_PATTERN.sub('[CARD REDACTED]', sanitized)
        
        return sanitized
    
    @classmethod
    def validate_metadata(cls, metadata: Dict) -> Dict[str, Any]:
        """
        Validate metadata structure.
        
        Returns:
            Dict with validation result
        """
        result = {"valid": True, "warnings": []}
        
        if not isinstance(metadata, dict):
            result["valid"] = False
            result["error"] = "Metadata must be a dictionary"
            return result
        
        # Check for sensitive keys
        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'credential']
        for key in metadata.keys():
            if any(s in key.lower() for s in sensitive_keys):
                result["warnings"].append(f"Sensitive key '{key}' found in metadata")
        
        # Validate metadata size
        metadata_size = len(json.dumps(metadata))
        if metadata_size > 10000:
            result["warnings"].append(f"Metadata size ({metadata_size} bytes) may be too large")
        
        return result


class DataRetentionManager:
    """
    Manages data retention policies.
    """
    
    DEFAULT_POLICIES = [
        DataRetentionPolicy(
            table_name="messages",
            retention_period=RetentionPeriod.MEDIUM,
            cleanup_column="created_at",
            soft_delete=True
        ),
        DataRetentionPolicy(
            table_name="conversations",
            retention_period=RetentionPeriod.LONG,
            cleanup_column="created_at",
            soft_delete=True
        ),
        DataRetentionPolicy(
            table_name="embeddings",
            retention_period=RetentionPeriod.LONG,
            cleanup_column="created_at",
            soft_delete=False
        ),
    ]
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.policies = self.DEFAULT_POLICIES.copy()
    
    def add_policy(self, policy: DataRetentionPolicy):
        """Add a retention policy"""
        self.policies.append(policy)
    
    def get_retention_sql(self, policy: DataRetentionPolicy) -> str:
        """Generate SQL for retention cleanup"""
        if policy.retention_period == RetentionPeriod.PERMANENT:
            return None
        
        days = policy.retention_period.value
        sql = f"""
            DELETE FROM {policy.table_name}
            WHERE {policy.cleanup_column} < NOW() - INTERVAL '{days} days'
        """
        
        if policy.soft_delete:
            sql = f"""
                UPDATE {policy.table_name}
                SET deleted_at = NOW()
                WHERE {policy.cleanup_column} < NOW() - INTERVAL '{days} days'
                AND deleted_at IS NULL
            """
        
        return sql
    
    def get_cleanup_candidates(self, policy: DataRetentionPolicy) -> List[Dict]:
        """Get records that would be cleaned up"""
        if not self.db or policy.retention_period == RetentionPeriod.PERMANENT:
            return []
        
        days = policy.retention_period.value
        try:
            results = self.db.execute(
                f"""
                SELECT COUNT(*) as count, MIN({policy.cleanup_column}) as oldest,
                       MAX({policy.cleanup_column}) as newest
                FROM {policy.table_name}
                WHERE {policy.cleanup_column} < NOW() - INTERVAL '{days} days'
                """
            )
            return results
        except Exception as e:
            logger.error(f"Error getting cleanup candidates: {e}")
            return []


class DataHasher:
    """
    Generate hashes for data integrity verification.
    """
    
    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA-256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def generate_checksum(records: List[Dict]) -> str:
        """Generate checksum for a set of records"""
        combined = json.dumps(records, sort_keys=True)
        return hashlib.sha256(combined.encode()).hexdigest()


class DataExporter:
    """
    Export data for backup purposes.
    """
    
    @staticmethod
    def export_to_json(data: List[Dict], include_metadata: bool = True) -> str:
        """Export records to JSON format"""
        export = {
            "exported_at": datetime.utcnow().isoformat(),
            "record_count": len(data),
            "records": data
        }
        return json.dumps(export, indent=2, default=str)
    
    @staticmethod
    def export_to_csv(records: List[Dict], columns: List[str]) -> str:
        """Export records to CSV format"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
        
        return output.getvalue()
