"""
Notification Manager
Handles notification creation, storage, and delivery
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import os
from .types import Notification, NotificationType, NotificationPriority

class NotificationManager:
    """Manages notifications for the application"""
    
    def __init__(self, storage_path: str = "data/notifications.json"):
        self.storage_path = storage_path
        self.notifications: List[Notification] = []
        self.load_notifications()
    
    def load_notifications(self):
        """Load notifications from storage"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.notifications = [
                        Notification(
                            title=n['title'],
                            message=n['message'],
                            notification_type=NotificationType(n['type']),
                            priority=NotificationPriority(n['priority']),
                            data=n.get('data', {}),
                            expires_at=datetime.fromisoformat(n['expires_at']) if n.get('expires_at') else None
                        ) for n in data
                    ]
            except Exception as e:
                print(f"Error loading notifications: {e}")
                self.notifications = []
    
    def save_notifications(self):
        """Save notifications to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump([n.to_dict() for n in self.notifications], f, indent=2)
        except Exception as e:
            print(f"Error saving notifications: {e}")
    
    def create_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
        expires_in_hours: Optional[int] = None
    ) -> Notification:
        """Create a new notification"""
        expires_at = None
        if expires_in_hours:
            expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        notification = Notification(
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            data=data,
            expires_at=expires_at
        )
        
        self.notifications.append(notification)
        self.save_notifications()
        return notification
    
    def get_notifications(
        self,
        notification_type: Optional[NotificationType] = None,
        priority: Optional[NotificationPriority] = None,
        unread_only: bool = False,
        limit: Optional[int] = None
    ) -> List[Notification]:
        """Get notifications with optional filtering"""
        filtered = self.notifications.copy()
        
        # Remove expired notifications
        filtered = [n for n in filtered if not n.is_expired()]
        
        # Apply filters
        if notification_type:
            filtered = [n for n in filtered if n.type == notification_type]
        
        if priority:
            filtered = [n for n in filtered if n.priority == priority]
        
        if unread_only:
            filtered = [n for n in filtered if not n.read]
        
        # Sort by priority and creation time
        priority_order = {
            NotificationPriority.CRITICAL: 4,
            NotificationPriority.HIGH: 3,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.LOW: 1
        }
        
        filtered.sort(key=lambda n: (priority_order[n.priority], n.created_at), reverse=True)
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read"""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                self.save_notifications()
                return True
        return False
    
    def mark_all_as_read(self) -> int:
        """Mark all notifications as read"""
        count = 0
        for notification in self.notifications:
            if not notification.read:
                notification.read = True
                count += 1
        self.save_notifications()
        return count
    
    def delete_notification(self, notification_id: str) -> bool:
        """Delete a notification"""
        for i, notification in enumerate(self.notifications):
            if notification.id == notification_id:
                del self.notifications[i]
                self.save_notifications()
                return True
        return False
    
    def clear_expired(self) -> int:
        """Clear expired notifications"""
        initial_count = len(self.notifications)
        self.notifications = [n for n in self.notifications if not n.is_expired()]
        removed_count = initial_count - len(self.notifications)
        if removed_count > 0:
            self.save_notifications()
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        total = len(self.notifications)
        unread = len([n for n in self.notifications if not n.read])
        expired = len([n for n in self.notifications if n.is_expired()])
        
        by_type = {}
        for notification_type in NotificationType:
            by_type[notification_type.value] = len([
                n for n in self.notifications 
                if n.type == notification_type and not n.is_expired()
            ])
        
        by_priority = {}
        for priority in NotificationPriority:
            by_priority[priority.value] = len([
                n for n in self.notifications 
                if n.priority == priority and not n.is_expired()
            ])
        
        return {
            "total": total,
            "unread": unread,
            "expired": expired,
            "by_type": by_type,
            "by_priority": by_priority
        }

# Global notification manager instance
notification_manager = NotificationManager()

def get_notification_manager() -> NotificationManager:
    """Get the global notification manager"""
    return notification_manager

def create_notification(
    title: str,
    message: str,
    notification_type: NotificationType,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    data: Optional[Dict[str, Any]] = None,
    expires_in_hours: Optional[int] = None
) -> Notification:
    """Create a notification using the global manager"""
    return notification_manager.create_notification(
        title, message, notification_type, priority, data, expires_in_hours
    )
