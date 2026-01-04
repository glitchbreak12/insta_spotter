"""
Notification System for InstaSpotter
Handles various types of notifications and alerts
"""

from .manager import NotificationManager
from .types import NotificationType, NotificationPriority

__all__ = ["NotificationManager", "NotificationType", "NotificationPriority"]
