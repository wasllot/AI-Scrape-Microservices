"""
Privacy Compliance and Audit Logging Module

Provides:
- GDPR compliance utilities (right to deletion, data portability)
- Audit logging for data access and modifications
- Consent management
- Data retention enforcement
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Audit action types"""
    DATA_ACCESS = "data_access"
    DATA_CREATE = "data_create"
    DATA_UPDATE = "data_update"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    LOGIN = "login"
    LOGOUT = "logout"
    CONSENT_GIVEN = "consent_given"
    CONSENT_WITHDRAWN = "consent_withdrawn"


class DataSubjectType(Enum):
    """Types of data subjects"""
    USER = "user"
    CUSTOMER = "customer"
    CANDIDATE = "candidate"
    EMPLOYEE = "employee"


@dataclass
class AuditLogEntry:
    """Audit log entry structure"""
    id: str
    timestamp: datetime
    action: str
    subject_type: str
    subject_id: str
    actor_id: Optional[str]
    actor_ip: Optional[str]
    details: Dict[str, Any]
    resource_type: Optional[str]
    resource_id: Optional[str]


@dataclass
class ConsentRecord:
    """Consent record for GDPR compliance"""
    subject_id: str
    consent_type: str
    granted: bool
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]


class AuditLogger:
    """
    Audit logger for tracking data operations.
    
    Stores audit logs for compliance and security monitoring.
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
    
    def log(
        self,
        action: AuditAction,
        subject_type: DataSubjectType,
        subject_id: str,
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        details: Optional[Dict] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> str:
        """
        Create an audit log entry.
        
        Args:
            action: Type of action performed
            subject_type: Type of data subject
            subject_id: ID of the data subject
            actor_id: ID of user performing action
            actor_ip: IP address of actor
            details: Additional details
            resource_type: Type of resource affected
            resource_id: ID of resource
            
        Returns:
            Audit log entry ID
        """
        entry = AuditLogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            action=action.value,
            subject_type=subject_type.value,
            subject_id=str(subject_id),
            actor_id=actor_id,
            actor_ip=actor_ip,
            details=details or {},
            resource_type=resource_type,
            resource_id=resource_id
        )
        
        if self.db:
            self._save_to_database(entry)
        
        logger.info(
            f"AUDIT: {action.value} on {subject_type.value}:{subject_id}",
            extra={"audit": asdict(entry)}
        )
        
        return entry.id
    
    def _save_to_database(self, entry: AuditLogEntry):
        """Save audit entry to database"""
        try:
            self.db.execute(
                """
                INSERT INTO audit_logs 
                (id, timestamp, action, subject_type, subject_id, actor_id, actor_ip, details, resource_type, resource_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.id,
                    entry.timestamp,
                    entry.action,
                    entry.subject_type,
                    entry.subject_id,
                    entry.actor_id,
                    entry.actor_ip,
                    json.dumps(entry.details),
                    entry.resource_type,
                    entry.resource_id
                ),
                fetch_results=False
            )
        except Exception as e:
            logger.error(f"Failed to save audit log: {e}")
    
    def get_logs_for_subject(
        self,
        subject_type: DataSubjectType,
        subject_id: str,
        limit: int = 100
    ) -> List[AuditLogEntry]:
        """Get audit logs for a specific data subject"""
        if not self.db:
            return []
        
        try:
            results = self.db.execute(
                """
                SELECT id, timestamp, action, subject_type, subject_id, 
                       actor_id, actor_ip, details, resource_type, resource_id
                FROM audit_logs
                WHERE subject_type = %s AND subject_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (subject_type.value, str(subject_id), limit)
            )
            
            return [
                AuditLogEntry(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    action=r["action"],
                    subject_type=r["subject_type"],
                    subject_id=r["subject_id"],
                    actor_id=r.get("actor_id"),
                    actor_ip=r.get("actor_ip"),
                    details=r.get("details", {}),
                    resource_type=r.get("resource_type"),
                    resource_id=r.get("resource_id")
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Failed to fetch audit logs: {e}")
            return []


class PrivacyManager:
    """
    Manages privacy compliance (GDPR, etc.)
    
    Handles:
    - Data deletion requests
    - Data export requests
    - Consent management
    - Retention policy enforcement
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        self.audit = AuditLogger(db_connection)
    
    def delete_user_data(
        self,
        subject_type: DataSubjectType,
        subject_id: str,
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        delete_related: bool = True
    ) -> Dict[str, Any]:
        """
        Delete all personal data for a subject (GDPR Right to Erasure).
        
        Args:
            subject_type: Type of data subject
            subject_id: ID of subject
            actor_id: ID of user requesting deletion
            actor_ip: IP address of requester
            delete_related: Whether to delete related records
            
        Returns:
            Deletion result with details
        """
        result = {
            "success": True,
            "deleted_tables": [],
            "errors": []
        }
        
        tables_to_check = {
            DataSubjectType.CANDIDATE: ["embeddings", "messages", "conversations"],
            DataSubjectType.USER: ["users", "sessions"],
        }
        
        tables = tables_to_check.get(subject_type, [])
        
        for table in tables:
            try:
                if self.db:
                    self.db.execute(
                        f"DELETE FROM {table} WHERE id = %s",
                        (str(subject_id),),
                        fetch_results=False
                    )
                    self.db.commit()
                result["deleted_tables"].append(table)
                
            except Exception as e:
                result["errors"].append(f"{table}: {str(e)}")
                logger.error(f"Failed to delete from {table}: {e}")
        
        if result["errors"]:
            result["success"] = False
        
        self.audit.log(
            action=AuditAction.DATA_DELETE,
            subject_type=subject_type,
            subject_id=str(subject_id),
            actor_id=actor_id,
            actor_ip=actor_ip,
            details={"deleted_tables": result["deleted_tables"], "success": result["success"]}
        )
        
        return result
    
    def export_user_data(
        self,
        subject_type: DataSubjectType,
        subject_id: str,
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export all personal data for a subject (GDPR Right to Portability).
        
        Returns data in JSON format.
        """
        export_data = {
            "export_date": datetime.utcnow().isoformat(),
            "subject_type": subject_type.value,
            "subject_id": str(subject_id),
            "data": {}
        }
        
        if self.db:
            table_map = {
                DataSubjectType.CANDIDATE: "embeddings",
                DataSubjectType.USER: "users",
            }
            
            table = table_map.get(subject_type)
            if table:
                try:
                    results = self.db.execute(
                        f"SELECT * FROM {table} WHERE id = %s",
                        (str(subject_id),)
                    )
                    export_data["data"][table] = results
                except Exception as e:
                    logger.error(f"Export failed: {e}")
                    export_data["error"] = str(e)
        
        self.audit.log(
            action=AuditAction.DATA_EXPORT,
            subject_type=subject_type,
            subject_id=str(subject_id),
            actor_id=actor_id,
            actor_ip=actor_ip,
            details={"exported_tables": list(export_data["data"].keys())}
        )
        
        return export_data
    
    def record_consent(
        self,
        subject_id: str,
        consent_type: str,
        granted: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        """
        Record user consent (GDPR Article 7).
        """
        record = ConsentRecord(
            subject_id=str(subject_id),
            consent_type=consent_type,
            granted=granted,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if self.db:
            try:
                self.db.execute(
                    """
                    INSERT INTO consent_records 
                    (subject_id, consent_type, granted, timestamp, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        record.subject_id,
                        record.consent_type,
                        record.granted,
                        record.timestamp,
                        record.ip_address,
                        record.user_agent
                    ),
                    fetch_results=False
                )
                self.db.commit()
            except Exception as e:
                logger.error(f"Failed to record consent: {e}")
        
        action = AuditAction.CONSENT_GIVEN if granted else AuditAction.CONSENT_WITHDRAWN
        self.audit.log(
            action=action,
            subject_type=DataSubjectType.USER,
            subject_id=str(subject_id),
            actor_id=str(subject_id),
            actor_ip=ip_address,
            details={"consent_type": consent_type, "granted": granted}
        )
        
        return record
    
    def check_consent(
        self,
        subject_id: str,
        consent_type: str
    ) -> Optional[bool]:
        """Check if subject has given consent for a specific type"""
        if not self.db:
            return None
        
        try:
            results = self.db.execute(
                """
                SELECT granted FROM consent_records
                WHERE subject_id = %s AND consent_type = %s
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (str(subject_id), consent_type)
            )
            
            if results:
                return results[0]["granted"]
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
        
        return None
    
    def get_deletion_deadline(self, request_date: datetime = None) -> datetime:
        """Calculate GDPR deletion deadline (30 days from request)"""
        request_date = request_date or datetime.utcnow()
        return request_date + timedelta(days=30)


# SQL for creating audit logs table
AUDIT_LOGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
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

CREATE INDEX IF NOT EXISTS idx_audit_subject ON audit_logs(subject_type, subject_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
"""

CONSENT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS consent_records (
    id SERIAL PRIMARY KEY,
    subject_id VARCHAR(255) NOT NULL,
    consent_type VARCHAR(100) NOT NULL,
    granted BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_consent_subject ON consent_records(subject_id, consent_type);
"""
