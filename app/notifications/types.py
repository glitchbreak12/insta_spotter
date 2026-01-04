"""
Notification types and enums
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

class NotificationType(Enum):
    """Types of notifications"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SYSTEM = "system"
    MODERATION = "moderation"
    POSTING = "posting"
    ANALYTICS = "analytics"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Notification:
    """Notification data structure"""
    
    def __init__(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ):
        self.id = f"notif_{datetime.now().timestamp()}"
        self.title = title
        self.message = message
        self.type = notification_type
        self.priority = priority
        self.data = data or {}
        self.created_at = datetime.now()
        self.expires_at = expires_at
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type.value,
            "priority": self.priority.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "read": self.read
        }
    
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
